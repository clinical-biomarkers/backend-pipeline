import os,sys
import json
import glob
import datetime
import csvutil
from optparse import OptionParser
import random
import orjson

def get_list_obj(doc):

    record_obj = {
        "record_id":doc["biomarker_id"],
        "biomarker_canonical_id":doc["biomarker_canonical_id"],
        "biomarker_id":doc["biomarker_id"]
    }
    f_list = ["biomarker", "assessed_biomarker_entity_id", "assessed_entity_type"]
    f_list += ["assessed_biomarker_entity", "specimen", "best_biomarker_role"]
    f_list += ["condition", "exposure_agent", "change_type_vocab", "aspect_type_vocab", "mod_type_vocab"]
    f_list += ["condition_id", "condition_name", "exposure_agent_id", "exposure_agent_name"]
    f_list += ["specimen_id", "specimen_name", "specimen_loinc_code"] 
    seen = {}
    for f in f_list:
        seen[f] = {}


    seen_cmp_evdn = {}
    cmp_count = 0
    for obj in doc["biomarker_component"]:
        cmp_count += 1
        for f in ["biomarker", "assessed_biomarker_entity_id", "assessed_entity_type"]:
            val = obj[f]
            seen[f][val] = True
        f = "assessed_biomarker_entity"
        val = obj[f]["recommended_name"]
        seen[f][val] = True 
        f = "specimen"
        for o in obj[f]:
            val = "%s (%s)" % (o["name"], o["id"])
            seen[f][val] = True
            seen["specimen_id"][o["id"]] = True
            seen["specimen_name"][o["name"]] = True
            if "loinc_code" in o:
                seen["specimen_loinc_code"][o["loinc_code"]] = True
        f = "evidence_source"
        for o in obj[f]:
            if o["database"] in ["PubMed", "DOI"]:
                seen_cmp_evdn[o["id"]] = True

    f = "best_biomarker_role"
    for obj in doc[f]:
        val = obj["role"]
        seen[f][val] = True

    for f in ["change_type_vocab", "aspect_type_vocab", "mod_type_vocab"]:
        if "c_vocab" in doc:
            if f in doc["c_vocab"]:
                val = doc["c_vocab"][f]
                seen[f][val] = True

    for f in ["condition", "exposure_agent"]:
        if f in doc:
            if doc[f] != {}:
                if "recommended_name" in doc[f]:
                    obj = doc[f]["recommended_name"]
                    if "id" in obj and "name" in obj:
                        val = "%s (%s)"%(obj["name"], obj["id"])
                        seen[f][val] = True
                        if f == "condition":
                            seen["condition_id"][obj["id"]] = True
                            seen["condition_name"][obj["name"]] = True
                        if f == "exposure_agent":
                            seen["exposure_agent_id"][obj["id"]] = True
                            seen["exposure_agent_name"][obj["name"]] = True
                    #for o in doc[f]["synonyms"]:
                    #    val = "%s (%s)" % (o["name"], o["id"])
                    #    seen[f][val] = True

                    


    seen_glbl_evdn, seen_glbl_evdn_src = {}, {}
    f = "evidence_source"
    for o in doc[f]:
        if o["database"] in ["PubMed", "DOI"]:
            seen_glbl_evdn[o["id"]] = True
        else:
            seen_glbl_evdn_src[o["id"]] = True

    for f in f_list:
        if f not in seen:
            seen[f][""] = True
        record_obj[f] = "; ".join(seen[f].keys())

    record_obj["component_count"] = cmp_count
    record_obj["component_evidence_count"] = len(list(seen_cmp_evdn.keys()))
    record_obj["global_evidence_count"] = len(list(seen_glbl_evdn.keys()))
    record_obj["global_evidence_count_src"] = len(list(seen_glbl_evdn_src.keys()))

    w_dict = { 
        "component_evidence_count":0.1
        ,"global_evidence_count":0.1
    }
    record_obj["hit_score"] = 0.1
    for p in w_dict:
        record_obj["hit_score"] += float(w_dict[p] *record_obj[p])
    record_obj["hit_score"] = round(record_obj["hit_score"], 2)

    record_obj["publication_id"] = ";".join(list(seen_glbl_evdn.keys()))
    record_obj["data_source"] = ";".join(doc["source_list"]) if "source_list" in doc else ""
 
    #print (json.dumps(record_obj, indent=4))
    #exit()

    return record_obj





###############################
def main():

    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-r","--rel",action="store",dest="rel",help="")
    (options,args) = parser.parse_args()
    for key in ([ options.rel]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    rel = options.rel


    global release_dir

    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)




    file_list = glob.glob(release_dir + "jsondb/biomarkerdb/*.json")
    file_list = sorted(file_list)

    log_file = "/data/shared/biomarkerdb/logs/make-listdb.txt"
    with open(log_file, "w") as FL:
        FL.write("")
        


        
    idx = 0
    total = len(file_list)
    for in_file in file_list:
        idx += 1
        doc_list = orjson.loads(open(in_file, "rb").read())
        record_obj_list = []
        for doc in doc_list:
            list_obj = get_list_obj(doc)
            record_obj_list.append(list_obj)
        
        file_name = in_file.split("/")[-1]
        out_file = release_dir + "jsondb/interm/listdb/%s" % (file_name)
        with open(out_file, "wb") as FW:
            FW.write(orjson.dumps(record_obj_list))

        with open(log_file, "a") as FL: 
            FL.write("make-listdb: finished %s/%s\n" % (idx, total))
        


    return 




if __name__ == '__main__':
    main()
 
