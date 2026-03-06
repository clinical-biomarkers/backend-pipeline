import os,sys
import string
from optparse import OptionParser
import glob
import json
from bson import json_util
import pymongo
from pymongo import MongoClient
import bcrypt
import base64
import datetime
import pytz

__version__="1.0"
__status__ = "Dev"



###############################
def main():


    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-s","--srv",action="store",dest="srv",help="dev/tst/beta/prd")
    parser.add_option("-e","--email",action="store",dest="email",help="")
    parser.add_option("-p","--password",action="store",dest="password",help="")
        
    (options,args) = parser.parse_args()

    for key in ([options.srv, options.email, options.password]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    srv = options.srv
    email = options.email
    password = options.password


    config_obj = json.loads(open("./conf/config.json", "r").read())
    mongo_port = config_obj["dbinfo"]["port"][srv]
    host = "mongodb://127.0.0.1:%s" % (mongo_port)

    db_user, db_pass = config_obj["dbinfo"]["bmkbdb"]["user"], config_obj["dbinfo"]["bmkbdb"]["password"]
    db_name = "bmkbdb_beta" if srv == "beta" else "bmkbdb"

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
        coll = "c_users"
        res = dbh[coll].delete_one({"email":email})
        password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        obj = {"email":email, "password":password, "access":"write", "status":1}
        res = dbh[coll].insert_one(obj)
    except pymongo.errors.ServerSelectionTimeoutError as err:
        print (err)
    except pymongo.errors.OperationFailure as err:
        print (err)



if __name__ == '__main__':
    main()
