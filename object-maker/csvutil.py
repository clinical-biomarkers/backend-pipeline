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
                    c_vocab = row[f_list.index("biomarker_controlled_vocab")].lower()
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
                    
                    if grp_idx == "":
                        continue 
                    grp = "%s|%s" % (source, grp_idx)
                    condition_or_agent_id = condition_id
                    ctype = "condition"
                    if condition_id == "" and exposure_agent_id != "":
                        condition_or_agent_id = exposure_agent_id
                        ctype = "exposure_agent"
                    
                    if c_vocab.find("presence of bmkb") != -1 or c_vocab.find("presence of bmkb") != -1:
                        mut_id = c_vocab.split(" ")[2].replace("bmkb_ii::","bmkb:").replace("bmkb_i::","bmkb:")
                        entity_id += "@%s" % (mut_id)

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

def load_canon2geneid():

    tmp_dict = {}
    in_file = "/data/shared/biomarkerdb/downloads/glygen/current/human_protein_xref_geneid.csv"
    data_frame = {}
    load_sheet(data_frame, in_file, [], ",")
    f_list = data_frame["fields"]
    for row in data_frame["data"]:
        canon = row[f_list.index("uniprotkb_canonical_ac")]
        gene_id = row[f_list.index("xref_id")]
        if canon not in tmp_dict:
            tmp_dict[canon] = {}
        tmp_dict[canon][gene_id] = True

    return tmp_dict


def load_upkb2geneid():

    tmp_dict = {}
    in_file = "/data/shared/biomarkerdb/downloads/glygen/current/human_protein_xref_geneid.csv"
    data_frame = {}
    load_sheet(data_frame, in_file, [], ",")
    f_list = data_frame["fields"]
    for row in data_frame["data"]:
        upkb = "UPKB:" + row[f_list.index("uniprotkb_canonical_ac")].split("-")[0]
        gene_id = "NCBI:" + row[f_list.index("xref_id")]
        if upkb not in tmp_dict:
            tmp_dict[upkb] = {}
        tmp_dict[upkb][gene_id] = True

    return tmp_dict


def load_refid2hgncid():

    canon2geneid = load_canon2geneid()

    tmp_dict = {}
    hgnc2uniprotac = {}
    in_file = "/data/shared/biomarkerdb/downloads/glygen/current/human_protein_xref_hgnc.csv"
    data_frame = {}
    load_sheet(data_frame, in_file, [], ",")
    f_list = data_frame["fields"]
    for row in data_frame["data"]:
        canon = row[f_list.index("uniprotkb_canonical_ac")]
        ref_id = "UPKB:" + canon.split("-")[0]
        hgnc_id = row[f_list.index("xref_id")]
        if ref_id not in tmp_dict:
            tmp_dict[ref_id] = {}
        tmp_dict[ref_id][hgnc_id] = True
        
        x = "HGNC:" + hgnc_id
        if x not in hgnc2uniprotac:
            hgnc2uniprotac[x] = {}
        hgnc2uniprotac[x][ref_id] = True


    in_file = "/data/shared/biomarkerdb/downloads/ncbi/gene_info/Homo_sapiens.gene_info"
    with open(in_file, "r") as FR:
        f_list, lcount = [], 0
        for line in FR:
            lcount += 1
            row = line[0:-1].split("\t")
            if lcount == 1:
                f_list = row
            else:
                gene_id =  row[f_list.index("GeneID")]
                db_xrefs = row[f_list.index("dbXrefs")]
                ref_id = "NCBI:" + gene_id
                for xref in db_xrefs.split("|"):
                    if xref.find("HGNC:HGNC:") != -1:
                        hgnc_id = xref.split(":")[-1]
                        if ref_id not in tmp_dict:
                            tmp_dict[ref_id] = {}
                        tmp_dict[ref_id][hgnc_id] = True

    return tmp_dict, hgnc2uniprotac


