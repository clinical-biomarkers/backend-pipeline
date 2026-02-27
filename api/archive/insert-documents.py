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
    parser.add_option("-v","--dataversion",action="store",dest="dataversion",help="2.0.2/2.0.3 ...")
   
    (options,args) = parser.parse_args()

    for key in ([options.server, options.coll, options.dataversion]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    server = options.server
    coll = options.coll
    ver = options.dataversion

    rel_dir = "/data/shared/glygen/releases/data/v-%s/" % (ver)

    db_name = "glydb_beta" if server == "beta" else "glydb"

    config_obj = json.loads(open("./conf/config.json", "r").read())
    #mongo_port = config_obj["dbinfo"]["port"][server]
    mongo_port = "27017"
    host = "mongodb://127.0.0.1:%s" % (mongo_port)
  
    db_obj = config_obj["dbinfo"][db_name]
    glydb_name, db_user, db_pass =  db_obj["db"], db_obj["user"], db_obj["password"]

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
        insert_info = json.loads(open("tmp/list.json", "r").read())
        main_id_field = insert_info["mainidfield"]
        for file_name in insert_info["filelist"]:
    
            db = coll.replace("c_", "") + "db"
            in_file = rel_dir + "jsondb/" + db + "/" + file_name        
            doc = json.loads(open(in_file, "r").read())
            if main_id_field not in doc:
                continue
            main_id = doc[main_id_field]
            res = dbh[coll].delete_one({main_id_field:main_id})
            res = dbh[coll].insert_one(doc)
 
    except pymongo.errors.ServerSelectionTimeoutError as err:
        print (err)
    except pymongo.errors.OperationFailure as err:
        print (err)



if __name__ == '__main__':
    main()
