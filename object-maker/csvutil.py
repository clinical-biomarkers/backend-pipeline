import os
import csv
import json
import re
import glob
import datetime
import pytz
import hashlib
import random
import requests


def parse_sent(s, phrase_dict,  min_word_count):

    MAX_WORD_COUNT = 6

    if s.strip() == "":
        return
    s = s.lower().replace(",", " ").replace("-", " ").replace(";", " ")
    s = s.replace("(", " ").replace(")", " ").replace("[", " ").replace("]", " ")
    w_list = s.split(" ")
    word_count = len(w_list) + 1
    word_count = MAX_WORD_COUNT if word_count > MAX_WORD_COUNT else word_count
    for wlen in range(0, word_count):
        if wlen > len(w_list):
            continue
        for i in range(0, len(w_list)):
            l = []
            for ww in w_list[i:i+wlen]:
                ww = ww.strip()
                if ww != "":
                    l.append(ww)
            if len(l) >= min_word_count:
                w = " ".join(l)
                if len(w) == 1:
                    continue
                phrase_dict[w] = True
                for prefix in ["doid:", "mondo:", "mim:", "go:", "uberon:"]:
                    if w.find(prefix) == 0:
                        p = w.replace(prefix, "")
                        phrase_dict[p] = True

    return



def write_log_msg(log_file, msg, mode):

    with open(log_file, mode) as FL:
        FL.write("%s\n" % (msg))
    return


def parse_doc(in_obj, path_dict, path):
    

    if type(in_obj) is dict:
        for k in in_obj:
            p = path + "." + k if path != "" else k
            parse_doc(in_obj[k], path_dict, p)
    elif type(in_obj) is list:
        for k in range(0, len(in_obj)):
            p = path + "." + str(k) if path != "" else str(k)
            parse_doc(in_obj[k], path_dict, p)
    elif type(in_obj) is str:
        path_dict[path] = in_obj
    elif type(in_obj) is int:
        path_dict[path] = "0"
    elif type(in_obj) is float:
        path_dict[path] = "0.0"

    return




def load_url_dict(in_file):

    tmp_dict = {}
    df = {}
    load_sheet(df, in_file, [], ",")
    f_list = df["fields"]
    for row in df["data"]:
        xref_key = row[f_list.index("xref_key")]
        xref_lbl = row[f_list.index("xref_lbl")]
        xref_url = row[f_list.index("xref_url")]
        tmp_dict[xref_key] = {"url":xref_url, "lbl":xref_lbl}
 
    return tmp_dict



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

def load_cite_dict(release_dir):

    tmp_dict = {}
    file_list = glob.glob(release_dir + "jsondb/citedb/*.json")
    idx = 0
    for in_file in file_list:
        idx += 1
        doc_list = json.load(open(in_file, "r"))
        for doc in doc_list:
            pmid = doc["pmid"]
            tmp_dict[pmid] = doc
            tmp_dict[pmid].pop("pmid")

    return tmp_dict



def get_cite_obj(pmid):
    in_file_two = "/data/shared/biomarkerdb/downloads/ncbi/medline_json/pmid.%s.json" % (pmid)

    url = "https://pubmed.ncbi.nlm.nih.gov/" + pmid
    ref_obj = {"id": pmid, "type": "PubMed", "url":url}
    ret_obj = {"title": "","journal":"","date":"","authors":"","reference": [ref_obj], "evidence": []}
    if os.path.isfile(in_file_two) == False:
        return ret_obj
   
 
    obj = json.loads(open(in_file_two, "r").read())
    if "AU" not in obj and "IR" in obj:
        obj["AU"] = obj["IR"]
    if "AU" not in obj:
        obj["AU"] = ["author information missing"]
    for tag in ["TI", "DP", "JT", "BTI"]:
        if tag not in obj:
            obj[tag] = ["missing tag=%s" % (tag)]

    row, flag_list = [], []
    if flag_list == []:
        if type(obj["TI"]) is list:
            title = " ".join(obj["TI"]).replace("\"", "`")
            journal = " ".join(obj["JT"]) if "JT" in obj else " ".join(obj["BTI"])
            pubdate = " ".join(obj["DP"])
            authors = ", ".join(obj["AU"])
            row = [title, journal, pubdate, authors]
        else:
            title = obj["TI"].replace("\"", "`")
            journal = obj["JT"] if "JT" in obj else obj["BTI"]
            pubdate = obj["DP"]
            authors = obj["AU"]
            row = [title, journal, pubdate, authors]

    if len(row) == 4:
        ret_obj["title"] = row[0]
        ret_obj["journal"] = row[1]
        ret_obj["date"] = row[2]
        ret_obj["authors"] = row[3]

    return ret_obj





