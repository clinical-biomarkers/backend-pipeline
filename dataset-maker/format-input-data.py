import os
import json
import glob





def main():


    rel = "3.5.1"
    downloads_dir = "/data/shared/biomarkerdb/downloads/"
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)

    required_fields = [
        "biomarker_index",
        "component_index",
        "entity_index",
        "assessed_biomarker_entity",
        "assessed_biomarker_entity_id",
        "assessed_entity_type",
        "condition","condition_id",
        "best_biomarker_role","specimen","specimen_id","loinc_code",
        "evidence_source","evidence"
    ]

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

    ignore_list = ["biomarker_controlled_vocab", "component_group", "biomarker_id"]
    ptrn_list = json.load(open("temp/ptrn_list.json"))


    bmkid2idx = {}
    ds_dict = json.load(open(release_dir + "misc/datasets.json"))
    ds_list = list(ds_dict["biomarkers"].keys())
    #ds_list = ["biomarkers_gwas"]
    for ds in ds_list:
        source = ds.replace("biomarkers_","")
        cv_file = "/data/shared/biomarkerdb/vocabdb/%s.json" % (ds)
        if os.path.isfile(cv_file):
            cv_dict = json.load(open(cv_file))
        for file_name in ds_dict["biomarkers"][ds]:
            in_file = downloads_dir + source + "/%s/" % (dir_map[ds]) + file_name
            f_list, f_list_new = [], []
            ent_dict = {}
            bmk_idx, cmp_idx, ent_idx = 0, 0, 0
            out_dir = "/data/shared/biomarkerdb/downloads/%s/2026_08_20_legacy/" % (source)
            out_file = out_dir +  file_name
            row_list = []
            with open(in_file, "r") as FR:
                lcount = 0
                for line in FR:
                    lcount += 1
                    line = line.replace("assesed_biomarker_entity", "assessed_biomarker_entity")
                    row = line.replace("\n", "").replace("\"", "\'").split("\t")
                    if lcount == 1:
                        f_list = row
                        f_list_new = required_fields
                        for f in f_list:
                            if f not in f_list_new and f not in ignore_list:
                                f_list_new.append(f)
                        extra_row =  ["change_type_vocab", "aspect_type_vocab", "mod_type_vocab", "legacy_biomarker_id"]
                        row_list.append(f_list_new + extra_row)
                    else:
                        val_dict = {}
                        for f in f_list:
                            val_dict[f] = row[f_list.index(f)] if f in f_list else ""
                        selected_o = {}
                        biomarker = val_dict["biomarker"] if "biomarker" in val_dict else "not_given"
                        if cv_dict != {}:
                            if biomarker in cv_dict:
                                selected_o = cv_dict[biomarker]
                        if "biomarker_index" in val_dict:
                            bmk_idx = val_dict["biomarker_index"]
                            cmp_idx = val_dict["component_index"]
                            ent_idx = val_dict["entity_index"]
                            #print ("A|%s|b_idx_%s|c_idx_%s|e_idx_%s|%s" % (ds, bmk_idx, cmp_idx,ent_idx,"xxx"))
                        elif "biomarker_id" in val_dict:
                            biomarker_id = val_dict["biomarker_id"]
                            entity_id = val_dict["assessed_biomarker_entity_id"]
                            if biomarker_id != "":
                                
                                if biomarker_id not in ent_dict:
                                    bmk_idx += 1
                                    ent_dict[biomarker_id] = {}
                                    bmkid2idx[biomarker_id] = bmk_idx
                                ent_dict[biomarker_id][entity_id] = True
                                cmp_idx = len(ent_dict[biomarker_id].keys())
                                val_dict["biomarker_index"] = bmkid2idx[biomarker_id] 
                                val_dict["component_index"] = cmp_idx
                                val_dict["entity_index"] = 1
                                #print ("B|%s|b_idx_%s|c_idx_%s|e_idx_%s|%s|%s" % (ds, bmkid2idx[biomarker_id] , cmp_idx, ent_idx,biomarker_id,entity_id))
                            elif "component_group" in val_dict:
                                entity_id = val_dict["assessed_biomarker_entity_id"]
                                biomarker_id = val_dict["component_group"]
                                if biomarker_id not in ent_dict:
                                    ent_dict[biomarker_id] = {}
                                    bmk_idx += 1
                                ent_dict[biomarker_id][entity_id] = True
                                cmp_idx = len(ent_dict[biomarker_id].keys())
                                val_dict["biomarker_index"] = bmk_idx
                                val_dict["component_index"] = cmp_idx
                                val_dict["entity_index"] = 1
                                #print ("X|%s|b_idx_%s|c_idx_%s|e_idx_%s|%s" % (ds, bmk_idx, cmp_idx, ent_idx, "xxx"))
                        elif "component_group" in val_dict:
                            entity_id = val_dict["assessed_biomarker_entity_id"]
                            biomarker_id = val_dict["component_group"]
                            if biomarker_id not in ent_dict:
                                ent_dict[biomarker_id] = {}
                                bmk_idx += 1
                            ent_dict[biomarker_id][entity_id] = True
                            cmp_idx = len(ent_dict[biomarker_id].keys())
                            val_dict["biomarker_index"] = bmk_idx
                            val_dict["component_index"] = cmp_idx
                            val_dict["entity_index"] = 1
                            #print ("C|%s|b_idx_%s|c_idx_%s|e_idx_%s|%s" % (ds, bmk_idx, cmp_idx, ent_idx, "xxx"))
                        newrow = []
                        for f in f_list_new:
                            newrow.append(str(val_dict[f]) if f in val_dict else "")
                        extra_row = []
                        for k in ["change_type", "aspect_type", "mod_type"]:
                            val = "not_specified"
                            if k in selected_o:
                                if selected_o[k] != "":
                                    val = selected_o[k]
                            extra_row.append(val)
                            print (k, val)

                        biomarker_id = "no_legacy_biomarker_id"
                        if "biomarker_id" in val_dict:
                            if val_dict["biomarker_id"] != "":
                                biomarker_id =val_dict["biomarker_id"]
                        extra_row.append(biomarker_id)
                        row_list.append(newrow + extra_row)

            FW = open(out_file, "w")
            for newrow in row_list:
                FW.write("%s\n" % ("\t".join(newrow)))
            FW.close()             
    return


if __name__ == '__main__':
    main()
 
            


