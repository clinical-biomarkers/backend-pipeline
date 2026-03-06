import os,sys
import json
import glob
import datetime
from optparse import OptionParser

import csvutil




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



    file_list = glob.glob(release_dir + "jsondb/biomarkerdb/*.json")
    n = len(file_list)
    batch_size = int(n/5) if n > 5 else n
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
        cmd = "nohup python3 val-comparison.py -s %s -e %s  & " % (o["s"], o["e"])
        os.system(cmd)
        #print (cmd)

 
    return 




if __name__ == '__main__':
    main()
 