def load_cmblist2src(release_dir):
    
    cmb_dict = {}
    file_list = glob.glob(release_dir + "unreviewed/biomarkers_*.tsv")
    
    for in_file in file_list:
        source = in_file.split("/")[-1].replace("biomarkers_","").replace(".tsv","")
        with open(in_file, "r") as FR:
            f_list, lcount = [], 0
            for line in FR:
                lcount += 1
                row = line[0:-1].split("\t")
                if lcount == 1:
                    f_list = row
                else:
                    biomarker = row[f_list.index("biomarker")]
                    biomarker_controlled_vocab = row[f_list.index("biomarker_controlled_vocab")]
                    entity_id = row[f_list.index("assessed_biomarker_entity_id")]
                    condition_id = row[f_list.index("condition_id")]
                    exposure_agent_id = row[f_list.index("exposure_agent_id")]
                    change_type = row[f_list.index("change_type_vocab")]
                    aspect_type = row[f_list.index("aspect_type_vocab")]
                    mod_type = row[f_list.index("mod_type_vocab")]

                    
                    vocab_parts = biomarker + " [biomarker_term_in_review]"
                    if change_type != "not_specified":
                        vocab_parts = "change_type:%s" % (change_type)
                    if aspect_type != "not_specified":
                        vocab_parts += ",aspect_type:%s" % (aspect_type)
                    if mod_type != "not_specified":
                        vocab_parts += ",mod_type:%s" % (mod_type)

                    grp_idx = ""
                    for k in ["biomarker_index", "component_group"]:
                        grp_idx = row[f_list.index(k)] if k in f_list else grp_idx
                    
                    #if source in ["exposure_agents", "cadsr"]:
                    #    print (entity_id,exposure_agent_id, source, grp_idx)
 
                    if grp_idx == "":
                        continue 
                    grp = "%s|%s" % (source, grp_idx)
                    condition_or_agent_id = condition_id
                    ctype = "condition"
                    if condition_id == "" and exposure_agent_id != "":
                        condition_or_agent_id = exposure_agent_id
                        ctype = "exposure_agent"
                    cmb = "%s|%s|%s|%s" % (entity_id,condition_or_agent_id,ctype,vocab_parts.lower())
                    if grp not in cmb_dict:
                        cmb_dict[grp] = {}
                    cmb_dict[grp][cmb] = True
                    #print (cmb, source)

    cmblist2src, grp2cmblist = {}, {}
    for grp in cmb_dict:
        cmb_list = sorted(list(cmb_dict[grp].keys()))
        cmb_list_str = json.dumps(cmb_list)
        if cmb_list_str not in cmblist2src:
            cmblist2src[cmb_list_str] = {}
        cmblist2src[cmb_list_str][grp] = True
        grp2cmblist[grp] = json.loads(cmb_list_str)

    return cmblist2src, grp2cmblist



