import os,sys
import json
import glob
import datetime
import csvutil
from optparse import OptionParser
import random




###############################
def main():

    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-s","--start",action="store",dest="start",help="")
    parser.add_option("-e","--end",action="store",dest="end",help="")
    (options,args) = parser.parse_args()
    for key in ([ options.start, options.end]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    s = int(options.start)
    e = int(options.end)




    #ver = "2025_12_22"
    ver = "current"
    #db_dir_one = "/data/shared/biomarkerdb/generated/datamodel/merged/%s/merged_json/" %(ver)
    db_dir_one = "/data/shared/biomarkerdb/generated/datamodel/merged/%s/merged_json_updated/" %(ver)
    sec_list = [ 
        "biomarker_id", "biomarker_component", "condition", "evidence_source", "best_biomarker_role", 
        "biomarker_canonical_id", "citation", "crossref", "source_list", 
        "entity_normal_ranges"
    ]
    file_list = glob.glob(db_dir_one + "*.json")

    e = len(file_list) if e > len(file_list) else e 
    idx = 0
    total = len(file_list)
    seen = {}
    d_name_dict = {}
    for in_file in file_list[s-1:e]:
        idx += 1
        #if idx%100 == 0:
        #    print ("parsed %s/%s" % (idx, total))

        biomarker_id = in_file.split("/")[-1].split(".")[0]
        doc = json.load(open(in_file))
        scr = 0.0
        for o in doc["score_info"]["contributions"]:
            scr += o["f"]*o["w"]
            if o["c"] not in seen:
                seen[o["c"]] = True
            #if o["c"] == "generic_condition_pen" and o["f"] != "0":
            #    print (biomarker_id, doc["source_list"], doc["condition"]["recommended_name"]["name"])
            d_name = doc["condition"]["recommended_name"]["name"]
            if o["c"] == "generic_condition_pen":
                if d_name not in d_name_dict:
                    d_name_dict[d_name] = {}
                d_name_dict[d_name][str(o["f"])] = True
        #print ("//\n")

        #print (biomarker_id, json.dumps(doc["score_info"], indent=4)) 
        #if doc["score"] != -1:
        #    print (biomarker_id, doc["score"], scr)
        #exit() 


     
    out_file = "logs/parse.%s-%s.txt" % (s, e)
    with open(out_file, "w") as FW:
        for d_name in d_name_dict:
            flag = "1" if "0.0" in d_name_dict[d_name] else "0"
            flag += "1" if "1.0" in d_name_dict[d_name] else "0"
            FW.write("%s,%s\n" % (flag, d_name))



    return 




if __name__ == '__main__':
    main()
 
