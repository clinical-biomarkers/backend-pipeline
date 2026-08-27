import os
import string
import random
import hashlib
import json
import datetime,time
import pytz
from collections import OrderedDict
from flask import Flask, request, jsonify, Response, stream_with_context
import zlib
import gzip
import struct           
import subprocess

from bmkb.db import get_mongodb
from bmkb.util import cache_hitlist,  extract_name, get_errors_in_query, order_obj, order_list, make_list_objects_direct, make_list_objects_indirect, retrieve_cached_list_objects




def list_download(query_obj, config_obj, data_path):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    init_obj = dbh["c_init"].find_one({})
    img_path = data_path + "/releases/data/v-%s/glycanimages_snfg_png/" % (init_obj["dataversion"])

    #Collect errors 
    error_list = get_errors_in_query("list_download",query_obj, config_obj)
    if error_list != []:
        if error_list[0]["field"] == "id" and query_obj["download_type"] == "motif_list":
            x = "xxx" # do nothing
        else:
            return {"error_list":error_list}

    if query_obj["download_type"] not in config_obj["downloadtypes"].keys():
        error_list.append({"error_code":"download-type-not-supported"})
        return {"error_list":error_list}
    
    if query_obj["format"].lower() not in config_obj["downloadtypes"][query_obj["download_type"]]["formatlist"]:
        error_list.append({"error_code":"download-type-format-combination-not-supported"})
        return {"error_list":error_list}

    if query_obj["format"].lower() not in config_obj["mimetypes"]:
        error_list.append({"error_code":"non-existent-mime-type-for-submitted-format"})
        return {"error_list":error_list}



    format_lc = query_obj["format"].lower()
    download_type_list = [
        "glycan_list", "site_list", "biomarker_list", "motif_list","protein_list", "genelocus_list", 
        "disease_list","ortholog_list",
        "idmapping_list_mapped", "idmapping_list_unmapped", "idmapping_list_all", 
        "idmapping_list_all_collapsed",
        "batch_retrieval"
    ]
    sequence_format_list = ["fasta", "iupac", "wurcs","glycam","smiles_isomeric","inchi","glycoct", "byonic", "grits"]

    data_buffer = ""
    if query_obj["download_type"] in download_type_list:
        list_obj = get_list_object(query_obj, config_obj)
        #return {"list_obj":list_obj}
        if "error_list" in list_obj:
            return list_obj
        if query_obj["download_type"] == "batch_retrieval":
            data_buffer = get_batch_retrieval_buffer(list_obj, query_obj, config_obj)
        else:
            if format_lc in ["json"]:
                data_buffer = json.dumps(list_obj["results"], indent=4)
            elif format_lc in ["csv", "tsv"]:
                data_buffer = get_tabular_buffer(list_obj, query_obj, config_obj)
    elif query_obj["download_type"] == "isoform_mapper_list":
        data_path, server = os.environ["DATA_PATH"],os.environ["SERVER"]
        out_file = data_path + "/userdata/" + server + "/jobs/%s/output.tsv" % (query_obj["id"])
        data_buffer = ""
        if os.path.isfile(out_file):
            with open(out_file, "r") as FR:
                for line in FR:
                    row = line[:-1].split("\t")
                    data_buffer += "\"" + "\",\"".join(row) + "\"\n"


    #Now that we have data_buffer, let's worry about compression
    if query_obj["compressed"] == True:
        fname = "%s.%s" % (query_obj["id"], query_obj["format"])
        c_data_buffer = gzip.compress(bytes(data_buffer, 'utf-8'))
        res_stream = Response(c_data_buffer, mimetype='application/gzip')
        res_stream.headers['Content-Disposition'] = 'attachment; filename=%s.gz' % (fname)
    else:
        res_stream = Response(data_buffer, mimetype=config_obj["mimetypes"][format_lc])
    return res_stream