def load_entity_names():

    name_dict = {"gene_names":{}, "protein_names":{}}
    file_list = glob.glob("/data/shared/biomarkerdb/downloads/glygen/current/*_protein_*names.csv")
    file_list += glob.glob("/data/shared/biomarkerdb/downloads/glygen/current/*_protein_*names_refseq.csv")
    file_list += glob.glob("/data/shared/biomarkerdb/downloads/glygen/current/*_protein_*names_uniprotkb.csv")
    sheet_info = json.load(open("conf/sheet_info.json"))
    for in_file in file_list:
        sheet_name = "protein_" + in_file.split("_protein_")[1].replace(".csv", "")
        prop_name = "gene_names" if sheet_name.find("genenames") != -1 else "protein_names"
        field_list = sheet_info[sheet_name]["fieldlist"]
        resource = sheet_info[sheet_name]["resource"]
        resource_badge = sheet_info[sheet_name]["badge"]
        data_frame = {}
        load_sheet(data_frame, in_file, [], ",")
        f_list = data_frame["fields"]
        for row in data_frame["data"]:
            canon = row[f_list.index("uniprotkb_canonical_ac")]
            for f in field_list:
                name = row[f_list.index(f)]
                if name.strip() == "":
                    continue
                name_type = "synonym"
                if f in ["recommended_name_full", "gene_symbol_recommended"]:
                    name_type = "recommended"
                xref_key = sheet_info[sheet_name]["xref_key"]
                xref_id = canon.split("-")[0]
                if xref_key == "protein_xref_refseq":
                    xref_id = row[f_list.index("refseq_ac")]
                nm_list = name.split(";")
                for nm in nm_list:
                    nm = nm.strip()
                    if nm != "":
                        name_obj = { "name":nm, "resource":resource_badge,"type":name_type,"id":xref_id}
                        combo_id = "%s|%s|%s|%s" % (canon,name_type,nm,resource)
                        name_dict[prop_name][combo_id] = name_obj

    prt_name_dict = {}
    for combo_id in name_dict["protein_names"]:
        entity_id = "UPKB:" + combo_id.split("-")[0]    
        if entity_id not in prt_name_dict:
            prt_name_dict[entity_id] = []
        prt_name_dict[entity_id].append(name_dict["protein_names"][combo_id])

    canon2gene = {}
    for combo_id in name_dict["gene_names"]:
        if combo_id.find("|recommended|") != -1:
            canon, gene_name = combo_id.split("|")[0],  combo_id.split("|")[2]
            if canon not in canon2gene:
                canon2gene[canon] = {}
            canon2gene[canon][gene_name] = True
           
    gene_name_dict = {}
    for combo_id in name_dict["gene_names"]:
        canon = combo_id.split("|")[0]
        if canon in canon2gene:
            for gene_name in canon2gene[canon]:
                entity_id = "HGNC:" + gene_name
                if entity_id not in gene_name_dict:
                    gene_name_dict[entity_id] = []
                gene_name_dict[entity_id].append(name_dict["gene_names"][combo_id])

       
    return prt_name_dict, gene_name_dict







def load_vocab_dict(release_dir):

    tmp_list = [
        "increased tnni3 level",
        "increased tnnt2 level",
        "increased pct level"
    ]
    vocab_dict = {}
    file_list = glob.glob(release_dir +  "unreviewed/biomarkers_*.tsv")
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
                    condition_id = row[f_list.index("condition_id")]
                    entity_type = row[f_list.index("assessed_entity_type")]
                    biomarker_controlled_vocab = row[f_list.index("biomarker_controlled_vocab")]
                    if biomarker not in vocab_dict:
                        vocab_dict[biomarker] = {}
                    ent_cmb = "%s|%s" % (entity_type.lower(),entity_id)
                    #ent_cmb = entity_id
                    vocab_dict[biomarker][ent_cmb] = biomarker_controlled_vocab

    return vocab_dict



def load_new_biomarkerid_dict(release_dir):

    tmp_dict = {}
    d_list = glob.glob("/data/shared/biomarkerdb/releases/data/v-*/jsondb/idgendb")
    for d in d_list:
        r = d.split("/")[-3].replace("v-","").replace(".","")
        if r.isdigit() == False:
            continue
        if int(r) < 311:
            continue
        file_list = glob.glob(d + "/*.json")
        for in_file in file_list:
            doc_list = json.load(open(in_file))
            for doc in doc_list:
                cmb_list = sorted(doc["cmb_list"])
                cmb_list_str = json.dumps(cmb_list)
                if cmb_list_str not in tmp_dict:
                    tmp_dict[cmb_list_str] = {}
                biomarker_id_list = doc["biomarker_id_list"]
                for biomarker_id in biomarker_id_list:
                    tmp_dict[cmb_list_str][biomarker_id] = True

    return tmp_dict





