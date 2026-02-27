import os,sys
import json
import glob
import datetime

import csvutil




def main():



    cmb2grpid = csvutil.load_cmb2grpid()
    for cmb in cmb2grpid:
        grp_idx = cmb2grpid[cmb]
        print ("A", grp_idx, cmb)


    file_list = glob.glob("unreviewed/biomarkers_*.tsv")
    seen = {}
    for in_file in file_list:
        source = in_file.split("/")[-1].replace("biomarkers_","").replace(".tsv","")
        #grp_dict = {}
        with open(in_file, "r") as FR:
            f_list, lcount = [], 0
            for line in FR:
                lcount += 1
                row = line[0:-1].split("\t")
                if lcount == 1:
                    f_list = row
                else:
                    biomarker = row[f_list.index("biomarker")]
                    entity_id = row[f_list.index("assessed_biomarker_entity_id")]
                    condition_id = row[f_list.index("condition_id")]
                    grp_idx = row[f_list.index("component_group")]
                    cmb = "%s|%s|%s" % (entity_id,condition_id,biomarker)
                    seen[cmb] = True
                    print ("B", grp_idx, cmb)
    exit()



    vocab_dict = {}
    file_list = glob.glob("unreviewed/biomarkers_*.csv")
    for in_file in file_list:
        with open(in_file, "r") as FR:
            for line in FR:
                row = line[1:-2].strip().split("\",\"")
                if row[0] == "biomarker":
                    continue
                biomarker, vocab = row[0], row[-1]
                vocab_dict[biomarker] = vocab




    map_dict = {}
    in_file = "tmp/biomarker_list_prd.txt"
    with open(in_file, "r") as FR:
        for line in FR:
            biomarker_id, entity_id, condition_id, biomarker = line.strip().split("|")
            ent_list = entity_id.split(";")
            vocab = vocab_dict[biomarker] if biomarker in vocab_dict else "not_mapped"
            flag = len(ent_list) > 1 
            if vocab == "not_mapped":
                x = "xx"
                #print (flag, line.strip())
            else:
                cmb = "%s|%s|%s" % (entity_id, condition_id, vocab)
                if cmb not in map_dict:
                    map_dict[cmb] = {}
                o = [biomarker_id, entity_id, condition_id, biomarker, vocab]
                map_dict[cmb][biomarker_id] = o


    for cmb in map_dict:
        biomarker_id_list = list(map_dict[cmb].keys())
        n = len(biomarker_id_list)
        #if n == 1:
        #    print (biomarker_id_list, cmb)
        if n != 1:
            row = ["biomarker_id","entity_id","condition_id","biomarker","biomarker_controlled_vocab"]
            print ("\n\"%s\"" % ("\",\"".join(row)))
            for biomarker_id in biomarker_id_list:
                row = map_dict[cmb][biomarker_id]
                print ("\"%s\"" % ("\",\"".join(row)))


    return 




if __name__ == '__main__':
    main()
 
