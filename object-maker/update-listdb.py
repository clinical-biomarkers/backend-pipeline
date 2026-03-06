#!/usr/bin/python
import os,sys
import string
from optparse import OptionParser
import csv
import json
import glob
import csvutil
import subprocess
import datetime
import pytz


def get_biomarker_filter_code(obj):

    code_list = []

    #grp_idx=0 by_assessed_entity_type
    c_list = []
    f_list = ["glycan", "protein"]
    type_list = obj["assessed_entity_type"].replace(" ", "").split(";")
    for f in f_list:
        c_list.append("1" if f.lower() in type_list else "0")
    code_list.append("".join(c_list))
   
 
    #grp_idx=1 by_biomarker_type
    c_list = []
    f_list = ["diagnostic", "monitoring", "predictive", "prognostic", "risk", "response", "safety"]
    type_list = obj["best_biomarker_role"].replace(" ", "").split(";")
    for f in f_list:
        c_list.append("1" if f in type_list else "0")
    code_list.append("".join(c_list))

    return ".".join(code_list)



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


    record_type = "biomarker"
    file_obj_list = []
    glob_str = release_dir + "jsondb/interm/listdb/*.json"
    file_list = glob.glob(glob_str)
    load_size = len(file_list)

    log_file = "/data/shared/biomarkerdb/logs/update-listdb.log"
    msg = "update-listdb: started logging"
    csvutil.write_log_msg(log_file, msg, "w")

    record_count_dict = {}
    local_idx = 0
    for in_list_file in file_list:
        local_idx += 1
        file_name = in_list_file.split("/")[-1]
        out_list_file = release_dir + "jsondb/listdb/%s" % (file_name)
        doc_list = json.loads(open(in_list_file,"r").read())
        if local_idx%10 == 0:
            msg = "update-listdb: created %s/%s %s listdb records" % (local_idx,load_size, record_type)
            csvutil.write_log_msg(log_file, msg, "a")
        for doc in doc_list:
            doc["filter_code"] = get_biomarker_filter_code(doc)

        with open(out_list_file, "w") as FW:
            FW.write("%s\n" % (json.dumps(doc_list, indent=4)))
         

    return



if __name__ == '__main__':
    main()