def detail_download(query_obj, config_obj, data_path):


    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    init_obj = dbh["c_init"].find_one({})

    #Collect errors 
    error_list = get_errors_in_query("detail_download",query_obj, config_obj)
    if error_list != []:
        d_type = query_obj["download_type"] if "download_type" in query_obj else ""
        if error_list[0]["field"] != "id" and d_type != "motif_list":
            return {"error_list":error_list}

    if query_obj["download_type"] not in config_obj["downloadtypes"].keys():
        error_list.append({"error_code":"download-type-not-supported"})
        return {"error_list":error_list}
    
    if query_obj["format"].lower() not in config_obj["downloadtypes"][query_obj["download_type"]]["formatlist"]:
        error_list.append({"error_code":"download-type-format-combination-not-supported"})
        return {"error_list":error_list}

    if query_obj["format"].lower() not in config_obj["mimetypes"]:
        error_list.append({"error_code":"non-existent-mime-type-for-submitted-format"})
        return {"error_list":error_list}

    format_lc = query_obj["format"].lower()
    img_path = data_path + "/releases/data/v-%s/glycanimages_snfg_png/" % (init_obj["dataversion"])
    if format_lc == "svg":
        img_path = data_path + "/releases/data/v-%s/glycanimages_snfg_svg/" % (init_obj["dataversion"])
    img_file = img_path +  "G0000000." + format_lc
 
    download_type_list =  [
        "glycan_detail", "motif_detail", "protein_detail","protein_detail_isoformset","protein_detail_homologset", 
        "site_detail", "publication_detail", "glycan_image", "biomarker_detail", "disease_detail"
    ]
    sequence_format_list = ["fasta", "iupac", "wurcs","glycam","smiles_isomeric","inchi","glycoct", "byonic", "grits"]

    data_buffer = ""
    if query_obj["download_type"] in download_type_list:
        record_obj = get_record_object(dbh, query_obj, config_obj)
        if record_obj == None:
            return {"error_list":{"error_code":"non-existent-record"}}
        elif query_obj["download_type"] in ["glycan_image"] and format_lc in ["png", "svg"]:
            img_file = img_path + query_obj["id"].upper() + "." + format_lc
            if os.path.isfile(img_file) == False:
                img_file = img_path +  "G0000000." + format_lc
            data_buffer = open(img_file, "rb").read()
        elif query_obj["download_type"] in ["motif_detail"] and format_lc in ["csv", "tsv"]:
            m_query = {"motifs.id": {'$eq': query_obj["id"]}}
            row = ["glytoucan_ac"]
            if format_lc == "csv":
                data_buffer += "\"" +  "\",\"".join(row) + "\"\n"
            elif format_lc == "tsv":
                data_buffer += "\"" +  "\"\t\"".join(row) + "\"\n"
            for o in dbh["c_glycan"].find(m_query):
                row = [o["glytoucan_ac"]]
                data_buffer += "\"" +  "\",\"".join(row) + "\"\n"
        elif query_obj["download_type"] in ["motif_detail"] and format_lc in ["png", "svg"]:
            data_buffer = ""
            glytoucan_ac = record_obj["glytoucan_ac"]
            img_file = img_path + glytoucan_ac.upper() + "." + format_lc
            if os.path.isfile(img_file) == False:
                img_file = img_path +  "G0000000." + format_lc
            data_buffer = open(img_file, "rb").read()
        else:
            data_buffer = json.dumps(record_obj,  indent=4)


    #Now that we have data_buffer, let's worry about compression
    if query_obj["compressed"] == True:
        fname = "%s.%s" % (query_obj["id"], query_obj["format"])
        c_data_buffer = ""
        if query_obj["download_type"] in ["glycan_image"]:
            c_data_buffer = gzip.compress(data_buffer)
        else:
            c_data_buffer = gzip.compress(bytes(data_buffer, 'utf-8'))
        res_stream = Response(c_data_buffer, mimetype='application/gzip')
        res_stream.headers['Content-Disposition'] = 'attachment; filename=%s.gz' % (fname)
    else:
        res_stream = Response(data_buffer, mimetype=config_obj["mimetypes"][format_lc])
    #print data_buffer

    return res_stream



def get_path_value(path, obj):

    p_list = path.split(".")
    val_obj = obj
    for p in p_list:
        if type(val_obj) is dict:
            val_obj = val_obj[p] if p in val_obj else ""
        elif type(val_obj) is list:
            tmp_list = []
            for val in val_obj:
                if type(val) is dict:
                    if type(val[p]) in [int, float, str]:
                        tmp_list.append(str(val[p]))
            val_obj = ";".join(tmp_list)
    return val_obj





