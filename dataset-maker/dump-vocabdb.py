import json
import glob

def dump_new(rel, ds):

    downloads_dir = "/data/shared/biomarkerdb/downloads/"
    out_dir = "/data/shared/biomarkerdb/vocabdb/"
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)
    ds_dict = json.load(open(release_dir + "misc/datasets.json"))

    dir_map = {
        "biomarkers_cadsr":"2026_07_21",
        "biomarkers_cgi":"2026_02_05",
        "biomarkers_civic":"2026_02_05",
        "biomarkers_civic_metakb":"2026_02_05",
        "biomarkers_clinvar":"2026_02_05",
        "biomarkers_edrn":"2026_02_05",
        "biomarkers_exposure_agents":"2026_04_16",
        "biomarkers_gwas":"2026_02_05",
        "biomarkers_llm_glycan":"2026_08_20",
        "biomarkers_markerdb":"2026_01_29",
        "biomarkers_microplastics":"2026_04_09",
        "biomarkers_mw_loinc":"2026_05_07",
        "biomarkers_mw_newborn_screening":"2026_05_07",
        "biomarkers_oncomx":"2026_02_26",
        "biomarkers_opentargets":"2026_02_05",
        "biomarkers_PMC_biomarker_sets":"2026_02_05",
        "biomarkers_sennet":"2026_02_05",
        "biomarkers_top_50":"2026_02_05",
        "biomarkers_upkb_reviewed_v2":"2026_02_26",
        "biomarkers_user_submitted":"2026_02_26"
    }

        
    for file_name in ds_dict["biomarkers"][ds]:
        in_file = downloads_dir + ds.replace("biomarkers_","") + "/%s/" % (dir_map[ds]) + file_name
        tmp_dict = {}
        with open(in_file, "r") as FR:
            lcount = 0
            for line in FR:
                lcount += 1
                row = line.replace("\n", "").replace("\"", "\'").split("\t")
                if lcount == 1:
                    f_list = row
                else:
                    biomarker = row[f_list.index("biomarker")]
                    parts = biomarker.split(" ")
                    change_type, aspect_type, mod_type, construct = "", "", "", ""
                    if parts[0] in ["increased", "decreased", "altered"]:
                        change_type = parts[0]
                    if parts[0] in ["absence"] and parts[1] == "of":
                        change_type = "absence of"
                    if parts[0] in ["presence", "presense"] and parts[1] == "of":
                        change_type = "presence of"
                    if parts[1] in ["expression", "level"]:
                        aspect_type = parts[1]
                    obj = {"change_type":change_type, "aspect_type":aspect_type, "mod_type":mod_type, "construct":""}
                    tmp_dict[biomarker] = obj
        out_file = out_dir + ds + ".json"
        with open(out_file, "w") as FW:
            FW.write("%s\n" % (json.dumps(tmp_dict, indent=4)))

    return


def dump_legacy(rel):
    out_dir = "/data/shared/biomarkerdb/vocabdb/"
    file_list = glob.glob("/data/shared/biomarkerdb/releases/data/v-%s/reviewed/biomarkers_*.tsv" % (rel))
    for in_file in file_list:
        ds = in_file.split("/")[-1].replace(".tsv","")
        tmp_dict = {}
        with open(in_file, "r") as FR:
            lcount = 0
            for line in FR:
                lcount += 1
                row = line.replace("\n", "").replace("\"", "\'").split("\t")
                if lcount == 1:
                    f_list = row
                else:
                    biomarker = row[f_list.index("biomarker")]
                    c_vocab = row[f_list.index("vocab_pattern")]
                    c_vocab_construct = row[f_list.index("biomarker_controlled_vocab")]
                    obj = {"change_type":"", "aspect_type":"", "mod_type":"", "construct":c_vocab_construct}
                    for s in c_vocab.split(";"):
                        if s != "":
                            k, v = s.split(":")
                            obj[k] = v
                    tmp_dict[biomarker] = obj
        out_file = out_dir + ds + ".json"
        with open(out_file, "w") as FW:
            FW.write("%s\n" % (json.dumps(tmp_dict, indent=4)))
 
    return



def main():

    #old_rel = "3.4.2"
    #dump_legacy(old_rel)

    new_rel = "3.5.1"
    ds = "biomarkers_user_submitted"    
    dump_new(new_rel, ds)
    


    return


if __name__ == '__main__':
    main()
 
            



