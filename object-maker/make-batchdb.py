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
    (options,args) = parser.parse_args()
    for file in ([options.rel]):
        if not (file):
            parser.print_help()
            sys.exit(0)

    rel = options.rel


    global release_dir
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)


     # clean out_dir
    out_dir = release_dir + "jsondb/batchdb/"
    if os.path.isdir(out_dir):
        cmd = "rm -rf %s/*" % (out_dir)
        x = subprocess.getoutput(cmd)


    log_file = "/data/shared/biomarkerdb/logs/make-batchdb.log" 
    msg = "make-batchdb: started logging"
    csvutil.write_log_msg(log_file, msg, "w")

    file_list = sorted(glob.glob(release_dir + "jsondb/jumbodb/entdb/*.json"))
    batch_idx = 0
    for in_file in file_list:
        file_name = in_file.split("/")[-1]
        msg = "make-batchdb: processing %s" % (file_name)
        csvutil.write_log_msg(log_file, msg, "a")
        doc = json.load(open(in_file))
        ref_id = doc["ref_id"]
        ent_obj_list = []
        idx = 0
        for obj in doc["entities"]:
            idx += 1
            ent_obj_list.append(obj)
            if idx%100 == 0:
                batch_idx += 1
                out_doc = {"batch_id":batch_idx,"record_id":ref_id, "record_type":"entity", "sections":{"entities":ent_obj_list} }
                out_file = release_dir + "jsondb/batchdb/entity.%s.batch.%s.json" % (ref_id, batch_idx)
                with open(out_file, "w") as FW:
                    FW.write("%s\n" % (json.dumps(out_doc, indent=4)))
                ent_obj_list = [] 
        if len(ent_obj_list) > 0:
            batch_idx += 1
            out_doc = {"batch_id":batch_idx,"record_id":ref_id, "record_type":"entity", "sections":{"entities":ent_obj_list} }
            out_file = release_dir + "jsondb/batchdb/entity.%s.batch.%s.json" % (ref_id, batch_idx)
            with open(out_file, "w") as FW:
                FW.write("%s\n" % (json.dumps(out_doc, indent=4)))



    return 




if __name__ == '__main__':
    main()
 