def section_download(query_obj, config_obj, sec_info, data_path):

    
    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj


    #Collect errors 
    error_list = get_errors_in_query("section_download",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}

    if query_obj["download_type"] not in config_obj["downloadtypes"].keys():
        error_list.append({"error_code":"download-type-not-supported"})
        return {"error_list":error_list}
    
    if query_obj["format"].lower() not in config_obj["downloadtypes"][query_obj["download_type"]]["formatlist"]:
        error_list.append({"error_code":"download-type-format-combination-not-supported"})
        return {"error_list":error_list}

    if query_obj["format"].lower() not in config_obj["mimetypes"]:
        error_list.append({"error_code":"non-existent-mime-type-for-submitted-format"})
        return {"error_list":error_list}
   
    format_lc = query_obj["format"].lower()
    download_type_list =  [ "protein_section", "site_section", "glycan_section", 
        "motif_section", "publication_section", "biomarker_section", "disease_section"]


    data_buffer = ""
    if query_obj["download_type"] in download_type_list:
        if "section" not in query_obj:
            return {"error_list":{"error_code":"missing-required-field (section)"}}
        sec = query_obj["section"]
        record_type = query_obj["download_type"].split("_")[0] 
        if record_type not in sec_info:
            return {"error_list":{"error_code":"unknown-record-type"}}
        if sec not in sec_info[record_type]:
            return {"error_list":{"error_code":"unknown-section"}}
        if "sectionfield" not in sec_info[record_type][sec]:
            return {"error_list":{"error_code":"unknown-section-field"}}

        filter_info = sec_info[record_type][sec]["filterinfo"]
        filter_type = filter_info["filtertype"] if "filtertype" in filter_info else ""
        lbl_dict = {}
        for o in sec_info[record_type][sec]["fieldmap"]:
            lbl_dict[o["path"]] = o["label"]

        record_obj = get_record_object(dbh, query_obj, config_obj)
        
        sec_field = sec_info[record_type][sec]["sectionfield"]
        if sec_field not in record_obj:
            return {"error_list":{"error_code":"missing-section-field"}}
        obj_list = record_obj[sec_field]


        debug_list = []
        list_obj = {"results":[]}
        idx = 0
        for obj in obj_list:
            idx += 1
            if filter_info["field"] != "":
                if filter_info["field"] in obj:
                    field_val = obj[filter_info["field"]]
                    if type(field_val) is str:
                        if filter_type == "exclude" and field_val in filter_info["valuelist"]:
                            continue
                        elif field_val not in filter_info["valuelist"]:
                            continue
                    elif type(field_val) is dict:
                        tmp_flag_list = [k in filter_info["valuelist"] for k in field_val]
                        if list(set(tmp_flag_list)) == [False]:
                            continue
                    elif type(field_val) is list:
                        overlap = False
                        for v in filter_info["valuelist"]:
                            if v in field_val:
                                overlap = True
                        if filter_type == "exclude" and overlap == True:
                            continue
                        elif filter_type != "exclude" and overlap == False:
                            continue
            o = {"idx":idx}
            debug_list.append(o)
            for path in lbl_dict:
                val_obj = get_path_value(path, obj)
                if type(val_obj) is list:
                    tmp_list = []
                    for val in val_obj:
                        if type(val) in [str, int, float]:
                            tmp_list.append(str(val))
                    val_obj = "; ".join(tmp_list)
                if type(val_obj) in [str, int, float]:
                    lbl = lbl_dict[path] if path in lbl_dict else path
                    o[lbl] = str(val_obj)
            #return {"o":o, "obj":obj, "lbl_dict":lbl_dict}
 
            #debug_list.append(o)
            if "evidence" in obj:
                if obj["evidence"] != []:
                    for oo in obj["evidence"]:
                        #new_o = o
                        new_o = {}
                        for k in o:
                            new_o[k] = o[k]
                        xref_db = oo["database"] if "database" in oo else ""
                        xref_url = oo["url"] if "url" in oo else ""
                        xref_id = oo["id"] if "id" in oo else ""
                        new_o["Source Xref DB"] = xref_db
                        new_o["Source Xref ID"] = xref_id 
                        new_o["Source Xref URL"] = xref_url
                        list_obj["results"].append(new_o)
                else:
                    list_obj["results"].append(o)
            else:
                list_obj["results"].append(o)

        #return debug_list

        if format_lc in ["csv", "tsv"]:
            data_buffer = get_tabular_buffer(list_obj, query_obj, config_obj)
            #data_buffer = json.dumps(list_obj)


    
    #Now that we have data_buffer, let's worry about compression
    if query_obj["compressed"] == True:
        fname = "%s.%s" % (query_obj["id"], query_obj["format"])
        c_data_buffer = gzip.compress(bytes(data_buffer, 'utf-8'))
        res_stream = Response(c_data_buffer, mimetype='application/gzip')
        res_stream.headers['Content-Disposition'] = 'attachment; filename=%s.gz' % (fname)
    else:
        res_stream = Response(data_buffer, mimetype=config_obj["mimetypes"][format_lc])

    #print data_buffer

    return res_stream













