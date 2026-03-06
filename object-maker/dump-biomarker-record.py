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

    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-r","--rel",action="store",dest="rel",help="")
    (options,args) = parser.parse_args()
    for key in ([ options.rel]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    rel = options.rel
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)

    file_list = glob.glob(release_dir + "jsondb/biomarkerdb/*.json")
    for in_file in file_list:
        doc_list = json.load(open(in_file))
        for doc in doc_list:
            #print (json.dumps(doc, indent=4))
            #exit()
            for obj in doc["biomarker_component"]:
                if obj["specimen"] != []:
                    for o in obj["specimen"]:
                        if o["loinc_code"] != "":
                            print (json.dumps(doc, indent=4))
                            exit()
    return 





if __name__ == '__main__':
    main()
 
