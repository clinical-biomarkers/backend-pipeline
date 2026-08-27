#!/usr/bin/python
import os,sys
import string
import csv
import json
import glob
import csvutil
from optparse import OptionParser



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





    pattern_dict = {"biomarker":"*"}

    file_obj_list = []
    for record_type in sorted(list(pattern_dict.keys())):
        glob_str = release_dir + "jsondb/%sdb/%s.json" % (record_type, pattern_dict[record_type])
        file_list = glob.glob(glob_str)
        for json_file in sorted(file_list):
            file_obj_list.append({"file":json_file, "record_type":record_type})

    n = len(file_obj_list)
    batch_size = int(len(file_obj_list)/5) if len(file_obj_list) > 5 else len(file_obj_list)

    range_list = []
    for i in range(0, 12):
        s = i*batch_size + 1
        e = s + batch_size
        if e >= n:
            e = n
            range_list.append({"s":s, "e":e})
            break
        range_list.append({"s":s, "e":e})

    for o in range_list:
        cmd = "nohup python3  make-indexdb.py -r %s -s %s -e %s  & " % (rel, o["s"], o["e"])
        os.system(cmd)
        #print (cmd)

    return




if __name__ == '__main__':
    main()


