import os,sys
import string
from optparse import OptionParser
import glob
import json
from bson import json_util
import pymongo
from pymongo import MongoClient
import datetime


__version__="1.0"
__status__ = "Dev"



###############################
def main():

    
    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-s","--server",action="store",dest="server",help="dev/tst/beta/prd")
    parser.add_option("-c","--coll",action="store",dest="coll",help="") 
    (options,args) = parser.parse_args()

    for key in ([options.server, options.coll]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    server = options.server
    coll = options.coll


    config_obj = json.loads(open("./conf/config.json", "r").read())
    mongo_port = "27017"
    host = "mongodb://127.0.0.1:%s" % (mongo_port)

    db_name = "glydb"
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
        for doc in dbh[coll].find({}, {"list_id":1,"cache_info":1, "total_count":1}):
            for k in ["_id"]:
                if k in doc:
                    doc.pop(k)
            cache_info = doc["cache_info"]
            ts = cache_info["ts"] if "ts" in cache_info else "no_ts"
            list_id = doc["list_id"]
            if coll.find("listcache") != -1:
                list_id = "%s|%s" % (cache_info["cache_id"], list_id)

            record_type = cache_info["record_type"] if "record_type" in cache_info else "no_record_type"
            search_type = cache_info["search_type"] if "search_type" in cache_info else "no_search_type"
            cache_name = cache_info["cache_name"] if "cache_name" in cache_info else "no_cache_name"
            total_count = doc["total_count"] if "total_count" in doc else -1
            cmb = "%s|%s|%s|%s|%s" % (coll, list_id,cache_name,record_type,total_count)
            if cmb not in seen:
                print (cmb, ts)
                seen[cmb] = True

    except pymongo.errors.ServerSelectionTimeoutError as err:
        print (err)
    except pymongo.errors.OperationFailure as err:
        print (err)



if __name__ == '__main__':
    main()
