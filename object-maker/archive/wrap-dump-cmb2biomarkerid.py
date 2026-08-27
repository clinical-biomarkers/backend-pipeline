import os
import sys
import json
import glob


###############################
def main():


    file_list = sorted(glob.glob("/data/shared/biomarkerdb/generated/datamodel/merged/current/merged_json/*"))
    n = len(file_list)
    batch_size = int(n/10) if n > 10 else n
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
        cmd = "nohup python3 dump-cmb2biomarkerid.py -s %s -e %s  & " % (o["s"], o["e"])
        os.system(cmd)
        #print (cmd)

    return




if __name__ == '__main__':
    main()

