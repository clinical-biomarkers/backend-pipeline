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
    

    count_dict = {}
    file_list = glob.glob("logs/c_initlistcache*.%s.log" % (server))
    for in_file in file_list:
        with open(in_file, "r") as FR:
            for line in FR:
                row = line.strip().split(",")
                cache_id, grp_id, cache_name = row[0], row[3], row[5]
                if cache_name not in count_dict:
                    count_dict[cache_name] = {}
                if grp_id not in count_dict[cache_name]:
                    count_dict[cache_name][grp_id] = 0
                count_dict[cache_name][grp_id] += 1 

    for cache_name in count_dict:
        tmp_list = []
        total = 0
        for grp_id in count_dict[cache_name]:
            n = count_dict[cache_name][grp_id]
            tmp_list.append("%s(%s)" % (grp_id, n))
            total += n
        #print (total, cache_name, ",".join(tmp_list))
        print (total, cache_name)

    return


if __name__ == '__main__':
    main()
