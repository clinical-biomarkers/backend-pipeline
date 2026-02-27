import os,sys
import json
import glob
import datetime
import subprocess
import csvutil
from optparse import OptionParser




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

    ds_dict = json.load(open(release_dir + "misc/datasets.json"))
    for grp in ds_dict:
        for ds in ds_dict[grp]:
            cmd = "python3 make-datasets.py -r %s -d %s" % (rel, ds)
            #x = subprocess.getoutput(cmd)
            print (cmd)
        

    return 




if __name__ == '__main__':
    main()
 
