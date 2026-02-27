import os,sys
import json
import glob
import datetime

import csvutil




def main():

    #modified|clinvar.tsv|presence of rs80356898 mutation in brca1|presense of|mutation|not_specified
   
    map_dict = {}
    in_file = "tmp/output.1.txt"
    with open(in_file, "r") as FR:
        for line in FR:
            if line.find("modified") != -1:
                flag,file_name,orig, v_type,a_type,m_type = line.replace("\n", "").split("|")
                map_dict[orig] = "{%s}{%s}{%s}" % (v_type,a_type,m_type) 


    doc_list = []
    #file_list = glob.glob("/data/shared/biomarkerdb/generated/datamodel/new_data/current/*.json")
    file_list = glob.glob("/data/shared/biomarkerdb/generated/datamodel/existing_data/*.json")
    for in_file in file_list:
        file_name = in_file.split("/")[-1].replace(".json", "")
        obj_list = json.load(open(in_file))
        cluster_dict = {}
        for obj in obj_list:
            biomarker_id = obj["biomarker_id"]
            biomarker_canonical_id = obj["biomarker_canonical_id"]
            n = len(obj["biomarker_component"])
            if "condition" not in obj:
                #print (json.dumps(obj, indent=4))
                #exit()
                continue
            if len(obj["biomarker_component"]) > 1:
                continue
            condition_id = obj["condition"]["id"]
            for o in obj["biomarker_component"]:
                biomarker = o["biomarker"]
                orig = biomarker.lower()
                new = map_dict[orig] if orig in map_dict else orig
                entity_id = o["assessed_biomarker_entity_id"]
                row = [file_name,biomarker_canonical_id,biomarker_id,entity_id,condition_id,biomarker]
                row += [new]
                cmb_old = "%s|%s|%s|%s" % (entity_id, condition_id,orig, biomarker_id)
                cmb_new = "%s|%s|%s" % (entity_id, condition_id,new)
                if cmb_new not in cluster_dict:
                    cluster_dict[cmb_new] = {}
                cluster_dict[cmb_new][cmb_old] = True
        for cmb_new in cluster_dict:
            if cmb_new.find("{expression}") == -1 :
                continue
            n = len(cluster_dict[cmb_new].keys())
            if n > 1:
                source = file_name.split("-")[0]
                doc = {"controlled_vocab":cmb_new, "source":source, "members":[]}
                for k in cluster_dict[cmb_new]:
                    doc["members"].append(k)
                doc_list.append(doc)
            
    print (json.dumps(doc_list, indent=4))

    return 




if __name__ == '__main__':
    main()
 
