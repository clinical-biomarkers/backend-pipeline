#!/usr/bin/python
import os,sys
import string
import csv
import json
import glob
import csvutil
from optparse import OptionParser
import subprocess


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
    global release_dir
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)


    # clean out_dir
    out_dir = release_dir + "jsondb/batchdb/"
    if os.path.isdir(out_dir):
        cmd = "rm -rf %s/*" % (out_dir)
        x = subprocess.getoutput(cmd)



    file_list = glob.glob(release_dir + "jsondb/jumbodb/entdb/*.json")
    n = len(file_list)
    range_list = csvutil.get_range_list(n)

    for o in range_list:
        cmd = "nohup python3  make-batchdb.py -r %s -s %s -e %s  & " % (rel, o["s"], o["e"])
        os.system(cmd)
        #print (cmd)

    return




if __name__ == '__main__':
    main()


