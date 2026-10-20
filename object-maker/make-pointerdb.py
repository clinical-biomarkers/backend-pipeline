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
    parser.add_option("-s","--start",action="store",dest="start",help="")
    parser.add_option("-e","--end",action="store",dest="end",help="")

    (options,args) = parser.parse_args()
    for file in ([options.start, options.end]):
        if not (file):
            parser.print_help()
            sys.exit(0)

    start = int(options.start)
    end = int(options.end)
    rel = options.rel
    global release_dir
    

    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)
    log_dir = "/data/shared/biomarkerdb/logs/"

    file_list = glob.glob(release_dir + "jsondb/biomarkerdb/*.json")
    end = len(file_list) if len(file_list) < end else end


    log_file = log_dir + "make-pointerdb.%s-%s.log" % (start, end)
    msg = "make-pointerdb: started ... "
    csvutil.write_log_msg(log_file, msg, "w")

    batch_size = len(file_list[start-1:end])
    idx = 0 
    for batch_file in file_list[start-1:end]:
        idx += 1
        doc_list = json.load(open(batch_file))
        batch_index = 0
        for doc in doc_list:
            batch_index += 1
            record_id = ""
            record_id = doc["biomarker_id"]
            if record_id == "":
                continue
            out_doc = {"record_id":record_id, "batch_file":batch_file, "index":batch_index-1}
            out_file = release_dir + "jsondb/pointerdb/%s.json" % (record_id)
            with open(out_file, "w") as FW:
                FW.write("%s\n" % (json.dumps(out_doc, indent=4)))

        msg = "make-pointerdb: processed %s/%s" % (idx, batch_size)
        csvutil.write_log_msg(log_file, msg, "a")            
               
            


    return




if __name__ == '__main__':
    main()