def get_tabular_buffer(list_obj, query_obj, config_obj):

    data_buffer = ""
    ordr_dict = {}
    format_lc = query_obj["format"].lower() 
    type_list_one = [
        "idmapping_list_mapped", "idmapping_list_unmapped", "idmapping_list_all", "idmapping_list_all_collapsed"
    ]
    format_list_one = ["iupac", "wurcs","glycam","smiles_isomeric","inchi","glycoct", "byonic", "grits"]
    format_list_two = ["fasta"]

    if query_obj["download_type"] in config_obj["objectorder"]:
        ordr_dict = config_obj["objectorder"][query_obj["download_type"]]
                                                                    
    if query_obj["download_type"] in type_list_one:
        new_list_obj = []
        mapped_legends = list_obj["cache_info"]["mapped_legends"]
        unmapped_legends = list_obj["cache_info"]["unmapped_legends"]
        legend_dict = mapped_legends
        if query_obj["download_type"] == "idmapping_list_unmapped":
            legend_dict = unmapped_legends
        #print json.dumps(list_obj["results"], indent=4)
        for j in range(0, len(list_obj["results"])):
            obj = list_obj["results"][j]
            if query_obj["download_type"] == "idmapping_list_mapped":
                if obj["category"] == "unmapped":
                    continue
            if query_obj["download_type"] == "idmapping_list_unmapped":
                if obj["category"] == "mapped":
                    continue
                    
            if query_obj["download_type"] in ["idmapping_list_all", "idmapping_list_all_collapsed"]:
                legend_dict["input_id"] = legend_dict["from"]
                legend_dict["reason"] = legend_dict["to"]

            new_obj = {}
            for k in obj:
                if k in ["category", "hit_score", "score_info"]:
                    continue
                new_obj[legend_dict[k]] = obj[k]
                if k in ordr_dict:
                    ordr_dict[legend_dict[k]] = ordr_dict[k]
            new_list_obj.append(new_obj)
        if query_obj["download_type"] == "idmapping_list_all_collapsed":
            collapse_dict = {}
            list_obj["results"] = []
            for obj in new_list_obj:
                in_id = obj[legend_dict["from"]]
                anchor = obj[legend_dict["anchor"]] if legend_dict["anchor"] in obj else ""
                out_id = obj[legend_dict["to"]]                      
                if in_id not in collapse_dict:
                    collapse_dict[in_id] = {"to":[], "anchor":[]}
                if anchor not in collapse_dict[in_id]["anchor"]:
                    collapse_dict[in_id]["anchor"].append(anchor)
                if out_id not in collapse_dict[in_id]["to"]:
                    collapse_dict[in_id]["to"].append(str(out_id))

            for in_id in collapse_dict:
                out_id = ",".join(collapse_dict[in_id]["to"])
                anchor = ",".join(collapse_dict[in_id]["anchor"])
                obj = {legend_dict["from"]:in_id, legend_dict["to"]:out_id, 
                        legend_dict["anchor"]:anchor}
                list_obj["results"].append(obj)
        else:
            list_obj["results"] = new_list_obj



    results_key = "objlist" if "objlist" in list_obj else "results"
   
    col_list = []
    if "query" in list_obj:
        if "columns" in list_obj["query"]:
            col_list = list_obj["query"]["columns"]

    if len(list_obj[results_key]) > 0:
        key_list = order_list(list_obj[results_key][0].keys(), ordr_dict)
        #Adjust column list if based on col_list
        k_list_one, k_list_two = [], []
        for k in col_list:
            if k in key_list:
                k_list_one.append(k)
        for k in key_list:
            if k not in col_list:
                k_list_two.append(k)
        key_list = k_list_one + k_list_two
        header_list = []
        for hh in key_list:
            if hh not in ["hit_score", "score_info", "filter_code"]:
                header_list.append(hh)
        if "GlyTouCan Accession" in header_list:
            header_list.append("Glycan Image Url")
        if format_lc == "csv":
            data_buffer = "\"" +  "\",\"".join(header_list) + "\"\n"
        else:
            data_buffer = "\"" +  "\"\t\"".join(header_list) + "\"\n"

        seen_row = {}
        line_list = []
        for j in range(0, len(list_obj[results_key])):
            obj = list_obj[results_key][j]
            row = []
            for k in key_list:
                if k in ["hit_score", "score_info", "filter_code"]:
                    continue
                val_k = str(obj[k]) if k in obj else ""
                if query_obj["download_type"] == "ortholog_list" and k == "sequence":
                    val_k = obj[k]["sequence"]
                if query_obj["download_type"] == "ortholog_list" and k == "evidence":
                    val_k = obj[k][0]["url"]
                row.append(val_k)

            if "GlyTouCan Accession" in key_list:
                glytoucan_ac = obj["GlyTouCan Accession"]
                image_url = "https://api.glygen.org/glycan/image/%s" % (glytoucan_ac)
                row.append(image_url)
            s = json.dumps(row)
            if s in seen_row:
                continue
            seen_row[s] = True
            line = "\"" +  "\"\t\"".join(row) + "\"\n"
            if format_lc == "csv":
                line = "\"" +  "\",\"".join(row) + "\"\n"
            line_list.append(line)
        data_buffer += "".join(line_list)
 
    return data_buffer