def load_entity_names():

    name_dict = {"gene_names":{}, "protein_names":{}, "glycan_names":{}}

    canon2geneid = load_canon2geneid()
    
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

    prop_name = "glycan_names"
    in_file = "/data/shared/biomarkerdb/downloads/bgsl/current/bgsl.tsv"
    with open(in_file, "r") as FR:
        f_list, lcount = [], 0
        for line in FR:
            lcount += 1
            row = line[0:-1].split("\t")
            if lcount == 1:
                f_list = row
            else:
                bgsl_id = row[f_list.index("bgsl_id")].split(":")[-1]
                term = row[f_list.index("term")]
                abbreviations = row[f_list.index("abbreviations")]
                exact_synonyms = row[f_list.index("exact_synonyms")]
                xref_id = bgsl_id
                name_type = "synonym"
                resource, resource_badge = "bgsl","bGSL"
                nm_list = abbreviations.split(";") if abbreviations != "" else []
                nm_list += exact_synonyms.split(";") if exact_synonyms != "" else []
                for nm in list(set(nm_list)):
                    combo_id = "%s|%s|%s|%s" % (bgsl_id,name_type,nm,resource)
                    name_obj = { "name":nm, "resource":resource_badge,"type":name_type,"id":xref_id}
                    name_dict[prop_name][combo_id] = name_obj
                if term != "":
                    name_type = "recommended"
                    combo_id = "%s|%s|%s|%s" % (bgsl_id,name_type,term,resource)
                    name_obj = { "name":term, "resource":resource_badge,"type":name_type,"id":xref_id}
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
        gene_id_list = list(canon2geneid[canon].keys()) if canon in canon2geneid else []
        for gene_id in gene_id_list:
            entity_id = "NCBI:" + gene_id
            if entity_id not in gene_name_dict:
                gene_name_dict[entity_id] = []
            gene_name_dict[entity_id].append(name_dict["gene_names"][combo_id])



    #entity_id = "NCBI:3082"
    #print (json.dumps(gene_name_dict[entity_id], indent=4))

    in_file = "/data/shared/biomarkerdb/downloads/ncbi/gene_info/Homo_sapiens.gene_info"
    with open(in_file, "r") as FR:
        f_list, lcount = [], 0
        for line in FR:
            lcount += 1
            row = line[0:-1].split("\t")
            if lcount == 1:
                f_list = row
            else:
                gene_id =  row[f_list.index("GeneID")]
                entity_id = "NCBI:" + gene_id
                
                rec_name = row[f_list.index("Symbol")]
                synonyms = row[f_list.index("Symbol")]
                if entity_id not in gene_name_dict:
                    gene_name_dict[entity_id] = []
                    o = {"name":rec_name, "resource":"RefSeq", "type":"recommended", "id":entity_id}
                    gene_name_dict[entity_id].append(o)
                    for nm in row[f_list.index("Symbol")].split("|"):
                        o = {"name":nm, "resource":"RefSeq", "type":"synonym", "id":entity_id} 
                        gene_name_dict[entity_id].append(o)
               

        tmp_obj_list = [
            {"entity_id":"NCBI:64012", "rec_name":"Rad50", "synonyms":["Rad50l"]},
            {"entity_id":"NCBI:17062", "rec_name":"Metrn", "synonyms":["1810006K14Rik","hmetrn","ymetrn"]},
            {"entity_id":"NCBI:581485", "rec_name":"LOC581485", "synonyms":[]},
            {"entity_id":"NCBI:59508", "rec_name":"LOC59508", "synonyms":[]},
        ]
        for o in tmp_obj_list:
            entity_id,rec_name, synonyms = o["entity_id"], o["rec_name"], o["synonyms"]
            gene_name_dict[entity_id] = []
            gene_name_dict[entity_id].append({"name":rec_name,"resource":"RefSeq","type":"recommended","id":entity_id})
            for nm in synonyms:
                gene_name_dict[entity_id].append({"name":nm, "resource":"RefSeq", "type":"synonym", "id":entity_id})
    
    glycan_name_dict = {}
    for combo_id in name_dict["glycan_names"]:
        bgsl_id = combo_id.split("|")[0]
        entity_id = "bGSL:" + bgsl_id
        if entity_id not in glycan_name_dict:
            glycan_name_dict[entity_id] = []
        glycan_name_dict[entity_id].append(name_dict["glycan_names"][combo_id])

       
    return prt_name_dict, gene_name_dict, glycan_name_dict


