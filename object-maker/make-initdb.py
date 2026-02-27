import os,sys
import string
import subprocess
from optparse import OptionParser
import glob
import json
import requests
import csvutil
import datetime
import pytz



__version__="1.0"
__status__ = "Dev"


def sort_release_list(tmp_list, reversed_flag):

    factor_list = [100000000, 1000, 1]
    rel_dict = {}
    for rel in tmp_list:
        parts = rel.split(".")
        ordr = 0
        for i in range(0,len(parts)):
            ordr += factor_list[i]*int(parts[i])
        rel_dict[ordr] = rel
    
    release_list = []

    for ordr in sorted(rel_dict, reverse=reversed_flag):
        release_list.append(rel_dict[ordr])


    seen = {}
    filtered_release_list = []
    for r in release_list:
        rr = r.split(".")[0] + "." + r.split(".")[1]
        if rr not in seen:
            seen[rr] = True
            filtered_release_list.append(r)

    return filtered_release_list




def main():
        
    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-r","--rel",action="store",dest="rel",help="")
    (options,args) = parser.parse_args()
    for key in ([ options.rel]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    rel = options.rel


    global jsondb_dir

    START_TS = datetime.datetime.now(pytz.timezone('US/Eastern'))

    jsondb_dir = "jsondb/"
    in_file = "conf/init.json"
    out_json = json.loads(open(in_file, "r").read())
    out_json["dataversion"] = rel
    
    release_list = [rel]
    out_json["versionlist"] = release_list

    if os.path.isdir(jsondb_dir + "/initdb") == False:
        cmd = "mkdir " + jsondb_dir + "/initdb"
        x, y = subprocess.getstatusoutput(cmd)


    out_file = jsondb_dir + "/initdb/init.json"
    with open(out_file, "w") as FW:
        FW.write("%s\n" % (json.dumps(out_json, indent=4)))

    cmd = "chmod -R 775 " + jsondb_dir + "/jsondb/initdb"
    x, y = subprocess.getstatusoutput(cmd)



    return







if __name__ == '__main__':
	main()



