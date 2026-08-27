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



    
    file_list = glob.glob(release_dir +  "jsondb/interm/statdb/*.csv")
    ent_type_stat = {}
    seen = {"condition":{}, "exposure_agent":{},"biomarker":{}, "biomarker_single":{}, "biomarker_multi":{}}
    for in_file in file_list:
        with open(in_file, "r") as FR:
            lcount = 0
            for line in FR:
                lcount += 1
                if lcount == 1:
                    continue
                row = line.strip().split("\",\"")
                biomarker_id,condition_id,agent_id,ent_type, role,src, keywords,flags = row
                if condition_id != "":
                    seen["condition"][condition_id] = True
                if agent_id != "":
                    seen["exposure_agent"][agent_id] = True
                if biomarker_id != "":
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
        "Unique Exposure Agent": len(seen["exposure_agent"].keys()),
        "Unique Biomarker": len(seen["biomarker"].keys()),
        "Single Biomarker": len(seen["biomarker_single"].keys()),
        "Multicomponent Biomarker": len(seen["biomarker_multi"].keys())
    }
    obj_two = {"title": "Entity Types"}
    for ent_type in ent_type_stat:
        obj_two[ent_type] = ent_type_stat[ent_type]

    doc = { "stat":[obj_one, obj_two]}
    out_file = release_dir + "jsondb/statdb/stat.json"
    with open(out_file, "w") as FW:
        FW.write("%s\n" % (json.dumps(doc, indent=4)))


    return

            

if __name__ == '__main__':
	main()



