#!/usr/bin/env python3
"""
Parse entity JSONs in entdb/ and report:
  - How many ref IDs map to a real HGNC ID
  - Which ref IDs do NOT map (hgnc_id is HGNC:0000... with 4+ zeroes only)

Output is written to LOG_DIR. NCBI IDs (prefix "NCBI:") are listed first,
followed by IDs from other namespaces.
"""

import json
import re
import glob
import sys
from datetime import datetime

ENTDB_DIR = "/data/shared/biomarkerdb/releases/data/current/jsondb/entdb"
LOG_DIR   = "/data/shared/biomarkerdb/releases/data/current/logs"

# Matches HGNC:0000... where the numeric part is ONLY zeroes (4 or more)
NOT_MAPPABLE_RE = re.compile(r'^HGNC:0{4,}$')

def is_not_mappable(hgnc_id: str) -> bool:
    return bool(NOT_MAPPABLE_RE.match(hgnc_id))

def main():
    batch_files = sorted(glob.glob(f"{ENTDB_DIR}/batch.*.json"))
    if not batch_files:
        print(f"No batch files found in {ENTDB_DIR}", file=sys.stderr)
        sys.exit(1)

    mapped   = set()  # ref_ids with a real HGNC mapping
    unmapped = set()  # ref_ids with an all-zero placeholder
    skipped  = 0      # entries missing hgnc_id or ref_id

    for path in batch_files:
        with open(path) as fh:
            try:
                records = json.load(fh)
            except json.JSONDecodeError as e:
                print(f"WARNING: could not parse {path}: {e}", file=sys.stderr)
                continue

        for rec in records:
            hgnc_id = rec.get("hgnc_id", "").strip()
            ref_id  = rec.get("ref_id",  "").strip()

            if not hgnc_id or not ref_id:
                skipped += 1
                continue

            if is_not_mappable(hgnc_id):
                unmapped.add(ref_id)
            else:
                mapped.add(ref_id)

    # Split unmapped into NCBI vs other, each sorted
    unmapped_ncbi  = sorted(r for r in unmapped if r.startswith("NCBI:"))
    unmapped_other = sorted(r for r in unmapped if not r.startswith("NCBI:"))

    total = len(mapped) + len(unmapped)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"{LOG_DIR}/hgnc_mapping_{timestamp}.log"

    lines = []
    lines.append("=" * 60)
    lines.append(f"Total ref IDs seen       : {total}")
    lines.append(f"  Mapped to HGNC         : {len(mapped)}")
    lines.append(f"  NOT mapped (zero IDs)  : {len(unmapped)}")
    if skipped:
        lines.append(f"  Skipped (missing field): {skipped}")
    lines.append("=" * 60)

    if unmapped_ncbi:
        lines.append(f"\nNCBI IDs not mapped to HGNC ({len(unmapped_ncbi)}):")
        for ref_id in unmapped_ncbi:
            lines.append(f"  {ref_id}")

    if unmapped_other:
        lines.append(f"\nOther IDs not mapped to HGNC ({len(unmapped_other)}):")
        for ref_id in unmapped_other:
            lines.append(f"  {ref_id}")

    output = "\n".join(lines) + "\n"

    with open(log_path, "w") as fh:
        fh.write(output)

    print(output)
    print(f"Log written to: {log_path}")

if __name__ == "__main__":
    main()