def get_batch_retrieval_buffer(list_obj, query_obj, config_obj):

    format_lc = query_obj["format"].lower()
    data_buffer = ""
    header_list = ["Input ID"]
    order_dict = dict(sorted(list_obj["order_dict"].items(), key=lambda item: item[1]))
    for f in order_dict:
        lbl = list_obj["columns"][f] if f in list_obj["columns"] else "N/A"
        header_list.append(lbl)
    if format_lc == "csv":
        data_buffer = "\"" +  "\",\"".join(header_list) + "\"\n"
    else:
        data_buffer = "\"" +  "\"\t\"".join(header_list) + "\"\n"

    line_list = []
    for obj in list_obj["rows"]:
        row = [obj["input_id"]]
        for f in order_dict:
            val = str(obj[f]) if f in obj else ""
            row.append(str(obj[f])) 
        line = "\"" +  "\"\t\"".join(row) + "\"\n"
        if format_lc == "csv":
            line = "\"" +  "\",\"".join(row) + "\"\n"
        line_list.append(line)
    data_buffer += "".join(line_list)

    return data_buffer





def get_list_object(query_obj, config_obj):

  
    if query_obj["download_type"] == "batch_retrieval":
        job_type = "batch_retrieval"
        job_dir = config_obj[config_obj["server"]]["pathinfo"]["userdata"]
        job_dir +=  str(query_obj["id"]) + "/"
        out_file = job_dir + config_obj["jobinfo"][job_type]["output_files"][0]["name"]
        doc = json.loads(open(out_file, "r").read())
        out_json = {}
        for p in ["columns", "rows"]:
            if p in doc:
                out_json[p] = doc[p]
        out_json["order_dict"] = {}        
        if "query" in doc:
            if "parameters" in doc["query"]:
                if "columns" in doc["query"]["parameters"]:
                    for obj in doc["query"]["parameters"]["columns"]:
                        out_json["order_dict"][obj["column_id"]] = obj["order"]

        return out_json
 

    api_name = "list_download" 
    list_query = "" 
    collection = config_obj["downloadtypes"][query_obj["download_type"]]["cache"]
    mongo_query = {"list_id":query_obj["id"]}
    if query_obj["download_type"] == "motif_list":
        mongo_query = {}
    list_obj = {}
    if query_obj["download_type"] == "motif_list":
        list_query = {"sort":"glycan_count","order":"desc", "limit":10000000}
        #list_obj = make_motif_list_objects_direct(list_query, config_obj)
    else:
        list_query = {"id":query_obj["id"], "limit":config_obj["max_download_records"]}
        cache_id = "xxx"
        listcache_id = query_obj["id"]
        if "filters" in query_obj:
            list_query["filters"] = query_obj["filters"]
        if query_obj["download_type"] in ["idmapping_list_all", "idmapping_list_all_collapsed",
            "idmapping_list_mapped","idmapping_list_unmapped", "genelocus_list", "ortholog_list"]:
            if collection == "c_userlistcache":
                #return {"error_list":[{"error_code":"aaaaa", "listcache_id":listcache_id}]}
                in_dict = {"cache_id":cache_id,"listcache_id":listcache_id,"api_name":api_name}
                list_obj = retrieve_cached_list_objects(in_dict,query_obj,config_obj,"allrecords")    
            else:
                list_obj = make_list_objects_direct(list_query, config_obj, False)
        else:
            if collection == "c_usercache":
                list_obj = make_list_objects_indirect(list_query, config_obj, False)
            elif collection == "c_userlistcache":
                in_dict = {"cache_id":cache_id,"listcache_id":listcache_id,"api_name":api_name}
                list_obj = retrieve_cached_list_objects(in_dict,query_obj,config_obj,"allrecords") 
    if list_obj == None:
        return {"error_list":[{"error_code":"list object not found", "coll":collection, "list_query":list_query}]}
    if "_id" in list_obj:
        list_obj.pop("_id")
    return list_obj



