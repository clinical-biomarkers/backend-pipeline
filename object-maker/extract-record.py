#!/usr/bin/python
import os,sys
import string
import csv
import json
import glob
import csvutil
import subprocess
from optparse import OptionParser
import datetime
import pytz




def main():

      
    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog " )
    parser.add_option("-r","--rel",action="store",dest="rel",help="")
    parser.add_option("-i","--recordid",action="store",dest="recordid",help="")

    (options,args) = parser.parse_args()
    for file in ([options.rel, options.recordid]):
        if not (file):
            parser.print_help()
            sys.exit(0)

    rel = options.rel
    record_id = options.recordid

    pointer_file = "/data/shared/biomarkerdb/releases/data/v-%s/jsondb/pointerdb/%s.json" % (rel,record_id)
    if os.path.isfile(pointer_file) == False:
        print ("pointer does not exist!")
        exit()

    pointer_doc = json.load(open(pointer_file))
    
    batch_file, index = pointer_doc["batch_file"], pointer_doc["index"]
    doc_list = json.load(open(batch_file))
    doc = doc_list[index]
    print (json.dumps(doc, indent=4))


    return




if __name__ == '__main__':
    main()
