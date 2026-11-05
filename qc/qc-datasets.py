#!/usr/bin/python
import os, sys
import csv
import tempfile
from optparse import OptionParser

import csvutil


REQUIRED_FIELDS = [
    "biomarker_index",
    "component_index",
    "entity_index",
    "assessed_biomarker_entity_id",
    "assessed_entity_type",
    "condition_id",
    "evidence_source",
    "change_type_vocab",
    "aspect_type_vocab",
    "mod_type_vocab",
]

# Fields that must not hold the value "not_specified".
# A row is valid when AT LEAST ONE of the two allowed pairs is fully satisfied:
#   pair A: change_type_vocab  + aspect_type_vocab
#   pair B: aspect_type_vocab  + mod_type_vocab
NOT_SPECIFIED_FIELDS = ("change_type_vocab", "aspect_type_vocab", "mod_type_vocab")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sort_release_list(tmp_list, reversed_flag):
    factor_list = [100000000, 1000, 1]
    rel_dict = {}
    for rel in tmp_list:
        parts = rel.split(".")
        ordr = sum(factor_list[i] * int(parts[i]) for i in range(len(parts)))
        rel_dict[ordr] = rel
    return [rel_dict[k] for k in sorted(rel_dict, reverse=reversed_flag)]


def _is_not_specified(val):
    """Return True when *val* is missing, blank, or the literal 'not_specified'."""
    return val is None or str(val).strip().lower() in ("", "not_specified")


def check_not_specified(row):
    """Return a list of NOT_SPECIFIED_FIELDS that violate the pair rule.

    A row is compliant when either of these pairs is non-'not_specified':
        pair A: change_type_vocab  + aspect_type_vocab
        pair B: aspect_type_vocab  + mod_type_vocab
    """
    ct_bad  = _is_not_specified(row.get("change_type_vocab"))
    at_bad  = _is_not_specified(row.get("aspect_type_vocab"))
    mod_bad = _is_not_specified(row.get("mod_type_vocab"))

    pair_a_ok = (not ct_bad)  and (not at_bad)
    pair_b_ok = (not at_bad)  and (not mod_bad)

    if pair_a_ok or pair_b_ok:
        return []   # compliant

    # Collect the offending fields to surface in the log
    offenders = []
    if ct_bad:
        offenders.append("change_type_vocab")
    if at_bad:
        offenders.append("aspect_type_vocab")
    if mod_bad:
        offenders.append("mod_type_vocab")
    return offenders


def validate_file(in_file, file_name):
    """Read *in_file*, check required fields and 'not_specified' rules,
    and return (violations, tmp_path).

    violations  -- list of dicts, one per bad row, ready to write to the log
    tmp_path    -- path to a temp file containing only the compliant rows
                   (caller is responsible for deleting it)
    """
    file_ext = in_file.rsplit(".", 1)[-1].lower()
    sep = "\t" if file_ext == "tsv" else ","

    violations = []

    tmp_fd, tmp_path = tempfile.mkstemp(suffix="." + file_ext, prefix="qc_filtered_")
    os.close(tmp_fd)

    with open(in_file, newline="", encoding="utf-8") as fh_in, \
         open(tmp_path, "w", newline="", encoding="utf-8") as fh_out:

        reader = csv.DictReader(fh_in, delimiter=sep)
        if reader.fieldnames is None:
            return violations, tmp_path

        writer = csv.DictWriter(fh_out, fieldnames=reader.fieldnames, delimiter=sep)
        writer.writeheader()

        for line_num, row in enumerate(reader, start=2):   # 2 = first data row
            row_ok = True

            # ------------------------------------------------------------------
            # Check 1: required fields must be present and non-empty / non-"NA"
            # ------------------------------------------------------------------
            missing = []
            for field in REQUIRED_FIELDS:
                val = row.get(field)
                if val is None or str(val).strip() in ("", "NA"):
                    if field == "condition_id":
                        fallback = row.get("exposure_agent_id")
                        if fallback is not None and str(fallback).strip() not in ("", "NA"):
                            continue
                    missing.append(field)

            if missing:
                violations.append({
                    "file":            file_name,
                    "line":            line_num,
                    "violation_type":  "missing_required",
                    "offending_fields": "|".join(missing),
                })
                row_ok = False

            # ------------------------------------------------------------------
            # Check 2: change_type_vocab / aspect_type_vocab / mod_type_vocab pair rule
            # ------------------------------------------------------------------
            if row_ok:   # only run if the row passed check 1
                ns_offenders = check_not_specified(row)
                if ns_offenders:
                    violations.append({
                        "file":            file_name,
                        "line":            line_num,
                        "violation_type":  "not_specified",
                        "offending_fields": "|".join(ns_offenders),
                    })
                    row_ok = False

            if row_ok:
                writer.writerow(row)

    return violations, tmp_path


