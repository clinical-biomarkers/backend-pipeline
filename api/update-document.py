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
    parser.add_option("-v","--dataversion",action="store",dest="dataversion",help="2.0.2/2.0.3 ...")
    parser.add_option("-c","--coll",action="store",dest="coll",help="c_glycan,c_protein ")
    parser.add_option("-r","--recordid",action="store",dest="recordid",help="record_id")        
    (options,args) = parser.parse_args()

    for key in ([options.server, options.dataversion, options.coll, options.recordid]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    global log_file

    server = options.server
    ver = options.dataversion
    coll = options.coll
    record_id = options.recordid

    db = coll.replace("c_", "") + "db"
    in_file = "/data/shared/glygen/releases/data/v-%s/jsondb/%s/%s.json" % (ver, db, record_id)
    doc = json.loads(open(in_file, "r").read()) 



    db_name = "glydb_beta" if server == "beta" else "glydb"
    config_obj = json.loads(open("./conf/config.json", "r").read())
    mongo_port = "27017"
    host = "mongodb://127.0.0.1:%s" % (mongo_port)

    db_obj = config_obj["dbinfo"][db_name]
    db_name, db_user, db_pass =  db_obj["db"], db_obj["user"], db_obj["password"]



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
        q = {"uniprot_canonical_ac": record_id}
        res = dbh[coll].delete_one(q)
        res = dbh[coll].insert_one(doc)
    except pymongo.errors.ServerSelectionTimeoutError as err:
        print (err)
    except pymongo.errors.OperationFailure as err:
        print (err)



if __name__ == '__main__':
    main()
