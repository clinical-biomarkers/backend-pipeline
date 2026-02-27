import os,sys
import json
import glob
import datetime
import csvutil
from optparse import OptionParser
import random
import orjson




###############################
def main():


    seen = {}
    in_file = "JUNK4"
    with open(in_file, "r") as FR:
        for line in FR:
            flag, biomarker_id = line.split(" ")[0], line.split(" ")[1]
            if flag == "110":
                seen[biomarker_id] = True
       
    cmb2biomarkerid = csvutil.load_cmb2biomarkerid()
    for cmb_list_str in cmb2biomarkerid:
        biomarker_id_list = sorted(list(cmb2biomarkerid[cmb_list_str].keys()))
        for biomarker_id in biomarker_id_list:
            if biomarker_id in seen:
                cmb_list = json.loads(cmb_list_str)
                print (len(cmb_list), biomarker_id, cmb_list_str)
        
        
 
    return 





if __name__ == '__main__':
    main()
 
