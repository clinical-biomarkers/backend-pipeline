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

    
    file_list = glob.glob(release_dir + "jsondb/interm/statdb/*.csv")
    seen = {"entity_type":{}, "role":{}, "source":{}}
    for in_file in file_list:
        with open(in_file, "r") as FR:
            lcount = 0
            for line in FR:
                lcount += 1
                if lcount == 1:
                    continue
                biomarker_id,condition_id,entity_type,role_list,source_list,flags = line.split("\",\"")
                seen["entity_type"][entity_type] = True
                for role in role_list.split(";"):
                    if role != "":
                        seen["role"][role] = True
                for source in source_list.split(";"):
                    if source != "":
                        seen["source"][source] = True

    doc = {
        "best_biomarker_role": list(seen["role"].keys()),
        "assessed_entity_type": list(seen["entity_type"].keys()),
        "simple_search_category": [
            {"id": "any","display": "Any"},
            {"id": "biomarker","display": "Biomarker"},
            {"id": "condition","display": "Condition"}
        ],
        "data_source": list(seen["source"].keys())
    }
    out_file = release_dir + "jsondb/searchinitdb/searchinit.json"
    with open(out_file, "w") as FW:
        FW.write("%s\n" % (json.dumps(doc, indent=4)))


    return

            

if __name__ == '__main__':
	main()



