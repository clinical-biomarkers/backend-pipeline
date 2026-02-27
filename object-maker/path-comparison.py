import os,sys
import json
import glob
import datetime
import csvutil
from optparse import OptionParser
import random


def sorted_deep(d):
    
    # If the input is a dictionary, create a new sorted dictionary
    if isinstance(d, dict):
        tmp_dict = {}
        for k, v in sorted(d.items()):
            tmp_dict[k] = sorted_deep(v)
        return tmp_dict
    # If the input is a list, sort its elements recursively
    elif isinstance(d, list):
        tmp_list = []
        for v in d:
            tmp_list.append(sorted_deep(v))
        return tmp_list
    # Otherwise, return the value as is
    else:
        return d


###############################
def main():

    #ver = "2025_12_22"
    ver = "current"
    file_list = glob.glob("jsondb/biomarkerdb/*.json")

    new_file_list = []
    for i in range(1, 1000):
        r = random.choice(file_list)
        if r not in new_file_list:
            new_file_list.append(r)
    new_file_list = ["jsondb/biomarkerdb/AQ7097-1.json"]
    #new_file_list = file_list

    for f_two in new_file_list:
        biomarker_id = f_two.split("/")[-1].split(".")[0]
        f_one = "/data/shared/biomarkerdb/generated/datamodel/merged/%s/merged_json/%s.json" % (ver,biomarker_id) 
        if os.path.isfile(f_one) == False:
            continue
        doc_one = json.load(open(f_one))
        doc_two = json.load(open(f_two))
        condition_id = doc_two["condition"]["id"]
        cmb_list = []
        for obj in doc_two["biomarker_component"]:
            entity_id = obj["assessed_biomarker_entity_id"]
            biomarker = obj["biomarker"]
            cmb = "%s|%s|%s" % (entity_id, condition_id, biomarker)
            cmb_list.append(cmb)    
        print (cmb_list)
        src_list = []
        for obj in doc_two["source_list"]:
            src_list.append("%s|%s" % (obj["source"], obj["biomarker_idx"]))


        for f in ["score","score_info"]:
            if f in doc_one:
                doc_one.pop(f)

        path_dict_one, path_dict_two = {}, {}
        csvutil.parse_doc(doc_one, path_dict_one, "")
        csvutil.parse_doc(doc_two, path_dict_two, "")
        path_list_one = list(path_dict_one.keys())
        path_list_two = list(path_dict_two.keys())
       
        n_one = len(doc_one["citation"])
        n_two = len(doc_two["citation"])
        
        if n_one != n_two:
            print ("flag-1|%s|%s|%s|%s" % (biomarker_id, n_one, n_two, src_list))
        
        for path_one in path_list_one:
            val_one = path_dict_one[path_one]
            if n_one == n_two and path_one not in path_list_two:
                print ("flag-2|%s|%s|%s|%s" % (biomarker_id, path_one, val_one, src_list))
        obj_one = doc_one["crossref"]
        obj_two = doc_two["crossref"]
        #print (json.dumps(obj_one, indent=4))
        #print (json.dumps(obj_two, indent=4))




    return 




if __name__ == '__main__':
    main()
 
