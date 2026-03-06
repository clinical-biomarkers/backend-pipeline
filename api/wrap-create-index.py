import os,sys
import string
import pytz
import datetime
import glob
import json
import subprocess
from lib_update import get_mongodb
from optparse import OptionParser
from cacheutil import get_c_initcache_queries,get_supersearch_init_query, get_pulldown_dict



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
        
    index_dict = json.load(open("conf/indexes.json")) 
    for coll in index_dict:
        for path in index_dict[coll]:
            idx_name = index_dict[coll][path]
            cmd = "python3 create-index.py -s %s -c %s -n %s" % (server, coll, idx_name)
            x = subprocess.getoutput(cmd)
            #print (cmd)
 

    return


if __name__ == '__main__':
    main()
