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

__version__="1.0"
__status__ = "Dev"



###############################
def main():


    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-s","--server",action="store",dest="server",help="dev/tst/beta/prd")
    parser.add_option("-v","--ver",action="store",dest="ver",help="2.0/2.1 ...")
    parser.add_option("-c","--cmp",action="store",dest="cmp",help="data/api/software")
        
    (options,args) = parser.parse_args()

    for key in ([options.server, options.ver, options.cmp]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    server = options.server
    ver = options.ver
    cmp = options.cmp

    config_obj = json.loads(open("./conf/config.json", "r").read())
    mongo_port = config_obj["dbinfo"]["port"][server]
    host = "mongodb://127.0.0.1:%s" % (mongo_port)

    db_name = "bmkbdb_beta" if server == "beta" else "bmkbdb"
    db_user, db_pass = config_obj["dbinfo"][db_name]["user"], config_obj["dbinfo"][db_name]["password"]

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
        coll = "c_version"
        
        doc = dbh[coll].find_one({"component":cmp})
        old_version_list = doc["version_list"] if "version_list" in doc else []
        
        ts = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S %Z%z')
        ver_obj = { "component":cmp, "version":ver, "release_date":ts, "version_list":[ver] + old_version_list}
        res = dbh[coll].update_one({"component":cmp}, {'$set': ver_obj}, upsert=True)
        doc = dbh[coll].find_one({"component":cmp})
        c, v, d = doc["component"], doc["version"], doc["release_date"]
        print (" ... %s version updated to %s on %s"  % (c, v, d))

    except pymongo.errors.ServerSelectionTimeoutError as err:
        print (err)
    except pymongo.errors.OperationFailure as err:
        print (err)



if __name__ == '__main__':
    main()
