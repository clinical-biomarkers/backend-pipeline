import os,sys
import string
from optparse import OptionParser
import glob
import json
import csvutil
import datetime
import pytz

__version__="1.0"
__status__ = "Dev"



def main():
    
    file_list = glob.glob("jsondb/interm/statdb/*.csv")
    ent_type_stat = {}
    seen = {"condition":{}, "biomarker":{}, "biomarker_single":{}, "biomarker_multi":{}}
    for in_file in file_list:
        with open(in_file, "r") as FR:
            lcount = 0
            for line in FR:
                lcount += 1
                if lcount == 1:
                    continue
                row = line.strip().split("\",\"")
                biomarker_id,condition_id,ent_type, role,src, flags = row
                seen["condition"][condition_id] = True
                seen["biomarker"][biomarker_id] = True
                if flags.find("biomarker_single") != -1:
                    seen["biomarker_single"][biomarker_id] = True
                if flags.find("biomarker_multi") != -1:
                    seen["biomarker_multi"][biomarker_id] = True
                if ent_type not in ent_type_stat:
                    ent_type_stat[ent_type] = 0
                ent_type_stat[ent_type] += 1

    obj_one = {
        "title": "Database Statistics",
        "Unique Condition": len(seen["condition"].keys()),
        "Unique Biomarker": len(seen["biomarker"].keys()),
        "Single Biomarker": len(seen["biomarker_single"].keys()),
        "Multicomponent Biomarker": len(seen["biomarker_multi"].keys())
    }
    obj_two = {"title": "Entity Types"}
    for ent_type in ent_type_stat:
        obj_two[ent_type] = ent_type_stat[ent_type]

    doc = { "stat":[obj_one, obj_two]}
    out_file = "jsondb/statdb/stat.json"
    with open(out_file, "w") as FW:
        FW.write("%s\n" % (json.dumps(doc, indent=4)))


    return

            

if __name__ == '__main__':
	main()