def write_validation_log(log_path, all_violations):
    """Append *all_violations* to *log_path* (creates the file if needed)."""
    fieldnames = ["file", "line", "violation_type", "offending_fields"]
    write_header = not os.path.isfile(log_path)

    with open(log_path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerows(all_violations)


# ---------------------------------------------------------------------------
# Record-count helpers
# ---------------------------------------------------------------------------

def get_record_count_detailed(in_file):
    file_ext = in_file.split(".")[-1].lower()
    res_obj = {}
    if file_ext == "tsv":
        sep = "\t" if file_ext == "tsv" else ","
        res_obj = csvutil.get_sheet_stats_detailed(in_file, sep)
    elif file_ext == "fasta":
        from Bio import SeqIO
        res_obj["rowcount"] = len(list(SeqIO.parse(in_file, "fasta")))
    return res_obj


def get_record_count(in_file):
    file_ext = in_file.split(".")[-1].lower()
    field_count, row_count, id_count = 1, 1, 1
    if file_ext == "tsv":
        sep = "\t" if file_ext == "tsv" else ","
        field_count, row_count, id_count = csvutil.get_sheet_stats(in_file, sep)
    elif file_ext == "fasta":
        from Bio import SeqIO
        id_count = len(list(SeqIO.parse(in_file, "fasta")))
    return field_count, row_count, id_count


def compare_files(cur_file, prev_file, writer, file_name):
    res_obj_cur, res_obj_prev = {}, {}
    if os.path.isfile(prev_file):
        res_obj_prev = get_record_count_detailed(prev_file)
    res_obj_cur = get_record_count_detailed(cur_file)

    f_list_prev = list(res_obj_prev["uniquecount"].keys()) if res_obj_prev else []
    f_list_cur  = list(res_obj_cur["uniquecount"].keys())

    f = "rowcount"
    v_prev = res_obj_prev.get(f, 0) if res_obj_prev else 0
    v_cur  = res_obj_cur[f]
    writer.writerow([file_name, f, str(v_prev), str(v_cur), str(int(v_cur) - int(v_prev))])

    for f in sorted(set(f_list_prev + f_list_cur)):
        v_prev = res_obj_prev["uniquecount"].get(f, "") if res_obj_prev else ""
        v_cur  = res_obj_cur["uniquecount"].get(f, "")
        d = int(v_cur) - int(v_prev) if v_prev != "" and v_cur != "" else ""
        writer.writerow([file_name, f, str(v_prev), str(v_cur), str(d)])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    usage = "\n%prog  [options]"
    parser = OptionParser(usage, version=" ")
    parser.add_option("-r", "--currel",  dest="currel",  help="Current release version (e.g. 3.1.1)")
    parser.add_option("-p", "--prevrel", dest="prevrel", help="Previous release version to compare against")
    (options, args) = parser.parse_args()

    if not options.currel or not options.prevrel:
        parser.print_help()
        sys.exit(0)

    data_release_dir = "/data/shared/biomarkerdb/releases/data/"
    subdir = "unreviewed"

    cur_dir  = os.path.join(data_release_dir, "v-" + options.currel,  subdir)
    prev_dir = os.path.join(data_release_dir, "v-" + options.prevrel, subdir)

    if not os.path.isdir(cur_dir):
        print("ERROR: current release directory not found: %s" % cur_dir)
        sys.exit(1)

    log_dir = os.path.join(data_release_dir, "v-" + options.currel, "logs")
    os.makedirs(log_dir, exist_ok=True)

    out_file        = os.path.join(log_dir, "qc-datasets.csv")
    validation_log  = os.path.join(log_dir, "qc-validation.csv")

    # Remove a stale validation log from a previous run so we start clean.
    if os.path.isfile(validation_log):
        os.remove(validation_log)

    supported_exts = (".csv", ".tsv", ".fasta")
    files = [f for f in sorted(os.listdir(cur_dir)) if f.lower().endswith(supported_exts)]

    if not files:
        print("No supported files found in %s" % cur_dir)
        sys.exit(0)

    all_violations = []
    tmp_files      = []     # track temp paths so we can delete them at the end

    try:
        with open(out_file, "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["file", "field",
                             "unique_values_in_prev_rel",
                             "unique_values_in_cur_rel", "diff"])

            for file_name in files:
                cur_file  = os.path.join(cur_dir,  file_name)
                prev_file = os.path.join(prev_dir, file_name)

                # ----------------------------------------------------------
                # Step 1: validate current-release file; collect violations
                # Only TSV files whose name starts with "biomarkers_" are
                # subject to required-field / not_specified validation;
                # all other files are passed unchanged.
                # ----------------------------------------------------------
                is_biomarker_tsv = (
                    file_name.lower().endswith(".tsv")
                    and file_name.startswith("biomarkers_")
                )
                if REQUIRED_FIELDS and is_biomarker_tsv:
                    violations, tmp_path = validate_file(cur_file, file_name)
                    tmp_files.append(tmp_path)

                    if violations:
                        all_violations.extend(violations)
                        missing_cnt = sum(1 for v in violations
                                          if v["violation_type"] == "missing_required")
                        ns_cnt      = sum(1 for v in violations
                                          if v["violation_type"] == "not_specified")
                        parts = []
                        if missing_cnt:
                            parts.append("%d missing-required" % missing_cnt)
                        if ns_cnt:
                            parts.append("%d not_specified-pair" % ns_cnt)
                        print("  [VALIDATION] %s: %s row(s) excluded"
                              % (file_name, ", ".join(parts)))

                    # Use the filtered copy for comparison
                    effective_cur = tmp_path
                else:
                    effective_cur = cur_file

                # ----------------------------------------------------------
                # Step 2: compare (filtered) current release vs previous
                # ----------------------------------------------------------
                if not os.path.isfile(prev_file):
                    print("WARNING: no matching file in previous release for %s" % file_name)

                compare_files(effective_cur, prev_file, writer, file_name)

    finally:
        for p in tmp_files:
            try:
                os.remove(p)
            except OSError:
                pass

    # Write the consolidated validation log
    if all_violations:
        write_validation_log(validation_log, all_violations)
        missing_total = sum(1 for v in all_violations if v["violation_type"] == "missing_required")
        ns_total      = sum(1 for v in all_violations if v["violation_type"] == "not_specified")
        print("\nValidation issues found:")
        if missing_total:
            print("  %d row(s) excluded for missing required fields" % missing_total)
        if ns_total:
            print("  %d row(s) excluded for not_specified pair rule "
                  "(change_type_vocab/aspect_type_vocab/mod_type_vocab)" % ns_total)
        print("Validation log written to %s" % validation_log)
    else:
        print("\nValidation passed: no missing required-field values found.")

    print("Comparison output written to %s" % out_file)


if __name__ == '__main__':
    main()