def load_legacy_biomarkerid_dict(release_dir):

    file_list = []
    ds_dict = json.load(open(release_dir + "misc/datasets.json"))
    for ds in ds_dict["biomarkers"]:
        for file_name in ds_dict["biomarkers"][ds]:
            in_file = "/data/shared/biomarkerdb/downloads/%s/current/%s" % (ds.replace("biomarkers_",""), file_name)
            file_list.append(in_file)


    vocab_dict = load_vocab_dict(release_dir)
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
                    biomarker_id = row[f_list.index("legacy_biomarker_id")] if "legacy_biomarker_id" in f_list else ""
                    entity_id = row[f_list.index("assessed_biomarker_entity_id")]
                    entity_type = row[f_list.index("assessed_entity_type")]
                    condition_id = row[f_list.index("condition_id")]
                    agent_id = row[f_list.index("exposure_agent_id")]
                    biomarker = row[f_list.index("biomarker")]
                    if entity_id == "" or biomarker_id == "":
                        continue
                    vocab = "not-mapped"
                    if biomarker in vocab_dict:
                        ent_cmb = "%s|%s" % (entity_type.lower(),entity_id)
                        #ent_cmb = entity_id
                        if ent_cmb in vocab_dict[biomarker]:
                            vocab = vocab_dict[biomarker][ent_cmb]

                    vocab_lc = vocab.lower()
                    cmb = "%s|%s|%s|%s" % (entity_id,condition_id,agent_id,vocab_lc)
                    if biomarker_id not in tmp_dict:
                        tmp_dict[biomarker_id] = {}
                    tmp_dict[biomarker_id][cmb] = True
                


    final_dict = {}
    for biomarker_id in tmp_dict:
        cmb_list = sorted(list(tmp_dict[biomarker_id].keys()))
        cmb_list_str = json.dumps(cmb_list)
        if cmb_list_str not in final_dict:
            final_dict[cmb_list_str] = {}
        final_dict[cmb_list_str][biomarker_id] = True
    return final_dict



def load_src_dict(release_dir):

    file_list = []
    ds_dict = json.load(open(release_dir + "misc/datasets.json"))
    for ds in ds_dict["biomarkers"]:
        for file_name in ds_dict["biomarkers"][ds]:
            in_file = "/data/shared/biomarkerdb/downloads/%s/current/%s" % (ds.replace("biomarkers_",""), file_name)
            file_list.append(in_file)

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
                    biomarker_id = row[f_list.index("legacy_biomarker_id")] if "legacy_biomarker_id" in f_list else ""
                    if biomarker_id != "":
                        if biomarker_id not in tmp_dict:
                            tmp_dict[biomarker_id] = {}
                        tmp_dict[biomarker_id][file_name] = True
    return tmp_dict




def load_canon2conagent_dict(grp2cmblist, release_dir):

    canon2conagent_dict = {}
    seen_grp = {}
    file_list = glob.glob(release_dir + "unreviewed/biomarkers_*.tsv")
    for in_file in file_list:
        source = in_file.split("/")[-1].replace("biomarkers_","").replace(".tsv","")
        with open(in_file, "r") as FR:
            f_list, lcount = [], 0
            for line in FR:
                lcount += 1
                row = line[0:-1].split("\t")
                if lcount == 1:
                    f_list = row
                else:
                    biomarker = row[f_list.index("biomarker")]
                    biomarker_controlled_vocab = row[f_list.index("biomarker_controlled_vocab")]
                    entity_id = row[f_list.index("assessed_biomarker_entity_id")]
                    condition_id = row[f_list.index("condition_id")]
                    agent_id = row[f_list.index("exposure_agent_id")]
                    grp_idx = ""
                    for k in ["biomarker_index", "component_group"]:
                        grp_idx = row[f_list.index(k)] if k in f_list else grp_idx
                    if grp_idx == "":
                        continue
                    if agent_id == "" and condition_id == "":
                        continue
                    grp = "%s|%s" % (source, grp_idx)
                    if grp not in seen_grp:
                        seen_grp[grp] = True
                        cmb_list = grp2cmblist[grp]
                        cmb_list_canon = []
                        seen_d_id = {}
                        for cmb in cmb_list:
                            ent_id, d_id, ctype, vocab = cmb.split("|")
                            seen_d_id[d_id] = True
                            cmb_list_canon.append("%s|%s" % (ent_id, vocab.lower()))
                        cmb_list_canon = sorted(set(cmb_list_canon))
                        cmb_list_str_canon = json.dumps(cmb_list_canon)
                        canon_id_md5 = hashlib.md5(cmb_list_str_canon.encode('utf-8')).hexdigest()
                        if canon_id_md5 not in canon2conagent_dict:
                            canon2conagent_dict[canon_id_md5] = {}
                        for d_id in seen_d_id:
                            if d_id != "":
                                canon2conagent_dict[canon_id_md5][d_id] = {"cmblist":cmb_list, "grp":grp}
                        
    return canon2conagent_dict


