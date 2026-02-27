import os,sys
import string
import pytz
import datetime
from optparse import OptionParser
import glob
import json
import hashlib
import pymongo
from pymongo import MongoClient
from itertools import combinations

from lib_update import supersearch_search, get_mongodb
from optparse import OptionParser
from copied_util import get_hash_id, make_list_objects_indirect, cache_list_objects, get_query_filter_code, get_filter_conf, get_list_objects, get_grp_id_list

from cacheutil import cache_exists, delete_cache, get_c_initcache_queries,get_supersearch_init_query,get_supersearch_log_lines

import orjson


def cache_hitlist(dbh,list_id, record_list, cache_info, cache_coll):

    res = dbh[cache_coll].delete_many({"list_id":list_id})
    total_count = len(record_list)
    partition_count = total_count/cache_batch_size
    for i in range(0,int(partition_count)+1):
        start = i*cache_batch_size
        end = start + cache_batch_size
        end = total_count if end > total_count else end
        cache_info["start"] = start
        if start < total_count:
            cache_obj = {
                "list_id":list_id,
                "cache_info":cache_info,
                "total_count":total_count,
                "results":record_list[start:end]
            }
            res = dbh[cache_coll].insert_one(cache_obj)

    return



def update_c_initcache(dbh, cache_name, list_id, record_type, query_info):


    query_obj, main_field = query_info["query"], query_info["mainfield"]
    search_type = "%s_search" % (record_type)
    mongo_query = query_info["mongoquery"]
    coll = "c_" + record_type
    cache_coll = "c_initcache"
       
    record_list = []
    if cache_name == "biomarker_all":
        file_list = glob.glob("/data/shared/biomarkerdb/releases/data/v-3.1.1/jsondb/listdb/*.json")
        for i in range(0, len(file_list)):
            in_file = file_list[i]
            doc_list = orjson.loads(open(in_file,"r").read())
            for doc in doc_list:
                record_list.append(doc["biomarker_id"])
    else:
        record_list = []
        prj_obj = {main_field:1}
        for obj in dbh[coll].find(mongo_query,prj_obj):
            record_list.append(obj[main_field])
 
    res_obj = {}
    if cache_name.find("_all") != -1 or len(record_list) > min_list_size_to_cache:
        #delete any cache by cache_name
        res = dbh["c_initcache"].delete_many({"cache_info.cache_name":cache_name})
        ts_format = "%Y-%m-%d %H:%M:%S %Z%z"
        ts = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format)
        cache_info = {
            "cache_name":cache_name,
            "query":query_obj,
            "ts":ts,
            "record_type":record_type,
            "search_type":search_type
        }
        cache_hitlist(dbh,list_id,record_list,cache_info,cache_coll)
        res_obj = {"list_id":list_id, "recordcount":len(record_list)}
    else:
        res_obj = {"list_id":list_id, "recordcount":len(record_list), "flag":"not_large"}
    return res_obj




def main():

    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-s","--server",action="store",dest="server",help="dev/tst/beta/prd")
    parser.add_option("-n","--cachename",action="store",dest="cachename",help="")
    
    
    (options,args) = parser.parse_args()
    for key in ([options.server, options.cachename]):
        if not (key):
            parser.print_help()
            sys.exit(0)
                                         
    server = options.server
    cache_name = options.cachename
    record_type = "biomarker"
    coll = "c_initcache"

    global seen_child
    global min_list_size_to_cache
    global cache_batch_size
    
    
    min_list_size_to_cache = 10000
    cache_batch_size =  5000



    db_name = "bmkbdb_beta" if server == "beta" else "bmkbdb"

    config_obj = json.loads(open("./conf/config.json", "r").read())
    mongo_port = config_obj["dbinfo"]["port"][server]
    host = "mongodb://127.0.0.1:%s" % (mongo_port)
  
    db_obj = config_obj["dbinfo"][db_name]
    db_name, db_user, db_pass =  db_obj["db"], db_obj["user"], db_obj["password"]

    client = pymongo.MongoClient(host,
        username=db_user,
        password=db_pass,
        authSource=db_name,
        authMechanism='SCRAM-SHA-1',
        serverSelectionTimeoutMS=10000
    )
    client.server_info()
    dbh = client[db_name]
    query_doc = {"biomarker":{"biomarker_all":{"query":{},"mongoquery":{}, "mainfield":"biomarker_id"}}}

    qry_dict = query_doc[record_type]
    qry_obj = query_doc[record_type][cache_name]
    api_name = "%s_search" % (record_type)
    list_id = get_hash_id(api_name, record_type, qry_obj["query"])
    #print (list_id, api_name, record_type, qry_obj["query"])

    if cache_exists(dbh, list_id,  "c_initcache"):
        delete_cache(dbh, list_id, "c_initcache")
    res_obj = update_c_initcache(dbh, cache_name, list_id, record_type, qry_obj)
    if "flag" not in res_obj:
        log_file = "logs/c_initcache.%s.%s.log" % (cache_name, server)
        with open(log_file, "w") as FL:
            FL.write("%s,%s,%s\n" % (list_id, res_obj["recordcount"],cache_name))


    return


if __name__ == '__main__':
    main()
