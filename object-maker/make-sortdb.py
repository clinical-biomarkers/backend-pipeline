#!/usr/bin/python
import os,sys
import string
import csv
import json
import glob
import subprocess
from optparse import OptionParser
import csvutil
import datetime
import pytz


def sort_objects(list_objects, return_fields, field_name, order_type):

    field_list = return_fields["float"] + return_fields["int"] + return_fields["string"]
    grid_obj = {}
    for f in field_list:
        grid_obj[f] = []
    for i in range(0, len(list_objects)):
        obj = list_objects[i]
        if field_name in return_fields["float"]:
            if field_name not in obj:
                obj[field_name] = -1.0
            grid_obj[field_name].append({"index":i, field_name:float(obj[field_name])})
        elif field_name in return_fields["string"]:
            if field_name not in obj:
                obj[field_name] = ""
            grid_obj[field_name].append({"index":i, field_name:obj[field_name]})
        elif field_name in return_fields["int"]:
            if field_name not in obj:
                obj[field_name] = -1
            grid_obj[field_name].append({"index":i, field_name:int(obj[field_name])})
    reverse_flag = True if order_type == "desc" else False
    key_list = []
    sorted_list_objects = sorted(grid_obj[field_name], key=lambda x: x[field_name], reverse=reverse_flag)
    for o in sorted_list_objects:
            key_list.append(o["index"])
    return key_list




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


    ts_format = "%Y-%m-%d %H:%M:%S %Z%z"
    START_TS = datetime.datetime.now(pytz.timezone('US/Eastern'))

    log_file = "/data/shared/biomarkerdb/logs/make-sortdb.log"
    msg = "make-sortdb: startd ..."
    csvutil.write_log_msg(log_file, msg, "w")
   
    record_count = 0 
    list_init_file = "/data/shared/repos/backend-pipeline/api/bmkb/conf/list_init.json"
    list_init_doc = json.load(open(list_init_file))
    
    record_type = "biomarker"
    field_list = []
    for obj in list_init_doc[record_type]["columns"]:
        field_list.append(obj["id"])
    list_objects = []
    file_list = glob.glob(release_dir + "jsondb/listdb/*.json")
    ts_flag = "0-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format)
    #print (ts_flag, len(file_list))
    idx = 0
    for list_file in file_list:
        idx += 1    
        doc_list = json.load(open(list_file))
        for doc in doc_list:
            list_objects.append(doc)


    msg = "make-sortdb: loaded %s %s listdb files" % (len(file_list), record_type)
    csvutil.write_log_msg(log_file, msg, "a")
    ts_flag = "1-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format)
    #print (ts_flag)

    return_fields = {"string":[], "int":[], "float":[]}
    for f in field_list:
        if f not in list_objects[0]:
            continue
        if type(list_objects[0][f]) is str:
            return_fields["string"].append(f)
        elif type(list_objects[0][f]) is int:
            return_fields["int"].append(f)
        elif type(list_objects[0][f]) is float:
            return_fields["float"].append(f)

    sort_order =  "asc"
    ordr_dict = {}
    for sort_field in return_fields["string"] + return_fields["int"] + return_fields["float"]:
        ts_flag = "2-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format)
        #print (ts_flag, sort_field)
        ordr_dict[sort_field] = [] 
        sorted_id_list = sort_objects(list_objects, return_fields, sort_field, sort_order)
        ordr = 1
        for idx in sorted_id_list:
            record_id = list_objects[idx]["record_id"]
            ordr_dict[sort_field].append(record_id)
        ts_flag = "3-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format)
        #print (ts_flag, sort_field)

    batch_size = 100000
    for sort_field in ordr_dict:
        record_list = ordr_dict[sort_field]
        grp = 0
        for offset in range(0, len(record_list), batch_size):
            tmp_record_list = record_list[offset:offset + batch_size]
            out_doc = {"offset":offset, "sort_field":sort_field, "record_type":record_type, 
                "record_list":tmp_record_list}
            grp += 1
            out_file = release_dir + "jsondb/sortdb/%s.%s.%s.json" % (record_type, sort_field, grp)
            with open(out_file, "w") as FW:
                FW.write("%s\n" % (json.dumps(out_doc, indent=4)))
            record_count += 1
            ts_flag = "4-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format)
            #print (ts_flag, out_file)
            msg = "make-sortdb: created %s" % (out_file)
            csvutil.write_log_msg(log_file, msg, "a")

    msg = "FINAL: %s files" % (record_count)
    csvutil.write_log_msg(log_file, msg, "a")

    END_TS = datetime.datetime.now(pytz.timezone('US/Eastern'))
    diff = END_TS - START_TS
    elapsed = round(diff.total_seconds()/60.0, 3)
    msg = "ELAPSED: %s minutes" % (elapsed)
    csvutil.write_log_msg(log_file, msg, "a")

    return



if __name__ == '__main__':
    main()



