import os,sys
import json
import glob
import datetime
import subprocess
import csvutil




def main():

    ds_dict = json.load(open("misc/datasets.json"))
    for grp in ds_dict:
        for ds in ds_dict[grp]:
            cmd = "python3 make-datasets.py -d %s" % (ds)
            x = subprocess.getoutput(cmd)
            #print (cmd)
        

    return 




if __name__ == '__main__':
    main()
 
