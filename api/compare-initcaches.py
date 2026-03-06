import os,sys
import string
from optparse import OptionParser
import glob
import json
from bson import json_util
import pymongo
from pymongo import MongoClient
import datetime
from cacheutil import get_comb_list


__version__="1.0"
__status__ = "Dev"



###############################
def main():

    
    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-s","--server",action="store",dest="server",help="dev/tst/beta/prd")
    parser.add_option("-r","--recordtype",action="store",dest="recordtype",help="")
    
    
    (options,args) = parser.parse_args()
    for key in ([options.server, options.recordtype]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    server = options.server
    record_type = options.recordtype

    config_obj = json.loads(open("./conf/config.json", "r").read())
    mongo_port = "27017"
    host = "mongodb://127.0.0.1:%s" % (mongo_port)
    db_name = "glydb_beta" if server == "beta" else db_name
    db_obj = config_obj["dbinfo"][db_name]
    db_user, db_pass =  db_obj["user"], db_obj["password"]

    current_day = datetime.date.today()
    ts_format = "%Y-%m-%d"
        
    try:
        client = pymongo.MongoClient(host,
            username=db_user,
            password=db_pass,
            authSource=db_name,
            authMechanism='SCRAM-SHA-1',
            serverSelectionTimeoutMS=10000
        )
        client.server_info()
        dbh = client[db_name]
        seen = {}
        coll = "c_initcache"
        q_obj = {"cache_info.record_type":record_type}
        result_dict, query_dict = {}, {}
        for doc in dbh[coll].find(q_obj):
            cache_info = doc["cache_info"]
            list_id = doc["list_id"]
            cache_name = cache_info["cache_name"] if "cache_name" in cache_info else "no_cache_name"
            if cache_name.find(record_type) == -1:
                continue
            if cache_name == "%s_all" %(record_type):
                continue
            if cache_name not in result_dict:
                result_dict[cache_name] = []
            result_dict[cache_name] += doc["results"]
            query_dict[cache_name] = cache_info["query"]


    

 
        for cache_name in result_dict:
            result_dict[cache_name] = set(result_dict[cache_name])
        cache_name_list = list(result_dict.keys())
    
        comb_list = get_comb_list(cache_name_list) 
        comb_list_new = []
        for cmb in comb_list:
            if len(cmb) != 2:
                continue
            f_0 = "_".join(cmb[0].split("_")[:2])
            f_1 = "_".join(cmb[1].split("_")[:2])
            if f_0 == f_1:
                continue
            comb_list_new.append(cmb)
        

        for cmb in comb_list_new:
            if len(cmb) != 2:
                continue
            tmp_list = list(cmb)
            name_1 = tmp_list[0]
            query_1 = query_dict[name_1]
            field_1 = "_".join(name_1.split("_")[:2])
            intr_set = result_dict[name_1]
            for i in range(1, len(tmp_list)):
                name_i = tmp_list[i]
                query_i = query_dict[name_i]
                field_i = "_".join(name_i.split("_")[:2])
                intr_set = intr_set.intersection(result_dict[name_i]) 
            n = len(intr_set)
            if n > 10000:
                print (n, tmp_list)
    
    except pymongo.errors.ServerSelectionTimeoutError as err:
        print (err)
    except pymongo.errors.OperationFailure as err:
        print (err)



if __name__ == '__main__':
    main()
