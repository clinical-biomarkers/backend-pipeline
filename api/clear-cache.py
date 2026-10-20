import os,sys
import string
from optparse import OptionParser
import glob
import json
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
    mongo_port = config_obj["dbinfo"]["port"][server]

    host = "mongodb://127.0.0.1:%s" % (mongo_port)
    db_name = "bmkbdb"
    db_obj = config_obj["dbinfo"][db_name]
    db_user, db_pass =  db_obj["user"], db_obj["password"]

    if coll in ["c_initcache", "c_initlistcache"]:
        print ("\n\tAre you sure you want to delete this collection?!!!\n\n")
        exit()



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
        
        index_info = {
            "c_usercache":{
                "list_id":"list_id_index"
            },
            "c_userlistcache":{
                "list_id":"list_id_index",
                "glbl.cache_info.cache_id":"glbl_cache_info_cache_id_index"
            }
        }
        doc_dict = {
            "c_usercache":{"list_id":""},
            "c_userlistcache":{"list_id":"","glbl":{"cache_info":{"cache_id":""}}}
        }
        dbh[coll].drop()
        res = dbh[coll].insert_one(doc_dict[coll])
       
         
        index_name_list = []
        for cur in dbh[coll].list_indexes():
            index_name_list.append(cur["name"])

        for path in index_info[coll]:
            index_name = index_info[coll][path]
            if index_name in index_name_list:
                res = dbh[coll].drop_index(index_name)
            res = dbh[coll].create_index([(path, -1 )], name=index_name)


        seen = {}
        for doc in dbh[coll].find({}):
            if len(doc.keys()) == 1:
                res = dbh[coll].delete_many({"_id":doc["_id"]})
                print ("deleted|empty cache")
                continue
            list_id = doc["list_id"]
            if list_id in seen:
                continue
            seen[list_id] = True
            empty_search_flag, search_type = False, ""
            cache_info = {}
            cache_info = doc["cache_info"] if "cache_info" in doc else cache_info
            if "glbl" in doc:
                cache_info = doc["glbl"]["cache_info"] if "cache_info" in doc["glbl"] else cache_info
            if "empty_search_flag" in cache_info:
                empty_search_flag = cache_info["empty_search_flag"]
            if "search_type" in cache_info:
                search_type = cache_info["search_type"]
            cache_id = cache_info["cache_id"] if "cache_id" in cache_info else ""
            listcache_id = cache_info["listcache_id"] if "listcache_id" in cache_info else ""
            total = cache_info["total"] if "total" in cache_info else -1
            res = dbh[coll].delete_many({"list_id":list_id})
            print ("deleted|%s|%s|%s" % (search_type, list_id, total))



    except pymongo.errors.ServerSelectionTimeoutError as err:
        print (err)
    except pymongo.errors.OperationFailure as err:
        print (err)



if __name__ == '__main__':
    main()

