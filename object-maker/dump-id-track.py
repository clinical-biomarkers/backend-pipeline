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
    parser.add_option("-c","--c",action="store",dest="canon",help="")
    (options,args) = parser.parse_args()
    for key in ([ options.canon]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    rel = "3.1.1"
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)

    canon_id = options.canon
    file_list = glob.glob(release_dir + "jsondb/idgendb/*.json")
    for in_file in file_list:
        doc_list = json.load(open(in_file))
        for doc in doc_list:
            if doc["canon_id_new"] == canon_id:
                print (json.dumps(doc, indent=4))

    return 





if __name__ == '__main__':
    main()
 
