import os,sys
import string
from optparse import OptionParser
import glob
import json
from bson import json_util
import pymongo
from pymongo import MongoClient
import datetime

from lib_update import search
from optparse import OptionParser
from copied_util import get_hash_id, make_list_objects_indirect, cache_list_objects
import hashlib



def main():

    dd, mm, yy = "*", "*", "2025"
    file_list = glob.glob("/data/shared/glygen/archive/c_cache-%s-%s-%s.json" % (yy, mm, dd))
    stat_dict = {}
    count_dict = {}
    qry_dict = {}
    for in_file in file_list:
        if in_file.find("2025-10") == -1 and in_file.find("2025-09") == -1:
            continue
        obj_list = json.load(open(in_file))
        for obj in obj_list:
            list_id = obj["list_id"]
            qry = obj["cache_info"]["query"] if "query" in obj["cache_info"] else {}
            
            hash_str = json.dumps(qry)
            hash_obj = hashlib.md5(hash_str.encode('utf-8'))
            qry_id =  hash_obj.hexdigest()
            qry_dict[qry_id] = qry
            
            search_type = obj["cache_info"]["search_type"] if "search_type" in obj["cache_info"] else ""
            search_type = "id_mapper" if "mapped_legends" in obj["cache_info"] else search_type
            record_type = obj["cache_info"]["record_type"] if "record_type" in obj["cache_info"] else ""
            record_type = "id_mapper" if "mapped_legends" in obj["cache_info"] else record_type
            if search_type == "":
                if "reqobj" in obj["cache_info"]:
                    continue
            if record_type not in stat_dict:
                stat_dict[record_type] = {}
            if search_type not in stat_dict[record_type]:
                stat_dict[record_type][search_type] = 0
            stat_dict[record_type][search_type] += 1
            result_count = len(obj["results"]) if "results" in obj else 0
            ts = obj["cache_info"]["ts"]
            #cmb = "%s|%s|%s|%s" % (list_id, record_type, search_type, ts)
            cmb = "%s|%s|%s|%s" % (qry_id, record_type, search_type, ts)
            if cmb not in count_dict:
                count_dict[cmb] = 0
            count_dict[cmb] += result_count

    out_dict = {}    
    for cmb in count_dict:
        n = count_dict[cmb]
        parts = cmb.split("|")
        qry_id = parts[0]
        if n > 1000:
            print (n, parts[0],parts[1], parts[2], qry_dict[qry_id])
            doc = {"cmb":cmb, "result_count":n, "query":qry_dict[qry_id]} 
            if n not in out_dict:
                out_dict[n] = []
            out_dict[n].append(doc)
    #for n in sorted(out_dict):
    #    print (json.dumps(out_dict[n], indent=4))
    
 
    #print (json.dumps(stat_dict, indent=4))

    return










if __name__ == '__main__':
    main()
