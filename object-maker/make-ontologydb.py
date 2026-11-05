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
    global release_dir

    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)
    src_file = release_dir + "misc/ontology.json"
    jsondb_dir = release_dir + "jsondb/ontologydb/"
    if os.path.isdir(jsondb_dir) == False:
        cmd = "mkdir -p " + jsondb_dir
        x, y = subprocess.getstatusoutput(cmd)

    cmd = "cp %s %s"  % (src_file, jsondb_dir)
    x, y = subprocess.getstatusoutput(cmd)


    cmd = "chmod -R 775 " + jsondb_dir
    x, y = subprocess.getstatusoutput(cmd)



    return







if __name__ == '__main__':
	main()



