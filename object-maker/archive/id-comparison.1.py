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

    # records without condition info
    ignore_list_one = ["BB1482-4", "BB1491-4"]
    # records without entity IDs
    ignore_list_two = ["BD0270-1", "BB1805-1","BB3805-1", "BB1596-1","BB1804-1", "BB3806-1"]

    ignore_list = ignore_list_one + ignore_list_two
    

    #ver = "2025_12_22"
    ver = "current"
    #db_dir_one = "/data/shared/biomarkerdb/generated/datamodel/merged/%s/merged_json/" %(ver)
    db_dir_one = "/data/shared/biomarkerdb/generated/datamodel/merged/%s/merged_json_updated/" %(ver)
    src_dict = csvutil.load_src_dict()
    cmb2biomarkerid = csvutil.load_cmb2biomarkerid()
    flag_dict = {}
    r_dict = {}
    for cmb in cmb2biomarkerid:
        biomarker_id_list = list(cmb2biomarkerid[cmb].keys())
        n = len(biomarker_id_list)
        for biomarker_id in biomarker_id_list:
            if biomarker_id in ignore_list:
                continue
            flag_dict[biomarker_id] = "100"
            if n > 1:
                r_dict[biomarker_id] = True

    file_list = glob.glob(db_dir_one + "*")
    old_pipeline_record_count = len(file_list)
    seen_one = {}
    for in_file in file_list:
        biomarker_id = in_file.split("/")[-1].split(".")[0]
        if biomarker_id in ignore_list:
            continue
        seen_one[biomarker_id] = True
        flag_dict[biomarker_id] = "110" if biomarker_id in flag_dict else "010"

    file_list = glob.glob("logs/make-biomarker.idlist.*.json")
    new_pipeline_record_count = 0
    idx = 0
    merged_count = 0
    seen_two = {}
    for in_file in file_list:
        doc = json.load(open(in_file))
        for idd in doc:
            print (idd)
            new_pipeline_record_count += 1
            id_list = idd.split(";")
            merged_count += len(id_list) - 1
            for biomarker_id in id_list:
                if biomarker_id in flag_dict:
                    flag_dict[biomarker_id] = flag_dict[biomarker_id][:-1] + "1" 
                else:
                    flag_dict[biomarker_id] = "001"
                seen_two[biomarker_id] = True

    exit()

    for biomarker_id in flag_dict:
        src_list = list(src_dict[biomarker_id].keys()) if biomarker_id in src_dict else []
        if flag_dict[biomarker_id] != "111":
            print (flag_dict[biomarker_id], biomarker_id, src_list)

    n11 = len(seen_one.keys())
    n21, n22 = len(seen_two.keys()),  merged_count
    print ("old=%s, new=%s, merged=%s" % (n11, n21, n22))
    
    return 





if __name__ == '__main__':
    main()
 
