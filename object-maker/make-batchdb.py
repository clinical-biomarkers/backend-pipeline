import os,sys
import json
import glob
import datetime
import csvutil
import subprocess
from optparse import OptionParser
import psutil
import orjson
import hashlib
import random

def main():

       
    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog " )
    parser.add_option("-r","--rel",action="store",dest="rel",help="")
    parser.add_option("-s","--start",action="store",dest="start",help="")
    parser.add_option("-e","--end",action="store",dest="end",help="")
    (options,args) = parser.parse_args()
    for file in ([options.rel, options.start, options.end]):
        if not (file):
            parser.print_help()
            sys.exit(0)

    rel = options.rel
    start = int(options.start)
    end = int(options.end)


    global release_dir
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)

    log_file = "/data/shared/biomarkerdb/logs/make-batchdb.%s-%s.log" % (start, end)
        
    msg = "make-batchdb: started logging"
    csvutil.write_log_msg(log_file, msg, "w")

    file_list = sorted(glob.glob(release_dir + "jsondb/jumbodb/entdb/*.json"))
    batch_idx = 0
    for in_file in file_list[start-1:end]:
        msg = "make-batchdb: processing %s" % (in_file)
        csvutil.write_log_msg(log_file, msg, "a")

        doc = json.load(open(in_file))
        ref_id = doc["ref_id"]
        ent_obj_list = []
        for obj in doc["entities"]:
            ent_obj_list.append(obj)
            out_str = json.dumps(ent_obj_list, indent=4)
            if len(out_str) > 5000000:
                batch_idx += 1
                out_doc = {"batch_id":batch_idx,"record_id":ref_id, "record_type":"entity", "sections":{"entities":ent_obj_list} }
                out_file = release_dir + "jsondb/batchdb/entity.%s.batch.%s.json" % (ref_id, batch_idx)
                with open(out_file, "w") as FW:
                    FW.write("%s\n" % (json.dumps(out_doc, indent=4)))
                ent_obj_list = [] 
        msg = "make-batchdb: done"
        csvutil.write_log_msg(log_file, msg, "a")



    return 




if __name__ == '__main__':
    main()
 
