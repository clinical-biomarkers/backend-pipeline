import sys,os
import json
import string
import csv
import traceback
import requests
from optparse import OptionParser
import pymongo
from pymongo import MongoClient


def main():

    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-s","--server",action="store",dest="server",help="dev/tst/beta/prd")
    parser.add_option("-a","--apigrp",action="store",dest="apigrp",help="glycan_list/protein_list")
    parser.add_option("-i","--cacheid",action="store",dest="cacheid",help="")

    (options,args) = parser.parse_args()
    for key in ([options.server, options.apigrp, options.cacheid]):
        if not (key):
            parser.print_help()
            sys.exit(0)
                                         
    server = options.server
    api_grp = options.apigrp
    cache_id = options.cacheid

    config_obj = json.loads(open("./conf/config.json", "r").read())
    base_url = config_obj["base_url"][server]

    try:
        url = base_url + "/%s/list/" % (api_grp)
        req_obj = {"id":cache_id}
        res = requests.post(url, json=req_obj, allow_redirects=True)
        res_obj = json.loads(res.content)
        #print (json.dumps(res_obj, indent=4))
        print (json.dumps(res_obj["cache_info"], indent=4))
        #print (json.dumps(res_obj["pagination"], indent=4))

    except pymongo.errors.ServerSelectionTimeoutError as err:
        print (err)
    except pymongo.errors.OperationFailure as err:
        print (err)





if __name__ == '__main__':
    main()





