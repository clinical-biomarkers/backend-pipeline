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
    (options,args) = parser.parse_args()

    for key in ([options.server]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    server = options.server

    config_file = "conf/config.json"
    config_obj = json.loads(open(config_file, "r").read())

    mongo_port = config_obj["dbinfo"]["port"][server]
    host = "mongodb://127.0.0.1:%s" % (mongo_port)
   
 
    admin_user, admin_pass = config_obj["dbinfo"]["admin"]["user"], config_obj["dbinfo"]["admin"]["password"]
    admin_db = config_obj["dbinfo"]["admin"]["db"]

    db_name_tmp = "tmpdb"
    db_name = "bmkbdb_beta" if server == "beta" else "bmkbdb"
    db_user, db_pass = config_obj["dbinfo"][db_name]["user"], config_obj["dbinfo"][db_name]["password"]

    try:
        client = pymongo.MongoClient(host,
            username=admin_user,
            password=admin_pass,
            authSource=admin_db,
            authMechanism='SCRAM-SHA-1',
            serverSelectionTimeoutMS=10000
        )
        client.server_info()


        for db_nm in [db_name, db_name_tmp]:
            users_info = client[db_nm].command('usersInfo')
            for user in users_info.get('users', []):
                if user["user"] == db_user:
                    client[db_nm].command('dropUser', db_user)
                    break
            role_obj_list = [{'role': 'readWrite', 'db': db_nm}]
            client[db_nm].command('createUser', db_user, pwd=db_pass, roles=role_obj_list)
            print ("added user=%s, db=%s" % (db_user, db_nm))

            
    except pymongo.errors.ServerSelectionTimeoutError as err:
        print (err)
    except pymongo.errors.OperationFailure as err:
        print (err)



if __name__ == '__main__':
    main()

