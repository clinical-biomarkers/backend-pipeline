import os,sys
import json
import glob
import datetime
import csvutil
from optparse import OptionParser
import random
import orjson




###############################
def main():

    ver = "current"
    db_dir_one = "/data/shared/biomarkerdb/generated/datamodel/merged/%s/merged_json_updated/" %(ver)

    seen = {}
    merge_idx = 0
    file_list = glob.glob("jsondb/idtrackdb/*.json")
    for in_file in file_list:
        doc_list = json.load(open(in_file))
        for doc in doc_list:
            if "biomarker_id_list" not in doc:
                continue
            biomarker_id_new = doc["biomarker_id_new"]
            old_id_list = ";".join(doc["biomarker_id_list"])
            #print (biomarker_id_new, old_id_list)
            if len(doc["biomarker_id_list"]) > 1:
                merge_idx += 1
                print ("//\n>merge_%s" % (merge_idx))
                for biomarker_id in doc["biomarker_id_list"]:
                    in_file = db_dir_one + biomarker_id + ".json"
                    old_doc = json.load(open(in_file))
                    condition_id = old_doc["condition"]["id"] if old_doc["condition"] != None else "none"
                    for obj in old_doc["biomarker_component"]:
                        ent_id = obj["assessed_biomarker_entity_id"]
                        orig = obj["biomarker_orig"]
                        biomarker = obj["biomarker"]
                        print ("%s|%s|%s|%s" % (biomarker_id,condition_id,ent_id,orig)) 


    return 





if __name__ == '__main__':
    main()
 
