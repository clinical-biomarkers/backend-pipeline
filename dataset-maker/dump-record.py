import os,sys
import json
import glob
import datetime

import csvutil




def main():

    id_list = ["AN4973-1", "AN5009-4"]
    #id_list = ["AN6400-1"]
    #file_list = glob.glob("/data/shared/biomarkerdb/generated/datamodel/new_data/current/*.json")
    file_list = glob.glob("/data/shared/biomarkerdb/generated/datamodel/existing_data/*.json")
    for in_file in file_list:
        file_name = in_file.split("/")[-1].replace(".json", "")
        obj_list = json.load(open(in_file))
        cluster_dict = {}
        for obj in obj_list:
            biomarker_id = obj["biomarker_id"]
            if biomarker_id not in id_list:
                continue
            n = len(obj["biomarker_component"])
            print (json.dumps(obj, indent=4))

            
            


    return 




if __name__ == '__main__':
    main()
 