def get_record_object(dbh, query_obj, config_obj):

    format_lc = query_obj["format"].lower()
    collection = "c_biomarker"
    main_id = ""
    if query_obj["download_type"] in ["biomarker_detail", "biomarker_section"]:
        main_id = "biomarker_id"   
 
    val = query_obj["id"]
    mongo_query = {main_id:{"$eq":val}}
    #return {"coll":collection, "mquery":mongo_query}
    record_obj = dbh[collection].find_one(mongo_query)
    if "_id" in record_obj:
        record_obj.pop("_id")

    return record_obj





def get_results_from_record_id(dbh, query_obj, section_field):


    main_id_dict = {
        "protein":"uniprot_canonical_ac",
        "glycan":"glytoucan_ac",
        "publication":"record_id",
        "biomarker":"biomarker_id",
        "motif":"motif_ac",
        "disease":"disease_id",
        "site":"id"
    }
    table_id, record_id = query_obj["section"], query_obj["id"]
    if table_id == "glycosylation_reported_with_glycans":
        table_id = "glycosylation_reported_with_glycan"

    record_type = query_obj["download_type"].split("_")[0]
    if record_type not in main_id_dict:
        return {"error_list":{"error_code":"non-existent-results (bad record_type)"}}
    main_id_field = main_id_dict[record_type]
    mongo_query = {main_id_field:{"$eq":record_id}}
    if main_id_field == "uniprot_canonical_ac":
        mongo_query = {
            "$or":[
                {"uniprot_canonical_ac":{"$eq":record_id}}, 
                {"uniprot_ac":{"$eq":record_id}}
            ]
        }

    if query_obj["download_type"] == "site_section":
        parts = record_id.split(".")
        if parts[0].find("-") == -1 and len(parts) == 3:
            tmp_list = []
            for i in range(1, 5):
                cmb = "%s-%s.%s.%s" % (parts[0], i, parts[1], parts[2])
                tmp_list.append({"id":{"$eq":cmb}})
            mongo_query = {"$or":tmp_list}


    #return mongo_query
    collection = "c_" + record_type
    doc = dbh[collection].find_one(mongo_query)
    if doc == None:
        return {"error_list":[{"error_code":"no record found for %s=%s" % (main_id_field, record_id)}]}
 
    if record_type == "protein":
        record_id = doc["uniprot_canonical_ac"]


    obj_list = []
    sec = section_field
    #sec = table_id
    #table_id_parts = table_id.split("_")
    #for k in ["glycosylation_", "snv_"]:
    #    if table_id.find(k) != -1:
    #        sec = table_id_parts[0]
    #if record_type in ["glycan"]:
    #    for k in ["expression_"]:
    #        if table_id.find(k) != -1:
    #            sec = table_id_parts[0]

    # Get section objects if this record was batched
    q = {"recordid": record_id, "recordtype": record_type}
    for batch_doc in dbh["c_batch"].find(q):
        if sec in doc:
            if sec in batch_doc["sections"]:
                doc[sec] += batch_doc["sections"][sec]

    #return {"n":len(doc[sec])}

    for obj in doc[sec]:
        if sec == "glycosylation":
            flag = False
            for site_cat in obj["site_category_dict"]:
                if table_id == sec + "_" + site_cat:
                    flag = True           
            if flag or record_type == "site":
                obj_list.append(obj)
        elif sec == "expression" and table_id == sec + "_" + obj["category"]:
                obj_list.append(obj)
        elif sec == "snv" and table_id == "snv_disease":
            if "disease" in obj["keywords"]:
                obj_list.append(obj)
        elif sec == "snv" and table_id == "snv_non_disease":
            if "disease" not in obj["keywords"]:
                obj_list.append(obj)
        else:
            obj_list.append(obj)


    return {"results":obj_list}
