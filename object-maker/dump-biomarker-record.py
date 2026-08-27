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
    parser.add_option("-i","--id",action="store",dest="id",help="")
    
    (options,args) = parser.parse_args()
    for key in ([ options.rel, options.id]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    rel = options.rel
    biomarker_id = options.id
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)

    file_list = glob.glob(release_dir + "jsondb/biomarkerdb/*.json")
    for in_file in file_list:
        doc_list = json.load(open(in_file))
        for doc in doc_list:
            if doc["biomarker_id"] == biomarker_id:
                print (json.dumps(doc, indent=4))
                exit()
    return 





if __name__ == '__main__':
    main()
 
