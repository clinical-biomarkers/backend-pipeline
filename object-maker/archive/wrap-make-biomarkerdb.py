import os,sys
import json
import glob
import datetime

import csvutil




def main():



    cmblist2src, grp2cmblist = csvutil.load_cmblist2src()
    cmb_dict = {}
    file_list = glob.glob("reviewed/biomarkers_*.tsv")
    for in_file in file_list:
        source = in_file.split("/")[-1].replace("biomarkers_","").replace(".tsv","")
        with open(in_file, "r") as FR:
            f_list, lcount = [], 0
            for line in FR:
                lcount += 1
                row = line[1:-2].strip().split("\t")
                if lcount == 1:
                    f_list = row
                else:
                    grp_idx = row[f_list.index("component_group")]
                    grp = "%s|%s" % (source, grp_idx)
                    cmb_list = grp2cmblist[grp]
                    cmb_list_str = json.dumps(cmb_list)
                    cmb_dict[cmb_list_str] = True

    n = len(cmb_dict.keys())
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
        cmd = "nohup python3 make-biomarkerdb.py -s %s -e %s  & " % (o["s"], o["e"])
        os.system(cmd)
        #print (cmd)

 
    return 




if __name__ == '__main__':
    main()
 
