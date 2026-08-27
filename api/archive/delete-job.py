import os,sys
import string
from optparse import OptionParser
import glob
import json
from bson import json_util
import pymongo
from pymongo import MongoClient
import datetime
import subprocess

__version__="1.0"
__status__ = "Dev"



###############################
def main():


    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-s","--server",action="store",dest="server",help="dev/tst/beta/prd")
    parser.add_option("-i","--jobid",action="store",dest="jobid",help="1/2/3/...")

    (options,args) = parser.parse_args()

    for key in ([options.server, options.jobid]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    server = options.server
    job_id = int(options.jobid)
    coll = "c_job"

    config_obj = json.loads(open("./conf/config.json", "r").read())
    mongo_port = "27017"
    
    host = "mongodb://127.0.0.1:%s" % (mongo_port)
  
    db_name = "glydb_beta" if server == "beta" else "glydb"
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
        q = {"jobid":job_id}
        doc = dbh[coll].find_one(q)
        if doc != None:
            res = dbh[coll].delete_many(q)
        else:
            print ("Job %s is not in c_job" % (job_id))

        job_dir = "/data/shared/glygen/userdata/%s/jobs/%s/" % (server, job_id)
        if os.path.isdir(job_dir):
            cmd = "sudo rm -rf " + job_dir
            x = subprocess.getoutput(cmd)
            #print (cmd)
        else:
             print ("out dir %s does not exist " % (job_dir))
    except pymongo.errors.ServerSelectionTimeoutError as err:
        print (err)
    except pymongo.errors.OperationFailure as err:
        print (err)



if __name__ == '__main__':
    main()
