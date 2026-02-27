import os,sys
import json
import glob
import datetime
import csvutil
from optparse import OptionParser

def load_vocab_dict():

    vocab_dict = {}
    file_list = glob.glob("reviewed/biomarkers_*.tsv")
    for in_file in file_list:
        with open(in_file, "r") as FR:
            f_list, lcount = [], 0
            for line in FR:
                lcount += 1
                row = line[0:-1].split("\t")
                if lcount == 1:
                    f_list = row
                else:
                    entity_id = row[f_list.index("assessed_biomarker_entity_id")]
                    biomarker = row[f_list.index("biomarker")]
                    biomarker_controlled_vocab = row[f_list.index("biomarker_controlled_vocab")]
                    if biomarker not in vocab_dict:
                        vocab_dict[biomarker] = {}
                    vocab_dict[biomarker][entity_id] = biomarker_controlled_vocab

    return vocab_dict



def load_cmb2biomarkerid(file_list):

    vocab_dict = load_vocab_dict()
    tmp_dict = {}
    for in_file in file_list:
        print (in_file)
        with open(in_file, "r") as FR:
            file_name = in_file.split("/")[-1]
            lcount = 0
            f_list = []
            for line in FR:
                lcount += 1
                row = line.replace("\n", "").replace("\"", "\'").split("\t")
                if lcount == 1:
                    f_list = row
                else:
                    biomarker_id = row[f_list.index("biomarker_id")]
                    entity_id = row[f_list.index("assessed_biomarker_entity_id")]
                    entity_type = row[f_list.index("assessed_entity_type")]
                    condition_id = row[f_list.index("condition_id")]
                    agent_id = row[f_list.index("exposure_agent_id")]
                    biomarker = row[f_list.index("biomarker")]
                    biomarker_id = row[f_list.index("biomarker_id")]
                    if entity_id == "":
                        continue
                    vocab = "not_mapped"
                    if biomarker in vocab_dict:
                        if entity_id in vocab_dict[biomarker]:
                            vocab = vocab_dict[biomarker][entity_id]
                    cmb = "%s|%s|%s" % (entity_id,condition_id,vocab)
                    if biomarker_id not in tmp_dict:
                        tmp_dict[biomarker_id] = {}
                    tmp_dict[biomarker_id][cmb] = True

    cmb2biomarkerid = {}
    for biomarker_id in tmp_dict:
        cmb_list = sorted(list(tmp_dict[biomarker_id].keys()))
        cmb_list_str = json.dumps(cmb_list)
        if cmb_list_str not in cmb2biomarkerid:
            cmb2biomarkerid[cmb_list_str] = {}
        cmb2biomarkerid[cmb_list_str][biomarker_id] = True
    return cmb2biomarkerid




###############################
def main():

    file_list = []
    ds_dict = json.load(open("misc/datasets.json"))
    for ds in ds_dict["biomarkers"]:
        for file_name in ds_dict["biomarkers"][ds]:
            in_file = "downloads/%s/current/%s" % (ds.replace("biomarkers_",""), file_name)
            file_list.append(in_file)

    cmb2biomarkerid = load_cmb2biomarkerid(file_list)
    exit()
    

    return 




if __name__ == '__main__':
    main()
 
