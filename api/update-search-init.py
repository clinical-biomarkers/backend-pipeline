import os,sys
import string
from optparse import OptionParser
import glob
import json
from bson import json_util
import pymongo
from pymongo import MongoClient
import datetime
from optparse import OptionParser




def main():

    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-s","--server",action="store",dest="server",help="dev/tst/beta/prd")
    (options,args) = parser.parse_args()
    for key in ([options.server]):
        if not (key):
            parser.print_help()
            sys.exit(0)
                                         
    server = options.server

    config_obj = json.loads(open("./conf/config.json", "r").read())
    mongo_port = "27017"
    host = "mongodb://127.0.0.1:%s" % (mongo_port)
    db_name = "glydb_beta" if server == "beta" else "glydb"
    db_obj = config_obj["dbinfo"][db_name]
    glydb_name, db_user, db_pass =  db_obj["db"], db_obj["user"], db_obj["password"]
    host_ip = config_obj["host_ip"][server]

    config_obj = json.load(open("glygen/conf/config.json"))
    config_obj["db_info"] = {
        "user":db_user, "password":db_pass, "host_ip":host_ip, "db_name":db_name
    }
 
    try:
        client = pymongo.MongoClient(host,
            username=db_user,
            password=db_pass,
            authSource=glydb_name,
            authMechanism='SCRAM-SHA-1',
            serverSelectionTimeoutMS=10000
        )
        client.server_info()
        dbh = client[glydb_name]
    
        doc = dbh["c_initcache"].find_one({"cache_info.cache_name":"supersearch_all"})
        if doc != None:
            result_summary = doc["cache_info"]["result_summary"]
            q_obj = {}
            update_obj = {"supersearch_init":result_summary}
            print ("updating c_searchinit ...")
            res = dbh["c_searchinit"].update_one(q_obj, {'$set':update_obj}, upsert=True)
            print ("done")
    except pymongo.errors.ServerSelectionTimeoutError as err:
        print (err)
    except pymongo.errors.OperationFailure as err:
        print (err)



    return


if __name__ == '__main__':
    main()