def get_unmapped_rsid_list(release_dir):

    file_list = glob.glob(release_dir + "unreviewed/biomarkers_*.tsv")
    seen_rsid = {}
    for in_file in file_list:
        file_name = in_file.split("/")[-1]
        source = in_file.split("/")[-1].replace("biomarkers_","").replace(".tsv","")
        with open(in_file, "r") as FR:
            f_list, lcount = [], 0
            for line in FR:
                lcount += 1
                row = line[0:-1].split("\t")
                if lcount == 1:
                    f_list = row
                else:
                    ent_id = row[f_list.index("assessed_biomarker_entity_id")]
                    ent_type = row[f_list.index("assessed_entity_type")]
                    c_vocab = row[f_list.index("biomarker_controlled_vocab")]
                    ref_id_list = []
                    ref_id_list = [ent_id] if ent_type == "gene" else ref_id_list
                    ref_id_list = [ent_id] if ent_type == "protein" else ref_id_list
                    et_list = ["metabolite","glycan","cell","amino acid","mRNA","other", "RNA", "miRNA","image"]
                    et_list += ["protein complex","lipoprotein", "chemical element", "peptide", "lipid", "DNA"]
                    ref_id_list = [ent_id] if ent_type in et_list else ref_id_list
                    if ent_type == "gene" and ent_id.find("dbSNP:") != -1:
                        c_vocab_id = c_vocab.split("/")[-1]
                        ref_id_list = [] if c_vocab_id.split(":")[1] == "" else [c_vocab_id]
                        if ref_id_list == [] and c_vocab.find("sequence variation in gene") != -1:
                            seen_rsid[ent_id] = True
    return seen_rsid



def get_range_list(n):
    batch_size = int(n/10) if n > 10 else n
    range_list = []
    for i in range(0, 12):
        s = i*batch_size + 1
        e = s + batch_size
        ss = s if i == 0 else s + 1
        if e >= n:
            e = n
            range_list.append({"s":ss, "e":e})
            break
        range_list.append({"s":ss, "e":e})
    return range_list





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

def load_origid2entid(current_rel):

    legacy_release_list = ["3.1.1","3.2.1","3.2.2","3.3.1","3.4.1","3.4.2"]
    url = "https://api.biomarkerkb.org//misc/verlist/"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    tmp_list = response.json()
    release_list = legacy_release_list + sorted(tmp_list)

    tmp_dict = {}
    for rel in release_list:
        if rel == current_rel:
            continue
        r = rel.replace(".","")
        current_r = current_rel.replace(".","")
        if r.isdigit() == False or current_r.isdigit() == False:
            continue
        if int(r) < 311 or int(r) >= int(current_r):
            continue

        d = "/data/shared/biomarkerdb/releases/data/v-%s/jsondb/entdb" % (rel)
        file_list = glob.glob(d + "/*.json")
        for in_file in file_list:
            doc_list = json.load(open(in_file))
            for doc in doc_list:
                if "orig_id" in doc:
                    tmp_dict[doc["orig_id"]] = doc["entity_id"]
    #exit()
    return tmp_dict






def check_biomarker_input_files(release_dir):

    error_list = []
    required_f_list = ["biomarker_index", "component_index", "entity_index"]
    required_f_list += ["assessed_biomarker_entity_id", "assessed_entity_type"]
    required_f_list += ["change_type_vocab", "aspect_type_vocab", "mod_type_vocab"]
    
    file_list = []
    ds_dict = json.load(open(release_dir + "misc/datasets.json"))
    for ds in ds_dict["biomarkers"]:
        for file_name in ds_dict["biomarkers"][ds]:
            in_file = "/data/shared/biomarkerdb/downloads/%s/current/%s" % (ds.replace("biomarkers_",""), file_name)
            file_list.append(in_file)
    for in_file in file_list:
        with open(in_file, "r") as FR:
            file_name = in_file.split("/")[-1]
            lcount = 0
            f_list = []
            for line in FR:
                row = line.replace("\n", "").replace("\"", "\'").split("\t")
                f_list = row
                for f in required_f_list:
                    if f not in f_list:
                        error_list.append("field=%s missing in file=%s" % (f, file_name))
                break
    return error_list





