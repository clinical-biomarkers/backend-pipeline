import csv
import json
import re
import glob
import datetime
import pytz


def get_mutation_term_list():
    term_list = ["mutation","deletion","fusion","insertion","rearrangement"]
    return term_list


def get_vocab_pattern(entity_id, biomarker, ptrn_dict, e_type_list):

    check_entity_flag = False
    flag, orig, vocab_ptrn = match_pattern(biomarker, ptrn_dict)
    mut_w_flag, mut_w = has_mutation_word(orig)
    if mut_w_flag:
        check_entity_flag = True
        vocab_ptrn = "presence of|not_specified|sequence variation"
    if vocab_ptrn.find("|sequence variation") != -1 and entity_id.find("NCBI:") != -1:
        check_entity_flag = True
    flag_list = ["not_mapped"] if vocab_ptrn == "" else []
    flag_list += ["check_entity"] if check_entity_flag else []
    flag_list += ["check_entity_type"] if e_type_list == [] else []

    return vocab_ptrn, flag_list



def match_pattern(biomarker, ptrn_dict):

    mutation_term_list = get_mutation_term_list()
    w_list = []
    for w in biomarker.lower().split(" "):
        if w.strip() != "":
            w_list.append(w)
                   
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
    

    if vocab_ptrn == "":
        if orig.find("presence of rs") != -1:
            flag, vocab_ptrn = "modified", "presence of|not_specified|sequence variation"
        else:
            tmp_flag = False
            for kw in mutation_term_list:
                if biomarker.lower().find(kw) != -1:
                    tmp_flag = True
            if tmp_flag:
                flag, vocab_ptrn = "modified", "presence of|not_specified|sequence variation"


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





def has_mutation_word(orig):

    typo_dict = {
        "abl1:e255k":"abl1 e255k",
        "abl1:f359v":"abl1 f359v",
        "abl1:t315a":"abl1 t315a",
        "abl1:v299l":"abl1 v299l",
        "abl1:i242t":"abl1 i242t",
        "abl1:t315i":"abl1 t315i",
        "akt1:e17k":"akt1 e17k",
        "erbb2:g776l":"erbb2 g776l",
        "flt3-itd":"flt3 itd",
        "flt3 (d835)":"flt3 d835",
        "nras (q61)":"nras q61",
        "ros1:g2032r":"ros1 g2032r",
        "stk11:d194e":"stk11 d194e",
        "tp53:r248q":"tp53 r248q"
    }

    for w_lc in typo_dict:
        if orig.lower().find(w_lc) != -1:
            orig = orig.lower().replace(w_lc, typo_dict[w_lc])

    #w_list = orig.lower().split(" ")
    w_list = orig.split(" ")
    ret_flag = False
    mut_w_list = []
    for w in w_list:
        if w == "":
            continue
        w_lc = w.lower()
        flag_list = []
        flag_list.append(w_lc[0].isdigit() or w_lc[0] in ["(",")"])
        flag_list.append(w_lc[1:-1].isdigit())
        flag_list.append(w_lc[-1].isdigit() or w_lc[-1] in ["(",")"])
        if flag_list == [False, True, False]:
            ret_flag = True
            if w not in mut_w_list:
                mut_w_list.append(w)
                #print ("flag-1a", mut_w_list)
        flag_list = []
        flag_list.append(w_lc.find("(") != -1 and w_lc.find(")") != -1 and w_lc.find(">") != -1)
        flag_list.append(w_lc.find("(c.") != -1 and w_lc.find(")") != -1 and w_lc.find("del") != -1)
        flag_list.append(w_lc.find("(c.") != -1 and w_lc.find(")") != -1 and w_lc.find("ins") != -1)
        flag_list.append(w_lc.find("(c.") != -1 and w_lc.find(")") != -1 and w_lc.find("dup") != -1)
        if len(w_lc) > 2:
            flag_list.append(w_lc[0:2] == "rs" and w_lc[2:].isdigit())
        if True in flag_list:
            ret_flag = True
            if w not in mut_w_list:
                mut_w_list.append(w)
                #print ("flag-1b", mut_w_list)
        if w.find(":") != -1:
            ptrn = w.split(":")[-1]
            flag_list = []
            flag_list.append(ptrn[0].isdigit())
            flag_list.append(ptrn[1:-1].isdigit())
            flag_list.append(ptrn[-1].isdigit())
            if flag_list == [False, True, False]:
                ret_flag = True
                if ptrn not in mut_w_list:
                    mut_w_list.append(ptrn)
                    #print ("flag-1c", mut_w_list) 



    for w in w_list:
        if w == "":
            continue
        flag_list = []
        flag_list.append(w[0].isdigit())
        flag_list.append(w[1:].isdigit())
        if flag_list == [False, True] and "mutation" in w_list:
            ret_flag = True
            if w not in mut_w_list:
                mut_w_list.append(w)
                #print ("flag-2a", mut_w_list)

        if w.find("(") != -1 and w.find(")") != -1 and w.find(">") != -1:
            ret_flag = True
            if w not in mut_w_list:
                mut_w_list.append(w)
                #print ("flag-2b", mut_w_list)

    if orig.find("::") != -1 or orig.find(":") != -1:
        if orig.lower().find("mutation") != -1:
            ret_flag = True
            for w in w_list:
                if w.find("::") != -1 or w.find(":") != -1:
                    if w not in mut_w_list:
                        mut_w_list.append(w)
                        #print ("flag-3a", mut_w_list)
                if w.find("(") != -1 and w.find(")") != -1 and w.find(">") != -1:
                    if w not in mut_w_list:
                        mut_w_list.append(w)
                        #print ("flag-3b", mut_w_list)           

    #print ("0000", w_list, mut_w_list)

    mut_w = " ".join(mut_w_list)
    #print ("YYY|%s|%s|%s" % (orig, mut_w_list,mut_w))


    return ret_flag, mut_w


