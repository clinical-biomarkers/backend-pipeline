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
    parser.add_option("-c","--coll",action="store",dest="coll",help="")
    (options,args) = parser.parse_args()

    for key in ([options.server, options.dataversion]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    server = options.server
    ver = options.dataversion
    coll_list = []
    if options.coll != None:
        coll_list.append(options.coll)

    jsondb_dir = "/data/shared/biomarkerdb/releases/data/v-%s/jsondb/" % (ver)
    config_obj = json.loads(open("./conf/config.json", "r").read())
    mongo_port = config_obj["dbinfo"]["port"][server]
    host = "mongodb://127.0.0.1:%s" % (mongo_port)
  

    db_name = "bmkbdb_beta" if server == "beta" else "bmkbdb"
    db_obj = config_obj["dbinfo"][db_name]
    db_name, db_user, db_pass =  db_obj["db"], db_obj["user"], db_obj["password"]

    if coll_list == []:
        for db in config_obj["downloads"]["jsondb"]:
            coll = "c_" + db[:-2]
            if coll in ["c_event", "c_video", "c_outreach"]:
                continue
            coll_list.append(coll)


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
        #print (dbh.list_collection_names())
        #exit()
        for coll in coll_list:
            db = coll[2:] + "db"
            file_list = glob.glob(jsondb_dir + db + "/*.json")
            n_one = len(file_list)
            if coll in ["c_index","c_biomarker","c_list","c_idtrack"]:
                n_one = 0
                for in_file in file_list:
                    if coll == "c_index":
                        for obj in json.load(open(in_file)):
                            n_one += len(obj)
                    else:
                        n_one += len(json.load(open(in_file)))
            n_two = len(list(dbh[coll].find({},{"_id":1})))
            #n_two = dbh[coll].count_documents({})
            print (n_one == n_two, coll, "in_file_sys=%s" %(n_one), "in_mongodb=%s" %(n_two))
    except pymongo.errors.ServerSelectionTimeoutError as err:
        print (err)
    except pymongo.errors.OperationFailure as err:
        print (err)



if __name__ == '__main__':
    main()