def load_legacy_biomarkerid_dict(release_dir):

    file_list = []
    ds_dict = json.load(open(release_dir + "misc/datasets.json"))
    for ds in ds_dict["biomarkers"]:
        for file_name in ds_dict["biomarkers"][ds]:
            in_file = "/data/shared/biomarkerdb/downloads/%s/current/%s" % (ds.replace("biomarkers_",""), file_name)
            file_list.append(in_file)


    orig_dict = {}
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
                    exposure_agent_id = row[f_list.index("exposure_agent_id")]
                    biomarker = row[f_list.index("biomarker")]
                    change_type = row[f_list.index("change_type_vocab")]
                    aspect_type = row[f_list.index("aspect_type_vocab")]
                    mod_type = row[f_list.index("mod_type_vocab")]
                    c_vocab = ""
                    if "biomarker_controlled_vocab" in f_list:
                        c_vocab = row[f_list.index("biomarker_controlled_vocab")].lower().replace("presense","presence")
                    if entity_id == "" or biomarker_id == "":
                        continue
                  
                    if biomarker_id not in orig_dict:
                        orig_dict[biomarker_id] = {}
                    orig_dict[biomarker_id][biomarker] = True
                          
                    vocab_parts = biomarker + " [biomarker_term_in_review]"
                    if change_type != "not_specified":
                        vocab_parts = "change_type:%s" % (change_type)
                    if aspect_type != "not_specified":
                        vocab_parts += ",aspect_type:%s" % (aspect_type)
                    if mod_type != "not_specified":
                        vocab_parts += ",mod_type:%s" % (mod_type)

                    condition_or_agent_id = condition_id
                    ctype = "condition"
                    if condition_id == "" and exposure_agent_id != "":
                        condition_or_agent_id = exposure_agent_id
                        ctype = "exposure_agent"
                   
                    if c_vocab.find("presence of bmkb") != -1 or c_vocab.find("presence of bmkb") != -1:
                        mut_id = c_vocab.split(" ")[2].replace("bmkb_ii::","bmkb:").replace("bmkb_i::","bmkb:")
                        entity_id += "@%s" % (mut_id)
 
                    cmb = "%s|%s|%s|%s" % (entity_id,condition_or_agent_id,ctype,vocab_parts.lower())
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
    return final_dict, orig_dict




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
    canonid2maxindex = {}

    r = current_rel.replace(".","")
    if r.isdigit() == False:
        print ("bad current release value=%s" % current_rel)
        exit()
    current_rel_int = int(r)

    cmblist2biomarkerid = {}
    for rel in release_list:
        r = rel.replace(".","")
        if r.isdigit() == False:
            continue
        if int(r) < 311 or int(r) >= current_rel_int:
            continue
        d = "/data/shared/biomarkerdb/releases/data/v-%s/jsondb/idgendb" % (rel)
        file_list = glob.glob(d + "/*.json")
        for in_file in file_list:
            doc_list = json.load(open(in_file))
            for doc in doc_list:
                biomarker_id = doc["record_id"] if "record_id" in doc else doc["biomarker_id"]
                
                cmb_list_str = json.dumps(doc["cmb_list"])
                cmblist2biomarkerid[cmb_list_str] = biomarker_id
                
                canon_id = biomarker_id.split("-")[0]
                canon_id_md5 = doc["canon_id_md5"]
                canon_id_dict[canon_id_md5] = canon_id
                seen_canon_id[canon_id] = True
                if biomarker_id[:4] == "BMKB":
                    is_bmkb[canon_id_md5] = True

                if biomarker_id != "":
                    biomarker_id_index = int(biomarker_id.split("-")[-1])
                    if canon_id not in canonid2maxindex:
                        canonid2maxindex[canon_id] = 0
                    if biomarker_id_index > canonid2maxindex[canon_id]:
                        canonid2maxindex[canon_id] = biomarker_id_index

 
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

    return canon_id_dict, canonid2maxindex, cmblist2biomarkerid



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





def get_new_comp_section(in_comp_obj_list):

    tmp_dict = {}
    for obj in in_comp_obj_list:
        component_index = obj["component_index"]
        entity_index = obj["entity_index"]
        if component_index not in tmp_dict:
            tmp_dict[component_index] = {}
        tmp_dict[component_index][entity_index] = obj
        
    k_list_one = ["assessed_biomarker_entity_id","assessed_biomarker_entity","assessed_entity_type"]
    k_list_one += ["assessed_entity_type"]
    
    out_comp_obj_list = []
    for component_index in tmp_dict:
        comp_obj = {"component_index":component_index, "entities":[]}
        seen, new_evdn_obj_list = {}, []
        for entity_index in tmp_dict[component_index]:
            obj = tmp_dict[component_index][entity_index]
            for k in obj:
                if k not in k_list_one and k not in comp_obj:
                    comp_obj[k] = obj[k]
            o = {"entity_index":entity_index}
            for k in k_list_one:
                o[k] = obj[k]
            comp_obj["entities"].append(o)
            for evdn_obj in obj["evidence_source"]:
                cmb = "%s|%s" % (evdn_obj["id"], evdn_obj["database"])
                if cmb not in seen:
                    new_evdn_obj_list.append(evdn_obj)
                    seen[cmb] = True
        comp_obj["evidence_source"] = new_evdn_obj_list
        out_comp_obj_list.append(comp_obj)
 
    return out_comp_obj_list




