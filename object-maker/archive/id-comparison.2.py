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


    #ver = "2025_12_22"
    ver = "current"
    #db_dir_one = "/data/shared/biomarkerdb/generated/datamodel/merged/%s/merged_json/" %(ver)
    db_dir_one = "/data/shared/biomarkerdb/generated/datamodel/merged/%s/merged_json_updated/" %(ver)

    seen = {}
    in_file = "/data/shared/biomarkerdb/tmp/qc_110.txt"
    with open(in_file, "r") as FR:
        for line in FR:
            biomarker_id = line.split(" ")[0]
            old_file = db_dir_one + biomarker_id + ".json"
            doc = json.load(open(old_file))
            if doc["condition"] == None:
                continue
            condition_id = doc["condition"]["id"]
            cmb_list = []
            for obj in doc["biomarker_component"]:
                ent_id = obj["assessed_biomarker_entity_id"]
                biomarker = obj["biomarker"].lower()
                cmb_list.append("%s|%s" % (ent_id, biomarker))
            #print (biomarker_id, condition_id, cmb_list, doc["source_list"]) 
            seen[biomarker_id] = True
    
    in_file = "junk1"
    with open(in_file, "r") as FR:
        for line in FR:
            biomarker_id = line.split(" ")[0]
            if biomarker_id in seen:
                biomarker = line.strip().split("|")[-1]
                print (biomarker_id, biomarker)
 
    return 





if __name__ == '__main__':
    main()
 
