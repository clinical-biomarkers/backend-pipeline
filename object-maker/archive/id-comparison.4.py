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

    id_list = [
        "BB1482-4","BB1491-4","BB1473-1","AN5599-8","AN5661-7","BB2951-1","AN6747-1",
        "AN6373-1","AN6441-1","AN6176-1","AN6179-1" ,"AN6295-1" ,"AN6400-1" ,"AN6435-1","AN6202-1"
    ]
    ver = "current"
    #db_dir_one = "/data/shared/biomarkerdb/generated/datamodel/merged/%s/merged_json/" %(ver)
    db_dir_one = "/data/shared/biomarkerdb/generated/datamodel/merged/%s/merged_json_updated/" %(ver)

    for biomarker_id in id_list:
        in_file = db_dir_one + biomarker_id + ".json"
        doc = json.load(open(in_file))
        condition_id = doc["condition"]["id"] if doc["condition"] != None else "none"
        cmb_list = []
        for obj in doc["biomarker_component"]:
            ent_id = obj["assessed_biomarker_entity_id"]
            ent_type = obj["assessed_entity_type"]
            orig = obj["biomarker_orig"].lower()
            biomarker = obj["biomarker"].lower()
            print ("%s|%s|%s|%s|%s|%s" % (biomarker_id,condition_id,ent_id,ent_type,orig,biomarker))
    

    return 





if __name__ == '__main__':
    main()
 