def load_annotation_dict(release_dir):


    url_dict = load_url_dict(release_dir + "misc/xref_info.csv")
   
    in_file = release_dir + "unreviewed/annotations.tsv"

    tmp_dict_one = {}
    with open(in_file, "r") as FR:
        f_list, lcount = [], 0
        for line in FR:
            lcount += 1
            row = line[0:-1].split("\t")
            if lcount == 1:
                f_list = row
            else:
                
                ent_id = row[f_list.index("assessed_biomarker_entity_id")]
                xref_key = row[f_list.index("xref_key")]
                xref_id = row[f_list.index("xref_id")]
                annotation_category = row[f_list.index("annotation_category")]
                annotation_term = row[f_list.index("annotation_term")]
                if xref_key == "protein_xref_uniprotkb_fun" and ent_id.find(xref_id) == -1:
                    continue
                if ent_id.find("UPKB:") != -1:
                    ent_id = ent_id.split("-")[0]

                cmb_one = "%s|%s|%s" % (ent_id,annotation_category, annotation_term)
                cmb_two = "%s|%s" % (xref_key, xref_id)
                if cmb_one not in tmp_dict_one:
                    tmp_dict_one[cmb_one] = {}
                tmp_dict_one[cmb_one][cmb_two] = True

    tmp_dict_two = {}
    for cmb_one in tmp_dict_one:
        ent_id = cmb_one.split("|")[0]
        annotation_category = cmb_one.split("|")[1]
        annotation_term = "|".join(cmb_one.split("|")[2:])
        if ent_id not in tmp_dict_two:
            tmp_dict_two[ent_id] = []
        ann_obj = {"entity_id":ent_id, "annotation_category":annotation_category, "annotation_term":annotation_term, "evidence":[]}
        for cmb_two in tmp_dict_one[cmb_one]:
            xref_key, xref_id = cmb_two.split("|")
            xref_lbl, xref_url = "", ""
            if xref_key in url_dict:
                xref_lbl, xref_url = url_dict[xref_key]["lbl"], url_dict[xref_key]["url"] % (xref_id)
            evdn_obj = {"id":xref_id, "database":xref_lbl, "url":xref_url}
            ann_obj["evidence"].append(evdn_obj)
        tmp_dict_two[ent_id].append(ann_obj)

    return tmp_dict_two


def load_entity_crossref_dict(release_dir):

    url_dict = load_url_dict(release_dir + "misc/xref_info.csv")

    in_file = release_dir + "unreviewed/xrefs.tsv"
    tmp_dict = {}
    with open(in_file, "r") as FR:
        f_list, lcount = [], 0
        for line in FR:
            lcount += 1
            row = line[0:-1].split("\t")
            if lcount == 1:
                f_list = row
            else:
                source_file = row[f_list.index("source_file")]
                biomarker_idx = row[f_list.index("biomarker_idx")]
                entity_id = row[f_list.index("entity_id")]
                xref_key = row[f_list.index("xref_key")]
                xref_id = row[f_list.index("xref_id")]
                cmb_two = "%s|%s" % (xref_key,xref_id)
                if entity_id not in tmp_dict:
                    tmp_dict[entity_id] = {}
                tmp_dict[entity_id][cmb_two] = True

    xref_dict = {}
    for entity_id in tmp_dict:
        for cmb_two in tmp_dict[entity_id]:
            xref_key, xref_id = cmb_two.split("|")
            if xref_key in url_dict:
                xref_lbl, xref_url = url_dict[xref_key]["lbl"], url_dict[xref_key]["url"] % (xref_id)
                o = {"id":xref_id, "url":xref_url, "database":xref_lbl, "categories":[]}
                if entity_id not in xref_dict:
                    xref_dict[entity_id] = []
                xref_dict[entity_id].append(o)

    return xref_dict

    


