import os
import sys
import gzip
import json
from optparse import OptionParser
import glob





###############################
def main():

    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog " )
    parser.add_option("-r","--rel",action="store",dest="rel",help="")

    (options,args) = parser.parse_args()
    for file in ([options.rel]):
        if not (file):
            parser.print_help()
            sys.exit(0)

    rel = options.rel
    global release_dir
    

    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)
    file_list = glob.glob(release_dir + "jsondb/biomarkerdb/*.json")

    n = len(file_list)
    batch_size = int(len(file_list)/10) if len(file_list) > 10 else len(file_list)

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
        cmd = "nohup python3 make-pointerdb.py -r %s -s %s -e %s  & " % (rel, o["s"], o["e"])
        os.system(cmd)
        #print (cmd)





if __name__ == '__main__':
    main()