def load_canon_id_dict(current_rel, canon_id_md5_list):

    legacy_release_list = ["3.1.1","3.2.1","3.2.2","3.3.1","3.4.1","3.4.2"]
    
    url = "https://api.biomarkerkb.org//misc/verlist/"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    tmp_list = response.json()
    release_list = legacy_release_list + sorted(tmp_list)
         
    is_bmkb = {}
    seen_canon_id = {}
    canon_id_dict = {}

    r = current_rel.replace(".","")
    if r.isdigit() == False:
        print ("bad current release value=%s" % current_rel)
        exit()
    current_rel_int = int(r)
    
    for rel in release_list:
        r = rel.replace(".","")
        if r.isdigit() == False:
            continue
        if int(r) < 311 and int(r) >= current_rel_int:
            continue
        d = "/data/shared/biomarkerdb/releases/data/v-%s/jsondb/idgendb" % (rel)
 
        file_list = glob.glob(d + "/*.json")
        for in_file in file_list:
            doc_list = json.load(open(in_file))
            for doc in doc_list:
                biomarker_id = doc["record_id"] if "record_id" in doc else doc["biomarker_id"]
                canon_id = biomarker_id.split("-")[0]
                canon_id_md5 = doc["canon_id_md5"]
                canon_id_dict[canon_id_md5] = canon_id
                seen_canon_id[canon_id] = True
                if biomarker_id[:4] == "BMKB":
                    is_bmkb[canon_id_md5] = True
 
    alphabet_list = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    for canon_id_md5 in canon_id_md5_list:
        canon_id = ""
        if canon_id_md5 in canon_id_dict:
            canon_id = canon_id_dict[canon_id_md5]
        if canon_id == "" or canon_id_md5 in is_bmkb:
            tmp_id = ""
            zeros = "0000"
            while True:
                c_one = random.choice(alphabet_list)
                c_two = random.choice(alphabet_list)
                rand_int = random.randint(1, 9999)
                padding = zeros[:4-len(str(rand_int))]
                tmp_id = "%s%s%s%s" % (c_one, c_two,padding, rand_int)
                if tmp_id not in seen_canon_id:
                    break
            canon_id_dict[canon_id_md5] = tmp_id
            #print ("A|%s|%s" % (canon_id_md5,canon_id))
        #else:
        #    print ("B|%s|%s" % (canon_id_md5,canon_id))

    return canon_id_dict


def load_biomarker_orig(rel):

    term_dict = {}
    file_list = glob.glob("/data/shared/biomarkerdb/releases/data/v-%s/reviewed/biomarkers_*.tsv" % (rel))
    for in_file in file_list:
        with open(in_file, "r") as FR:
            f_list, lcount = [], 0
            for line in FR:
                lcount += 1
                row = line[0:-1].split("\t")
                if lcount == 1:
                    f_list = row
                else:
                    biomarker_id = row[f_list.index("biomarker_id")]
                    biomarker = row[f_list.index("biomarker")]
                    term_dict[biomarker_id] = biomarker

    return term_dict


