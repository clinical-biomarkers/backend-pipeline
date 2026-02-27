import csv
import json
import re
import glob
import datetime
import pytz


def match_pattern(w_list, ptrn_dict):

    vocab_ptrn = ""
    orig = " ".join(w_list)
    for label in ptrn_dict:
        for ptrn_list in ptrn_dict[label]:
            if len(w_list) == len(ptrn_list):
                flag_list = []
                for i in range(0, len(ptrn_list)):
                    if ptrn_list[i][0] != "*":
                        ptrn = ptrn_list[i]
                        flag_list.append(True if w_list[i] in ptrn.split("|") else False)
                    else:
                        flag_list.append(True)
                if list(set(flag_list)) == [True]:
                    vocab_ptrn = label
    if vocab_ptrn == "":
        aa_list = list("ARNDCEQGHILKMFPSTWYV".lower())
        mut_flag = False
        for w in w_list:
            if len(w) > 2:
                if w[0] in aa_list and w[-1] in aa_list and w[1:-1].isdigit():
                    mut_flag = True
        if mut_flag == False:
            for w in w_list:
                if w.find("(c.") != -1 and w[-1] == ")":
                    mut_flag = True
        if mut_flag:
            vocab_ptrn = "presence of|not_specified|sequence variation"

    flag = "original" if vocab_ptrn == "" else "modified"
    return flag, orig, vocab_ptrn




def load_sheet(sheet_obj, in_file, field_list, separator):

    seen = {}
    sheet_obj["fields"] = []
    sheet_obj["data"] = []
    field_ind_list = []
    with open(in_file, 'r') as FR:
        csv_grid = csv.reader(FR, delimiter=separator, quotechar='\"')
        row_count = 0
        ncols = 0
        for row in csv_grid:
            if json.dumps(row) in seen:
                continue
            seen[json.dumps(row)] = True
            row_count += 1
            for j in range(0, len(row)):
                row[j] = row[j].replace("\"", "`")
            if row_count == 1:
                ncols = len(row)
                for j in range(0, len(row)):
                    f = row[j].strip()
                    if field_list != [] and f in field_list:
                        field_ind_list.append(j)
                        sheet_obj["fields"].append(f)
                    else:
                        field_ind_list.append(j)
                        sheet_obj["fields"].append(f)
            else:
                #make sure every row has ncols columns
                if len(row) != ncols:
                    continue
                new_row = []
                for j in field_ind_list:
                    new_row.append(row[j].strip())
                sheet_obj["data"].append(new_row)



    return




def load_cmb2grpid(release_dir):

    file_list = []
    ds_dict = json.load(open(release_dir + "misc/datasets.json"))
    for ds in ds_dict["biomarkers"]:
        for file_name in ds_dict["biomarkers"][ds]:
            in_file = "/data/shared/biomarkerdb/downloads/%s/current/%s" % (ds.replace("biomarkers_",""), file_name)
            file_list.append(in_file)


    biomarkerid2index = {}
    grp_idx = 1
    tmp_dict = {}
    for in_file in file_list:
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
                    condition_id = row[f_list.index("condition_id")]
                    biomarker = row[f_list.index("biomarker")]
                    biomarker_id = row[f_list.index("biomarker_id")]
                    if entity_id == "":
                        continue
                    cmb = "%s|%s|%s" % (entity_id,condition_id,biomarker)
                    if biomarker_id not in tmp_dict:
                        tmp_dict[biomarker_id] = {}
                    tmp_dict[biomarker_id][cmb] = True
                    if biomarker_id not in biomarkerid2index:
                        biomarkerid2index[biomarker_id] = grp_idx
                        grp_idx += 1

    cmb2grpid = {}
    for biomarker_id in tmp_dict:
        grp_idx = biomarkerid2index[biomarker_id]
        for cmb in tmp_dict[biomarker_id]:
            if cmb not in cmb2grpid:
                cmb2grpid[cmb] = {}
            cmb2grpid[cmb][biomarker_id] = str(grp_idx)
            #print ("Robel", biomarker_id,cmb,grp_idx)
            

    return cmb2grpid





