import os,sys
import json
import glob
import datetime

import csvutil




def main():


    file_list = glob.glob("/data/shared/biomarkerdb/downloads/ncbi/medline_json/pmid.*.json")
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
        cmd = "nohup python3 make-citedb.py -s %s -e %s  & " % (o["s"], o["e"])
        os.system(cmd)
        #print (cmd)

 
    return 




if __name__ == '__main__':
    main()
 
