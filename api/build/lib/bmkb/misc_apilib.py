import os
import string
import random
import hashlib
import json
import datetime,time
import pytz
import glob
from collections import OrderedDict
import collections
import subprocess

from jsonschema import validate, Draft7Validator
import jsonschema


from flask import Flask, request, jsonify, Response, stream_with_context

import zlib
import gzip
import struct           



from bmkb.db import get_mongodb
from bmkb.util import get_errors_in_query, sort_objects, cache_hitlist, load_species_info
from bmkb.protein_apilib import protein_detail
from bmkb.glycan_apilib import glycan_detail
from bmkb.libgly import load_sheet, load_sheet_as_dict




def verlist(config_obj):
    
    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj
   
    init_obj = dbh["c_init"].find_one({})
    out_obj = []
    for rel in init_obj["versionlist"]:
        out_obj.append(rel)
 
    return out_obj

def messagelist(config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    out_obj = []
    import pymongo
    #q_obj = { "creation_time": { "$exists": True} } 
    q_obj = {}
    for doc in dbh["c_message"].find(q_obj).sort('creation_time', pymongo.DESCENDING):
        doc.pop("_id")
        for k in ["creation_time", "update_time", "ts"]:
            if k not in doc:
                continue
            doc[k] = doc[k].strftime('%Y-%m-%d %H:%M:%S %Z%z')
        out_obj.append(doc)


    return out_obj


def bcolist(config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    out_obj = {}
    for doc in dbh["c_bco"].find({}):
        if "object_id" in doc:
            bco_id = doc["object_id"].split("/")[3]
            if "io_domain" in doc:
                if "output_subdomain" in doc["io_domain"]:
                    if doc["io_domain"]["output_subdomain"] != []:
                        file_name = doc["io_domain"]["output_subdomain"][0]["uri"]["filename"]
                        out_obj[bco_id] = file_name

    return out_obj


def testurls (query_obj, config_obj):
      
    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    coll = query_obj["coll"]
    group_dict = config_obj["urltest"][coll]["groups"]
    id_field = config_obj["urltest"][coll]["idfield"]
    mongo_query = {id_field:{"$in":query_obj["idlist"]}}

    url_list = {}
    for doc in dbh[coll].find(mongo_query):
        if coll == "c_glycan":
            url = "https://glytoucan.org/Structures/Glycans/%s" % (doc["glytoucan_ac"])
            doc["glytoucan"] = {"glytoucan_url":url}
        elif coll == "c_protein":
            url = "http://www.uniprot.org/uniprot/%s/" % (doc["uniprot_canonical_ac"])
            doc["uniprot"] = {"url":url}
        
        for f in group_dict["group_one"]:
            obj_one = doc[f]
            fobj = group_dict["group_one"][f]
            url_key = fobj["field"]
            if url_key not in obj_one:
                continue
            url = obj_one[url_key]
            if f not in url_list:
                url_list[f] = []
            if url not in url_list[f]:
                url_list[f].append({"url":url})

        for f in group_dict["group_two"]:
            obj_one_list = doc[f]
            for obj_one in obj_one_list:
                fobj = group_dict["group_two"][f]
                url_key = fobj["field"]
                if url_key not in obj_one:
                    continue
                url = obj_one[url_key]
                if f not in url_list:
                    url_list[f] = []
                if url not in url_list[f]:
                    url_list[f].append({"url":url})
                        

        for f in group_dict["group_three"]:
            obj_one_list = doc[f]
            for obj_one in obj_one_list:
                for obj_two in obj_one["evidence"]:
                    fobj = group_dict["group_three"][f]
                    url_key = fobj["field"]
                    if url_key not in obj_two:
                        continue
                    url = obj_two[url_key]
                    if f not in url_list:
                        url_list[f] = []
                    if url not in url_list[f]:
                        url_list[f].append({"url":url})
        for f in group_dict["group_four"]:
            f_parts = f.split(".")
            obj_one_list = doc[f_parts[0]]
            fobj = group_dict["group_four"][f]
            url_key = fobj["field"]
            for obj_one in obj_one_list:
                if len(f_parts) < 3:
                    continue
                if f_parts[1] not in obj_one:
                    continue
                if f_parts[2] not in obj_one[f_parts[1]]:
                    continue
                obj_three_list = obj_one[f_parts[1]][f_parts[2]]
                for obj_three in obj_three_list:
                    if url_key not in obj_three:
                        continue
                    url = obj_three[url_key]
                    if f not in url_list:
                        url_list[f] = []
                    if url not in url_list[f]:
                        url_list[f].append({"url":url}) 
    
    import requests 
    res_obj = {"liveurls":{}, "deadurls":{}}
    seen = {}
    for f in url_list:
        for obj in url_list[f]:
            url = obj["url"]
            url_base = "/".join(url.split("/")[:-1])
            combo_id = "%s-%s" % (f, url_base)
            if combo_id in seen or url.find("xxx/yyy/") != -1:
                continue
            seen[combo_id] = True
            res = requests.get(url)
            status_code = res.status_code
            category = "deadurls"
            cn_len = 0
            if status_code == 200:
                category = "liveurls"
                cn_len = len(res.content)
            if f not in res_obj[category]:
                res_obj[category][f] = []
            res_obj[category][f].append(url)

    return res_obj

def testrecords (query_obj, config_obj, data_path):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    record_id, record_type = query_obj["recordid"], query_obj["recordtype"]


    
    integ_json = json.loads(open("conf/integrity.conf", "r").read())
    sec_info = integ_json[record_type]

    stat_obj = {"api":{}, "ds":{}}
    get_recordinfo_from_api(sec_info, query_obj, stat_obj, config_obj)
    
    get_recordinfo_from_ds(sec_info, query_obj,stat_obj, data_path)

    
    row_list_one, row_list_two = [], []
    for combo_id in list(set(stat_obj["api"].keys() + stat_obj["ds"].keys())):
        api_flag = combo_id in stat_obj["api"]
        ds_flag = combo_id in stat_obj["ds"]
        flag = [api_flag, ds_flag] == [True, True]
        row = [combo_id, str(api_flag), str(ds_flag), str(flag)]
        if flag == False:
            for i in range(0, len(row)):
                if row[i] != "True":
                    row[i] = '<font color=red>' + row[i] + '</font>';
            row_list_one.append(row)
        else:
            row_list_two.append(row)
    
    res_obj = {}
    res_obj["section"] = query_obj["section"] 
    res_obj["table"] = [
        ["combo_id","in_api", "in_dataset", "in_both"],
        ["string","string", "string", "string"]
    ]
    res_obj["table"] += row_list_one
    res_obj["table"] += row_list_two

    return res_obj



def get_recordinfo_from_ds(sec_info, query_obj, stat_obj, data_path): 
    sec = query_obj["section"]
    record_id = query_obj["recordid"]
    record_type = query_obj["recordtype"]
    
    masterlist_file = data_path + "releases/data/v-%s/misc/dataset-masterlist.json" % (query_obj["datarelease"])
    master_list = get_filename_list(masterlist_file)



    
    data_frame = {}
    xrefkey2badge = {}
    in_file = data_path + "releases/data/v-%s/misc/xref_info.csv" % (query_obj["datarelease"])
    load_sheet_as_dict(data_frame, in_file, ",", "xref_key")
    f_list = data_frame["fields"]
    for xref_key in data_frame["data"]:
        for row in data_frame["data"][xref_key]:
            xref_badge = row[f_list.index("xref_badge")]
            xrefkey2badge[xref_key] = xref_badge


    species_obj = {}
    seen = {}
    in_file = data_path
    in_file += "releases/data/v-%s/misc/species_info.csv" % (query_obj["datarelease"])
    load_species_info(species_obj, in_file)


    reviewed_dir = data_path + "releases/data/v-%s/reviewed/" 
    reviewed_dir = reviewed_dir % (query_obj["datarelease"])

    seen_glycan = {}
    in_file = reviewed_dir + "/glycan_masterlist.csv"
    sheet_obj = {}
    load_sheet_as_dict(sheet_obj, in_file, ",", "glytoucan_ac")
    tmp_fl = sheet_obj["fields"]
    for glytoucan_ac in sheet_obj["data"]:
        if glytoucan_ac not in seen_glycan:
            seen_glycan[glytoucan_ac] = True


    cmd = "grep ^'\"%s\"' " % (record_id) + reviewed_dir + "*_protein_masterlist.csv" 
    species = subprocess.getoutput(cmd).split("\n")[0].split(":")[0].split("/")[-1].split("_")[0]

    uniprotkb_ac = record_id.split("-")[0]
    if record_type == "protein" and sec == "species":
        tax_id = str(species_obj[species]["tax_id"])
        tax_name = species_obj[tax_id]["long_name"]
        id_list = [record_id, tax_id, tax_name, "UniProtKB",uniprotkb_ac]
        combo_id = "|".join(id_list)
        combo_id = combo_id.lower()
        stat_obj["ds"][combo_id] = True
        return
    
    if record_type == "glycan" and sec == "composition":
        in_file = data_path + "/releases/data/v-%s/reviewed/glycan_monosaccharide_composition.csv"
        in_file = in_file % (query_obj["datarelease"])
        data_frame = {}
        load_sheet_as_dict(data_frame, in_file, ",", "glytoucan_ac")
        f_list = data_frame["fields"]
        for row in data_frame["data"][record_id]:
            for f in f_list[:-1]:
                if row[f_list.index(f)] == "0":
                    continue
                id_list = [record_id.lower(), f.lower(), row[f_list.index(f)]]
                combo_id = "|".join(id_list)
                stat_obj["ds"][combo_id] = True
        return


    file_list = []
    for g in sec_info[sec]["glob"]:
        if g.find("SPECIES") != -1:
            g = g.replace("SPECIES", species)
        for f in glob.glob(reviewed_dir + g):
            if f.find(".stat.csv") == -1:
                file_list.append(f)


    seq_hash = {}
    in_file = data_path + "releases/data/v-%s/reviewed/%s_protein_allsequences.fasta"
    in_file = in_file % (query_obj["datarelease"], species)



    if sec == "orthologs":
        in_file = data_path + "releases/data/v-%s/reviewed/protein_homolog_clusters.csv" 
        in_file = in_file % (query_obj["datarelease"])
        data_frame = {}
        load_sheet(data_frame, in_file, ",")
        f_list = data_frame["fields"]
        cls_list = []
        for row in data_frame["data"]:
            canon = row[f_list.index("uniprotkb_canonical_ac")]
            if canon == record_id:
                cls_id = row[f_list.index("homolog_cluster_id")]
                cls_list.append(cls_id)
        for row in data_frame["data"]:
            cls_id = row[f_list.index("homolog_cluster_id")]
            canon = row[f_list.index("uniprotkb_canonical_ac")]
            if cls_id in cls_list and canon != record_id:
                tax_id = row[f_list.index("tax_id")]
                xref_key = row[f_list.index("xref_key")]
                xref_id = row[f_list.index("xref_id")]
                xref_badge = xrefkey2badge[xref_key]
                if xref_key == "protein_xref_oma":
                    xref_id = record_id.split("-")[0]
                combo_id = "|".join([record_id,canon,tax_id,xref_badge,xref_id])
                combo_id = combo_id.lower()
                stat_obj["ds"][combo_id] = True
        return


    canon2ensemblegeneid = {}
    if sec == "expression_tissue":
        in_file = data_path + "releases/data/v-%s/reviewed/%s_protein_xref_bgee.csv"
        in_file = in_file % (query_obj["datarelease"], species)
        data_frame = {}
        load_sheet_as_dict(data_frame, in_file, ",", "uniprotkb_canonical_ac")
        f_list = data_frame["fields"]
        for row in data_frame["data"][record_id]:
            xref_id = row[f_list.index("xref_id")]
            canon2ensemblegeneid[record_id] = xref_id

    seen_doid = {}
    if sec == "expression_disease":
        uberonid2doid = {}
        data_frame = {}
        in_file = data_path + "releases/data/v-%s/misc/doid2uberonid-mapping.csv" % (query_obj["datarelease"])
        load_sheet_as_dict(data_frame, in_file, ",", "uberon_id")
        f_list = data_frame["fields"]
        for uberon_id in data_frame["data"]:
            if uberon_id not in uberonid2doid:
                uberonid2doid[uberon_id] = []
            for row in data_frame["data"][uberon_id]:
                do_id = row[f_list.index("do_id")]
                if do_id not in uberonid2doid[uberon_id]:
                    uberonid2doid[uberon_id].append(do_id)


        in_file = data_path + "releases/data/v-%s/reviewed/%s_protein_expression_normal.csv"
        in_file = in_file % (query_obj["datarelease"], species)
        if os.path.isfile(in_file):
            data_frame = {}
            load_sheet_as_dict(data_frame, in_file, ",", "uniprotkb_canonical_ac")
            f_list = data_frame["fields"]
            for row in data_frame["data"][record_id]:
                uberon_id = row[f_list.index("uberon_anatomical_id")].split(":")[1]
                if uberon_id in uberonid2doid:
                    for do_id in uberonid2doid[uberon_id]:
                        seen_doid[do_id] = True

    main_id_name = "uniprotkb_canonical_ac"
    if sec in ["reactions","reaction_enzymes"]:
        main_id_name = "participant_id"

    if query_obj["recordtype"] == "glycan":
        main_id_name = "glytoucan_ac"
        if sec in ["glycoprotein", "interactions", "expression"]:
            main_id_name = "saccharide"


    heirarchy_dict = {}
    if sec == "subsumption":
        in_file = data_path + "releases/data/v-%s/reviewed/glycan_subsumption.csv"
        in_file = in_file % (query_obj["datarelease"])
        heirarchy_dict = load_subsumption_heirarchy(in_file)



    for in_file in file_list:
        file_type = in_file.split(".")[-1] 
        file_name = in_file.split("/")[-1]
        if file_name.split(".")[0] not in master_list:
            continue

        data_frame = {}
        load_sheet_as_dict(data_frame, in_file, ",", main_id_name)
        f_list = data_frame["fields"]
        if record_id in data_frame["data"]:
            for row in data_frame["data"][record_id]:
                if sec in ["interactions"] and record_type == "protein":
                    if row[f_list.index("saccharide")].strip() == "":
                        continue
                    if row[f_list.index("saccharide")].strip() not in seen_glycan:
                        continue
                if sec in ["expression_tissue"]:
                    f = "uberon_anatomical_id"
                    row[f_list.index(f)] =  row[f_list.index(f)].replace("UBERON:","")
                if sec in ["mutagenesis"]:
                    if row[f_list.index("ann_type")] not in ["Mutagenesis_Annotation"]:
                        continue
                if sec in ["reactions", "reaction_enzymes"]:
                    if row[f_list.index("role")] not in ["enzyme"]:
                        continue

                if sec in ["subsumption"]:
                    related_accession = row[f_list.index("related_accession")]
                    relationship = row[f_list.index("relationship")].lower()
                    glytoucan_type = row[f_list.index("glytoucan_type")].lower()
                    gt_list = ["topology", "composition", "basecomposition"]
                    rl_list = ["ancestor", "descendant"]
                    cond_one = record_id != related_accession
                    cond_two = glytoucan_type == relationship
                    cond_three = glytoucan_type in gt_list
                    cond = cond_one and cond_two and cond_three
                    if cond == False:
                        continue

                    rl = ""
                    if record_id in heirarchy_dict:
                        if related_accession in heirarchy_dict[record_id]:
                            rl = heirarchy_dict[record_id][related_accession]
                    row[f_list.index("relationship")] = rl

                if sec in ["expression"]:
                    if row[f_list.index("glycosylation_site_uniprotkb")] == "":
                        continue
                    abundance, tissue_name, uberon_id = "", "", ""
                    if "source_tissue_uberon_id" in f_list:
                        tissue_name = row[f_list.index("source_tissue_name")]
                        uberon_id = row[f_list.index("source_tissue_uberon_id")]
                    if "abundance" in f_list:
                        abundance = row[f_list.index("abundance")]
                    cl_name, cl_id = "", ""
                    if "source_cell_line_cellosaurus_id" in f_list:
                        cl_name = row[f_list.index("source_cell_line_name")]
                        cl_id = row[f_list.index("source_cell_line_cellosaurus_id")]
                    if "cellosaurus_id" in f_list:
                        cl_name = row[f_list.index("cellosuaurus_cell_line_name")]
                        cl_id = row[f_list.index("cellosaurus_id")]

                    src_xref_key = row[f_list.index("src_xref_key")]
                    if src_xref_key == "protein_xref_glyconnect":
                        row[f_list.index("src_xref_key")] = "glycan_xref_glyconnect"
                        row[f_list.index("src_xref_id")] = row[f_list.index("structure_id")]




                id_list_one = [record_id]
                evdn_list_one, evdn_list_two = [], []
                if file_name.find("_xref_") != -1:
                    if "xref_key" in f_list:
                        xref_key = row[f_list.index("xref_key")]
                        xref_id = row[f_list.index("xref_id")]
                        xref_badge = xrefkey2badge[xref_key]
                        id_list_one.append(xref_badge)
                        id_list_one.append(xref_id)
                    else:
                        xref_key = "_".join(file_name.split(".")[0].split("_")[1:])
                        xref_id = row[f_list.index("database_id")]
                        xref_badge = xrefkey2badge[xref_key]
                        id_list_one.append(xref_badge)
                        id_list_one.append(xref_id)
                elif sec in ["reactions"]:
                    src = in_file.split("_")[-1].split(".")[0]
                    id_list_one.append(row[f_list.index(sec_info[sec]["dsfieldlist"][0])])
                    id_list_one.append(src)
                    id_list_one.append(row[f_list.index(sec_info[sec]["dsfieldlist"][0])])
                else:
                    for f in sec_info[sec]["dsfieldlist"]:
                        if f.find(":md5") != -1:
                            f_new = f.split(":")[0]
                            v = row[f_list.index(f_new)].lower()
                            #v = hashlib.md5(v).hexdigest()
                            if sec == "go_annotation" and f_new == "go_term_category":
                                v = v.replace("_", " ")
                        else:
                            v = ""
                            if f == "aa_pos" and f not in f_list:
                                v = row[f_list.index("begin_aa_pos")]
                            elif f.find("CONSTANT_") != -1:
                                v = f.split("_")[1]
                            elif f in f_list:
                                v = row[f_list.index(f)]
                            if f in ["glycan_mass", "glycan_permass"] and v != "":
                                v = str(round(float(v),2))
                            v = xrefkey2badge[v] if f == "xref_key" and v in xrefkey2badge else v
                            v = xrefkey2badge[v] if f == "src_xref_key" and v in xrefkey2badge else v
                        if f in ["missing_score"] and v.strip() == "":
                            v = "0"

                        v = str(float(v)) if f == "uniprotkb_protein_mass" else v
                        if f == "do_id" and v == "":
                            v = "None"
                        if f in ["do_id","mondo_id"]:
                            v = "%s:%s" % (f,v)
                            v = v.replace("_", "")

                        if f in ["reviewed_isoforms", "unreviewed_isoforms"]:
                            v = row[f_list.index(f)]
                            if v in seq_hash:
                                #seq = seq_hash[v].lower()
                                id_list_one.append(v)
                                #id_list_one.append(seq)
                        elif f in ["xref_key", "xref_id","source_id"]:
                            evdn_list_one.append(v)
                        elif f in ["src_xref_key", "src_xref_id"]:
                            evdn_list_two.append(v)
                        else:
                            if f == "ec_name" and v != "":
                                v = "EC-%s"%(v)
                            id_list_one.append(v)

                #print "Robel", sec_info[sec]["dsfieldlist"]
                #print "Robel", id_list_one
                if record_type == "protein" and sec == "snv":
                    #id_list_one += ["BioMuta", uniprotkb_ac]
                    xref_key = row[f_list.index("xref_key")]
                    xref_id = row[f_list.index("xref_id")]
                    id_list_one += [xrefkey2badge[xref_key],xref_id]
                elif record_type == "protein" and sec == "expression_disease":
                    do_id = id_list_one[-1]
                    parent_doid = row[f_list.index("parent_doid")]
                    if do_id not in seen_doid and parent_doid not in seen_doid:
                        continue
                    id_list_one += ["BioXpress", uniprotkb_ac]
                elif record_type == "protein" and sec == "expression_tissue":
                    id_list_one[1] = id_list_one[1].replace("present", "yes")
                    id_list_one[1] = id_list_one[1].replace("absent", "no")
                    id_list_one += ["Bgee", canon2ensemblegeneid[record_id]]
                elif record_type == "glycan" and sec == "residues":
                    id_list_one[-1] = "rxn." + id_list_one[-1]

                if sec == "isoforms":
                    for seq_id in id_list_one[1:]:
                        if seq_id in seq_hash:
                            seq = seq_hash[seq_id].lower()
                            combo_id = "|".join([id_list_one[0], seq_id, seq])
                            combo_id = combo_id.lower()
                            stat_obj["ds"][combo_id] = True
                elif sec == "protein_names" and len(id_list_one) > 1:
                    name_type = "recommended" if in_file.find("recnames") != -1 else "synonym"
                    resource = "refseq" if in_file.find("refseq") != -1 else "uniprotkb"
                    id_list_one = [id_list_one[0], name_type,resource] +  list(set(id_list_one[1:]))
                    if "" in id_list_one:
                        id_list_one.remove("")
                    for tmp_id in id_list_one[3:]:
                        if tmp_id[0:3] == "EC-":
                            out_list = [id_list_one[0],"synonym",id_list_one[2]] + [tmp_id[3:]]
                            combo_id = "|".join(out_list)
                        else:
                            combo_id = "|".join(id_list_one[0:3] + [tmp_id])
                        combo_id = combo_id.lower()
                        stat_obj["ds"][combo_id] = True
                elif sec == "gene_names" and len(id_list_one) > 1:
                    resource = "refseq" if in_file.find("refseq") != -1 else "uniprotkb"
                    for j in range(1, len(id_list_one)):
                        name_type = "recommended" if j == 1 else "synonym"
                        name = id_list_one[j]
                        if name == "":
                            continue
                        new_id_list_one = [id_list_one[0], name_type,resource] + [name]
                        combo_id = "|".join(new_id_list_one)
                        combo_id = combo_id.lower()
                        stat_obj["ds"][combo_id] = True
                else:
                    if "" in id_list_one:
                        id_list_one.remove("")

                    if "doid:None" in id_list_one:
                        id_list_one.remove("doid:None")
                    else:
                        tmp_list = []
                        for x in id_list_one:
                            if x.find("mondoid") == -1:
                                tmp_list.append(x)
                        id_list_one = tmp_list
                   
                    if evdn_list_one != []:
                        tmp_list = id_list_one + evdn_list_one
                        combo_id = "|".join(tmp_list).lower().replace("mondoid", "mondo")
                        stat_obj["ds"][combo_id] = True
                        #print "DS-1:Robel", id_list_one, evdn_list_one
                    if evdn_list_two != []:
                        tmp_list = id_list_one + evdn_list_two
                        combo_id = "|".join(tmp_list).lower().replace("mondoid", "mondo")
                        stat_obj["ds"][combo_id] = True
                        #print "DS-2:Robel", id_list_one, evdn_list_two

                    if evdn_list_one == [] and evdn_list_two == []:
                        if len(id_list_one) == 1:
                            return
                        tmp_list = id_list_one 
                        combo_id = "|".join(tmp_list).lower().replace("mondoid", "mondo")
                        stat_obj["ds"][combo_id] = True
                        #print "DS-3:Robel", id_list_one
                        

    return



def get_recordinfo_from_api(sec_info, query_obj, stat_obj, config_obj):
   
    sec = query_obj["section"]
    record_id = query_obj["recordid"]
    record_type = query_obj["recordtype"]

    doc = {}
    if record_type == "protein":
        q_obj = {"uniprot_canonical_ac":record_id}
        doc = protein_detail(q_obj, config_obj)
    elif record_type == "glycan":
        q_obj = {"glytoucan_ac":record_id}
        doc = glycan_detail(q_obj, config_obj)



    if sec not in doc:
        #combo_id = record_id.lower() + "|"
        #stat_obj["api"][combo_id] = True
        return



    if sec in sec_info:
        obj_list = doc[sec]
        if type(obj_list) is not list:
            if type(obj_list) in [int, float, str]:
                obj_list = [{sec:doc[sec]}]
            else:
                obj_list = [doc[sec]]
        if sec == "go_annotation":
            obj_list = doc[sec]["categories"]
        for obj in obj_list:
            if obj == {}:
                continue
            id_list_one = [record_id]
            for f in sec_info[sec]["apifieldlist"]:
                if f.find(":md5") != -1:
                    f_new = f.split(":")[0]
                    v = obj[f_new].lower() if f_new in obj else ""
                    if f_new in ["name", "full"]:
                        v = v.split(";")[0]
                    #v = hashlib.md5(v).hexdigest()
                    id_list_one.append(str(v))
                else:
                    v = str(obj[f]) if f in obj else ""
                    v = v.split(";")[0] if sec in ["gene"] else v
                    id_list_one.append(str(v))
            if record_type == "protein" and sec in ["protein_names", "gene_names"]:
                v = "%s|%s|%s" % (obj["type"], obj["resource"],obj["name"])
                id_list_one.append(v)
            elif record_type == "protein" and sec == "disease":
                d_id = obj["recommended_name"]["id"] if "recommended_name" in obj else ""
                #d_id = d_id.replace("DOID:", "")
                id_list_one.append(d_id)
            elif record_type in ["protein", "glycan"] and sec == "publication":
                for o in obj["reference"]:
                    id_list_one += [o["type"],o["id"]]
                    #print "Robel-1", o

            elif record_type == "protein" and sec == "snv" and "disease" in obj:
                for o in obj["disease"]:
                    d_id = o["recommended_name"]["id"] if "recommended_name" in o else ""
                    #id_list_one.append(d_id)
            elif record_type == "protein" and sec == "isoforms" and "sequence" in obj:
                if "sequence" in obj["sequence"]:
                    id_list_one.append(obj["sequence"]["sequence"].lower())
            elif record_type == "protein" and sec == "expression_disease" and "disease" in obj:
                if obj["disease"] != []:
                    for o in obj["disease"]:
                        do_id = o["recommended_name"]["id"]
                        id_list_one.append(do_id)
            elif record_type == "protein" and sec == "expression_tissue" and "tissue" in obj:
                if "id" in obj["tissue"]:
                    id_list_one.append(obj["tissue"]["id"])
                    id_list_one.append(obj["tissue"]["name"].lower())
            elif record_type == "protein" and sec == "gene" and "locus" in obj:
                id_list_one.append(str(obj["locus"]["chromosome"]))
                start_pos = str(obj["locus"]["start_pos"])
                end_pos = str(obj["locus"]["end_pos"])
                id_list_one += sorted([start_pos, end_pos])
                if "evidence" in obj["locus"]:
                    if "evidence" != []:
                        id_list_one.append(str(obj["locus"]["evidence"][0]["id"]))
            elif record_type == "glycan" and sec == "classification":
                gly_type, gly_subtype = "", ""
                if "type" in obj:
                    gly_type = obj["type"]["name"]
                if "subtype" in obj:
                    gly_subtype = obj["subtype"]["name"]
                if gly_type.lower() not in ["other"] and gly_subtype.lower() not in ["other"]:
                    id_list_one += [gly_type, gly_subtype]


            if "" in id_list_one:
                id_list_one.remove("")


            if sec not in ["publication"] and "evidence" in obj:
                for ev_obj in obj["evidence"]:
                    id_list_two = []
                    if "id" in ev_obj:
                        id_list_two.append(ev_obj["database"])
                        id_list_two.append(str(ev_obj["id"]))
                    combo_id = "|".join(id_list_one + id_list_two)
                    combo_id = combo_id.lower()
                    stat_obj["api"][combo_id] = True
                    #print "Robel", combo_id
            elif "go_terms" in obj:
                for term_obj in obj["go_terms"]:
                    id_list_two = []
                    id_list_two.append(term_obj["id"].replace(":", "_"))
                    id_list_two.append(term_obj["name"])
                    combo_id = "|".join(id_list_one + id_list_two)
                    combo_id = combo_id.lower()
                    stat_obj["api"][combo_id] = True
            else:
                if sec in ["reaction_enzymes"]:
                    id_list_one = [id_list_one[0],id_list_one[0].split("-")[0]]
                if len(id_list_one) == 1:
                    return
                combo_id = "|".join(id_list_one)
                combo_id = combo_id.lower()
                stat_obj["api"][combo_id] = True
                #print "Robel", id_list_one

    return 







def validate(query_obj, config_obj):
    
    schema_obj = query_obj["schema"]
    instance_obj = query_obj["instance"]
    msg_list = []
    try:
        Draft7Validator.check_schema(schema_obj)
    except jsonschema.SchemaError as e:
        msg_list.append(e.message)
    if msg_list == []:
        v = Draft7Validator(schema_obj)
        for error in sorted(v.iter_errors(instance_obj), key=str):
            msg_list.append(error.message)
    
    out_json = {"status":"valid"}
    if msg_list != []:
        out_json = {"status":"invalid", "messagelist":sorted(list(set(msg_list)))}
    return out_json



def pathlist(query_obj, config_obj):

    
    json_file = "specs/%s/detail/response.example.json" % (query_obj["recordtype"])
    if query_obj["recordtype"] in ["glycoprotein", "enzyme"]:
        json_file = "specs/protein/detail/response.example.json"

    api_doc = json.loads(open(json_file, "r").read())

    seen = {}
    load_properity_lineage(api_doc, "", seen)
    out_json = []
    for k in sorted(list(seen.keys())):
        out_json.append(k)

    return out_json




def propertylist(query_obj, config_obj):


    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj


    coll = "c_%s" % (query_obj["recordtype"])
    seen = {"api":{}, "docstore":{}}

    json_file = "specs/%s/detail/response.example.json" % (query_obj["recordtype"])
    if query_obj["recordtype"] in ["glycoprotein", "enzyme"]:
        json_file = "specs/protein/detail/response.example.json"
    if os.path.isfile(json_file) == True:
        api_doc = json.loads(open(json_file, "r").read())
        load_properity_lineage(api_doc, "", seen["api"])

    path_info = {}
    for doc in dbh["c_path"].find({}):
        record_type = doc["record_type"]
        if record_type == query_obj["recordtype"]:
            seen["docstore"][doc["path"]] = True
            path_info[doc["path"]] = {"label":doc["label"], "description":doc["description"]}



    seen["apinew"] = {}
    for k in list(seen["api"].keys()):
        k = k.replace("{", "").replace("}", "").replace("[0]", "")
        k = k.replace("enzymes.", "enzyme.")
        if k.find(" dict") != -1 or k.find(" list") != -1:
            continue
        seen["apinew"][k] = True

    out_json = {
        "in_api":[], "in_docstore":[],
        "in_api_only":[], "in_docstore_only":[], "in_api_and_docstore":[]}
    key_list = list(set(list(seen["docstore"].keys()) + list(seen["apinew"].keys())))
    for k in sorted(key_list):
        tv = [k in seen["docstore"].keys(), k in  seen["apinew"].keys()]
        #o = {"path":k.split("{")[0], "type":k.split("{")[1]} 
        if tv == [True, True]:
            out_json["in_api_and_docstore"].append(k)
        elif tv == [True, False]:
            out_json["in_docstore_only"].append(k)
        elif tv == [False, True]:
            out_json["in_api_only"].append(k)
        if k in seen["docstore"].keys():
            label = "xxx"
            if k in path_info:
                label = path_info[k]["label"]
            k_new = "%s|%s" % (k, label)
            out_json["in_docstore"].append(k_new)
        if k in seen["apinew"].keys():
            out_json["in_api"].append(k)

    for k in out_json:
        out_json[k] = sorted(out_json[k])

    return out_json


def load_properity_lineage(in_obj, in_key, seen):

    if type(in_obj) in [dict, collections.OrderedDict]:
        k = "%s {dict}" % (in_key)
        if in_key != "":
            seen[k] = True
        for k in in_obj:
            new_key = in_key + "." + k if in_key != "" else k
            load_properity_lineage(in_obj[k], new_key, seen)
    elif type(in_obj) is list:
        k = "%s {list}" % (in_key)
        seen[k] = True
        for idx in range(0, len(in_obj)):
            if idx > 0:
                continue
            idx_key = in_key + "[%s]" % (idx) 
            load_properity_lineage(in_obj[idx], idx_key, seen)
    elif type(in_obj) in [str, int, float]:
        value_type = str(type(in_obj)).replace("<type ", "").replace("'", "").replace(">", "")
        in_key += " {%s}" % (value_type)
        seen[in_key] = True

    return 



def get_filename_list(masterlist_file):

            
    file_name_list = []
    ds_obj_list = json.loads(open(masterlist_file, "r").read())
    for obj in ds_obj_list:
        ds_name = obj["name"]
        ds_format = obj["format"]
        mol = obj["categories"]["molecule"]
        if ds_name in ["homolog_alignments", "isoform_alignments"]:
            continue
        if obj["categories"]["species"] == []:
            if obj["integration_status"]["status"] == "integrate_all":
                file_name_list.append("%s_%s" % (mol, ds_name))
        elif obj["integration_status"]["status"] != "integrate_none":
            sp_list_one = sorted(obj["categories"]["species"])
            for species in sp_list_one:
                if species not in obj["integration_status"]["excludelist"]:
                    file_name_list.append("%s_%s_%s" % (species, mol, ds_name))

    return file_name_list


def gtclist(config_obj, data_path):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    init_obj = dbh["c_init"].find_one({})
    release_list = []
    for rel in init_obj["versionlist"]:
        release_list.append(rel)

    seen = {}
    for rel in release_list:
        reviewed_dir = data_path + "/releases/data/v-%s/reviewed/" % (rel)
        file_list = glob.glob(reviewed_dir + "/glycan_masterlist.csv")
        file_list += glob.glob(reviewed_dir + "/*_glycan_idmapping.csv")
        file_list += glob.glob(reviewed_dir + "/*_glycan_properties.csv")
        for in_file in file_list:
            sheet_obj = {}
            load_sheet_as_dict(sheet_obj, in_file, ",", "glytoucan_ac")
            tmp_fl = sheet_obj["fields"]
            for glytoucan_ac in sheet_obj["data"]:
                seen[glytoucan_ac] = True

    return list(seen.keys())





def load_subsumption_heirarchy(in_file):

    heirarchy_dict = {}
    data_frame = {}
    load_sheet_as_dict(data_frame, in_file, ",", "glytoucan_ac")
    tmp_fl = data_frame["fields"]
    for main_id in data_frame["data"]:
        for tmp_row in data_frame["data"][main_id]:
            related_accession = tmp_row[tmp_fl.index("related_accession")]
            relationship = tmp_row[tmp_fl.index("relationship")].lower()
            glytoucan_type = tmp_row[tmp_fl.index("glytoucan_type")].lower()
            gt_list = ["topology", "composition", "basecomposition"]
            rl_list = ["ancestor", "descendant"]
            if relationship in rl_list:
                if main_id not in heirarchy_dict:
                    heirarchy_dict[main_id] = {}
                if related_accession not in heirarchy_dict[main_id]:
                    heirarchy_dict[main_id][related_accession] = {}
                heirarchy_dict[main_id][related_accession] = relationship

    return heirarchy_dict



