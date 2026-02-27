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
    (options,args) = parser.parse_args()

    for key in ([options.server]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    server = options.server

    config_obj = json.loads(open("./conf/config.json", "r").read())
    mongo_port = "27017"
    host = "mongodb://127.0.0.1:%s" % (mongo_port)
  
    db_info = config_obj["dbinfo"]
    mongo_port = "27017"
    host = "mongodb://127.0.0.1:%s" % (mongo_port)

    admin_client = pymongo.MongoClient(host,
            username=db_info["admin"]["user"],
            password=db_info["admin"]["password"],
            authSource="admin",
            authMechanism='SCRAM-SHA-1',
            serverSelectionTimeoutMS=10000
    )
    admin_client.server_info()
    admin_dbh = admin_client["glydb"]
    
    for coll in ["c_protein", "c_glycan","c_biomarker", "c_disease","c_site" , "c_list"]:
        admin_dbh.command({"planCacheClear": coll})
        print ("flushed cache for collection=%s"%(coll))





if __name__ == '__main__':
    main()
