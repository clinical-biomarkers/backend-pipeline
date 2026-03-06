import os,sys
import string
from optparse import OptionParser
import glob
import json
from bson import json_util
import pymongo
from pymongo import MongoClient
import datetime
import pytz
import subprocess

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

    global log_file

    server = options.server

    config_obj = json.loads(open("./conf/config.json", "r").read())
    mongo_port = config_obj["dbinfo"]["port"][server]
    host = "mongodb://127.0.0.1:%s" % (mongo_port)

    glydb_user = config_obj["dbinfo"]["glydb"]["user"]
    glydb_pass = config_obj["dbinfo"]["glydb"]["password"]
    glydb_name =  config_obj["dbinfo"]["glydb"]["db"]

    try:
        glydb_client = pymongo.MongoClient(host,
            username=glydb_user,
            password=glydb_pass,
            authSource=glydb_name,
            authMechanism='SCRAM-SHA-1',
            serverSelectionTimeoutMS=10000
        )
        glydb_dbh = glydb_client[glydb_name]
        for c in glydb_dbh.list_collection_names():
            print (c)
    except pymongo.errors.ServerSelectionTimeoutError as err:
        print (err)
    except pymongo.errors.OperationFailure as err:
        print (err)



if __name__ == '__main__':
    main()
