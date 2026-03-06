import os,sys
import string
import pytz
import datetime
import glob
import json
import subprocess
from lib_update import get_mongodb
from optparse import OptionParser
from cacheutil import get_c_initlistcache_queries



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

    #xxxx

    db_name = "bmkbdb_beta" if server == "beta" else "bmkbdb"
    config_obj = json.loads(open("./conf/config.json", "r").read())
    mongo_port = config_obj["dbinfo"]["port"][server]
    host_ip = "127.0.0.1"

    db_obj = config_obj["dbinfo"][db_name]
    db_name, db_user, db_pass =  db_obj["db"], db_obj["user"], db_obj["password"]

    config_obj = json.load(open("bmkb/conf/config.json"))
    config_obj["db_info"] = {"user":db_user, "password":db_pass, "host_ip":host_ip, "db_name":db_name,"port":mongo_port}
    dbh, error_obj = get_mongodb(config_obj["db_info"])
    if error_obj != {}:
        print (error_obj)
        exit()



    query_doc = get_c_initlistcache_queries(dbh)
    for record_type in query_doc:
        for cache_name in query_doc[record_type]:
            cmd = "python3 update-initlistcache.py -s %s -n %s" % (server, cache_name)
            x = subprocess.getoutput(cmd)
            #print (cmd)

 

    return


if __name__ == '__main__':
    main()
