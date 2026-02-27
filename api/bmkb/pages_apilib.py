import os
import string
import random
import hashlib
import json
import datetime,time
import pytz
import pymongo
from collections import OrderedDict



import smtplib
from email.mime.text import MIMEText


from bmkb.db import get_mongodb
from bmkb.util import cache_hitlist,  extract_name, get_errors_in_query, order_obj, load_species_info, get_taxid2name



def ontology(config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("pages_ontology",{}, config_obj)
    if error_list != []:
        return {"error_list":error_list}

    res_obj = {}
    for doc in dbh["c_ontology"].find({}):
        doc.pop("_id")
        if doc != {}:
            if "data" in doc:
                res_obj = doc["data"]
    return res_obj



def home_init(config_obj, data_path):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("pages_home_init",{}, config_obj)
    if error_list != []:
        return {"error_list":error_list}

    ts = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S %Z%z')
  
    res_obj = {"version":[], "statistics":[]}
    for doc in dbh["c_version"].find({}):
        doc.pop("_id")
        if doc != {}:
            res_obj["version"].append(doc)

    for doc in dbh["c_stat"].find({}):
        doc.pop("_id")
        if "stat" in doc:
            for obj in doc["stat"]:
                res_obj["statistics"].append(obj)


    now_est = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime('%m/%d/%Y %H:%M:%S')
    dt, tm = now_est.split(" ")[0], now_est.split(" ")[1]
    mm, dd, yy = dt.split("/")
    hr, mn, sc = tm.split(":")
    now_in_seconds = int(yy)*365*24*3600 + int(mm)*31*24*3600 + int(dd)*1*24*3600 + int(hr)*1*3600 + int(mn)*60 + int(sc)


    res_obj["events"] = []
    cond_list = []
    cond_list.append({"visibility":{"$eq":"visible"}})
    #cond_list.append({"status":{"$eq":"current"}})
    now = datetime.datetime.now()
    cond_list.append({"start_date_s":{"$lte":now_in_seconds}})
    cond_list.append({"end_date_s":{"$gte":now_in_seconds}})
    q_obj = {"$and":cond_list}
    doc_list = dbh["c_event"].find(q_obj).sort('createdts', pymongo.DESCENDING)
    for doc in doc_list:
        doc["id"] = str(doc["_id"])
        doc.pop("_id")
        for k in ["createdts", "updatedts", "start_date", "end_date"]:
            if k not in doc:
                continue
            doc[k] = doc[k].strftime('%Y-%m-%d %H:%M:%S %Z%z')
        doc["now_in_seconds"] = now_in_seconds
        res_obj["events"].append(doc)


    res_obj["video"] = {}
    doc = dbh["c_video"].find_one({})
    if doc != None:
        doc.pop("_id")
        for k in ["createdts"]:
            if k not in doc:
                continue
            if type(doc[k]) is not str:
                doc[k] = doc[k].strftime('%Y-%m-%d %H:%M:%S %Z%z').strip()
        res_obj["video"] = doc




    return res_obj 



def list_init(config_obj, query_obj):

    #Collect errors 
    error_list = get_errors_in_query("pages_list_init",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}
    
    res_obj = {}
    if query_obj["table_id"] in config_obj["list_init"]:
        res_obj = config_obj["list_init"][query_obj["table_id"]]
    else:
        return {"error_list":[{"error_code":"uknown-table-id-value"}]}

    return res_obj 



def filter_init(config_obj, query_obj):
    
    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj


    #Collect errors 
    error_list = get_errors_in_query("pages_filter_init",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}

    main_id_dict = {
        "protein":"uniprot_canonical_ac",
        "glycan":"glytoucan_ac",
        "publication":"record_id",
        "biomarker":"biomarker_id"
    }

    table_id, record_type, record_id = query_obj["table_id"],query_obj["record_type"], query_obj["record_id"]
    main_id_field = main_id_dict[record_type]
    mongo_query = {main_id_field:{"$regex":record_id, "$options":"i"}}
    #return mongo_query

    collection = "c_" + record_type
    doc = dbh[collection].find_one(mongo_query)
    if doc == None:
        return {"error_list":[{"error_code":"no record found for %s=%s" % (main_id_field, record_id)}]}

    sec_map = {
        "glycosylation_reported_with_glycan":"glycosylation",
        "glycosylation_reported":"glycosylation",
        "glycosylation_predicted":"glycosylation",
        "glycosylation_automatic_literature_mining":"glycosylation",
        "snv_disease":"snv",
        "snv_non_disease":"snv",
        "expression_tissue":"expression",
        "expression_cell_line":"expression"
    }
  
    if table_id not in sec_map:
        return {"error_list":[{"error_code":"no section found for table_id=%s" % (table_id)}]}
    sec = sec_map[table_id] 
    res_obj = {}

    if table_id not in config_obj["filter_init"]:
        return {"error_list":[{"error_code":"no filter_init found for table_id=%s" % (table_id)}]}
    filter_conf = config_obj["filter_init"][table_id] 

    taxid2name = get_taxid2name(default=True)
    taxid2name = dict(sorted(taxid2name.items(), key=lambda item: item[1]))
    sp_dict = {}
    for tax_id in taxid2name:
        sp_dict[taxid2name[tax_id]] = tax_id

    code_dict = {}
    for grp in sorted(filter_conf):
        code_dict[grp] = []
        sorted_dict = dict(sorted(filter_conf[grp]["order_dict"].items(), key=lambda item: item[1]))
        sorted_dict = sp_dict if grp == "by_organism" else sorted_dict
        for val in sorted_dict:
            if val != "":
                code_dict[grp].append({"value":val, "ptrn":"*"})

    #return code_dict

    grp_id_list = sorted(code_dict.keys())
   
    filter_code_list = [] 
    count_dict = {}
    query_site_cat = table_id.replace("glycosylation_", "")
    for obj in doc[sec]:
        #this fill filter out objects that are coming from tables that are not glycosylation
        #later this should be relaxed to include other tables
        if "site_category_dict" not in obj:
            continue
        if query_site_cat not in obj["site_category_dict"]:
            continue 
        if "filter_code" not in obj:
            continue
        code_parts = obj["filter_code"].split(".")
        filter_code_list.append(obj["filter_code"])
        for grp_idx in range(0, len(grp_id_list)):
            grp = grp_id_list[grp_idx]
            filter_code_list.append("%s-%s-%s" % (grp,len(code_dict[grp]), code_parts[grp_idx]))
            for j in range(0, len(code_parts[grp_idx])):
                label = code_dict[grp][j]["value"]
                if code_parts[grp_idx][j] == "1":
                    if grp not in count_dict:
                        count_dict[grp] = {}
                    if label not in count_dict[grp]:
                        count_dict[grp][label] = 0
                    count_dict[grp][label] += 1
    
    #return filter_code_list
    #return count_dict


    if "by_organism" in filter_conf:
        label_dict = {}
        for tax_id in taxid2name:
            species_name = taxid2name[tax_id]
            label_dict[species_name] = species_name
        order_dict = {}
        ordr = 1
        for species_name in sorted(label_dict):
            order_dict[species_name] = ordr
            ordr += 1
        filter_conf["by_organism"]["label_dict"] = label_dict
        filter_conf["by_organism"]["order_dict"] = order_dict


    res_obj["available"] = []
    tmp_seen = {}
    for grp in filter_conf:
        group_label = filter_conf[grp]["group_label"]
        group_ordr = filter_conf[grp]["group_order"]
        obj = {"id":grp, "label":group_label, "order":group_ordr, "tooltip":"", "tmp_options":{}}
        for option_id in filter_conf[grp]["order_dict"]:
            label = option_id
            option_ordr = filter_conf[grp]["order_dict"][option_id]
            if grp not in tmp_seen:
                tmp_seen[grp] = {}
            tmp_seen[grp][label] = True
            count = 0
            if grp in count_dict:
                if label in count_dict[grp]:
                    count = count_dict[grp][label]
            lbl = filter_conf[grp]["label_dict"][option_id] if option_id in filter_conf[grp]["label_dict"] else option_id
            obj["tmp_options"][option_id] = {"id":option_id, "label":lbl, "count":count,"order":option_ordr}
        res_obj["available"].append(obj)

    #return res_obj


    seen = {}
    obj_list = []
    for grp_obj in res_obj["available"]:
        filter_group_id = grp_obj["id"]
        grp_obj["options"] = []
        for option_id in grp_obj["tmp_options"]:
            obj = grp_obj["tmp_options"][option_id]
            if obj["count"] == 0:
                continue
            grp_obj["options"].append(obj)
            if filter_group_id not in seen:
                seen[filter_group_id] = {}
            if option_id not in seen[filter_group_id]:
                seen[filter_group_id][option_id] = True
        grp_obj.pop("tmp_options")
        if grp_obj["options"] != []:
            obj_list.append(grp_obj)

    res_obj["available"] = obj_list


    return res_obj










def convert_stat_json(backend_obj, frontend_obj):
    
    frontend_key_sets = [
        ["venn_protein_homo", "venn_protein_mus", "venn_protein_rat"],
        ["venn_glycan_species"],
        ["bar_mass_ranges","bar_sugar_ranges"],
        ["sunb_canon_isof_prot"],
        ["sunb_glycan_organism_type"],
        ["sunb_glycan_type_subtype"],
        ["sunb_bio_molecules"],
        ["sunb_glycoprot_rep_pred_glyc"],
        ["pie_glycohydrolases_prot", "pie_glycosyltransferases_prot"],
        ["donut_motif"]
    ]

    for k_one in frontend_obj.keys():
        if k_one in frontend_key_sets[0]:
            for o in frontend_obj[k_one]:
                tax_id = o["organism"]["id"]
                s = [str(idx) for idx in o["sets"]]
                backend_key = "%s_%s" % (tax_id, "|".join(s))
                if backend_key in backend_obj["protein"]["byproteintype"]:
                    o["size"] = backend_obj["protein"]["byproteintype"][backend_key]
            #print json.dumps(frontend_obj[k_one], indent=4)
        elif k_one in frontend_key_sets[1]:
            for o in frontend_obj[k_one]:
                s = [str(idx) for idx in o["sets"]]
                backend_key = "%s" % ("|".join(s))
                if backend_key in backend_obj["glycan"]:
                    o["size"] = backend_obj["glycan"][backend_key]
                #print json.dumps(frontend_obj[k_one], indent=4)
        elif k_one in frontend_key_sets[2]:
            frontend_obj[k_one]["data"] = backend_obj["glycan"][k_one]
            #print json.dumps(frontend_obj[k_one], indent=4)
        elif k_one in frontend_key_sets[3]:
            for o_one in frontend_obj[k_one]["children"]:
                tax_id = o_one["organism"]["id"]
                for o_two in o_one["children"]:
                    seq_type = "canonical"
                    if o_two["name"].find("Isoform") != -1:
                        seq_type = "isoform"
                    backend_key = "%s_%s" % (tax_id, seq_type)
                    if backend_key in backend_obj["protein"]["bysequencetype"]:
                        n = backend_obj["protein"]["bysequencetype"][backend_key]
                        o_two["size"] = n
            #print json.dumps(frontend_obj[k_one], indent=4)
        elif k_one in frontend_key_sets[4]:
            for o_one in frontend_obj[k_one]["children"]:
                tax_id = o_one["organism"]["organism_list"][0]["id"]
                for o_two in o_one["children"]:
                    g_type = o_two["glycan_type"].lower()
                    backend_key = "%s_%s" % (tax_id, g_type)
                    if backend_key in backend_obj["glycan"]["byglycantype"]:
                        n = backend_obj["glycan"]["byglycantype"][backend_key]
                        o_two["size"] = n
            #print json.dumps(frontend_obj[k_one], indent=4)
        elif k_one in frontend_key_sets[5]:
            for o_one in frontend_obj[k_one]["children"]:
                g_type = o_one["name"].lower()
                for o_two in o_one["children"]:
                    g_subtype = o_two["name"].lower()
                    backend_key = "%s_%s" % (g_type, g_subtype)
                    if backend_key in backend_obj["glycan"]["byglycantype"]:
                        n = backend_obj["glycan"]["byglycantype"][backend_key]
                        o_two["size"] = n
                    #print json.dumps(frontend_obj[k_one], indent=4)
        elif k_one in frontend_key_sets[6]:
            for o_one in frontend_obj[k_one]["children"]:
                if o_one["name"].find("Protein") != -1:
                    tax_id = o_one["organism"]["id"]
                    backend_key = "%s" % (tax_id)
                    if backend_key in backend_obj["protein"]["total"]:
                        n = backend_obj["protein"]["total"][backend_key]
                        o_one["size"] = n
                else:
                    tax_id = o_one["organism"]["organism_list"][0]["id"]
                    for o_two in o_one["children"]:
                        g_type = o_two["glycan_type"].lower()
                        backend_key = "%s_%s" % (tax_id, g_type)
                        if backend_key in backend_obj["glycan"]["byglycantype"]:
                            n = backend_obj["glycan"]["byglycantype"][backend_key]
                            o_two["size"] = n
            #print json.dumps(frontend_obj[k_one], indent=4)
        elif k_one in frontend_key_sets[7]:
            for o_one in frontend_obj[k_one]["children"]:
                for o_two in o_one["children"]:
                    tax_id = o_two["organism"]["id"]
                    site_type = o_two["name"].split(" ")[1].lower()
                    backend_key = "%s_%s" % (tax_id, site_type)
                    if backend_key in backend_obj["protein"]["bysitetype"]:
                        n = backend_obj["protein"]["bysitetype"][backend_key]
                        o_two["size"] = n
            #print json.dumps(frontend_obj[k_one], indent=4)
        elif k_one in frontend_key_sets[8]:
            for o_one in frontend_obj[k_one]:
                tax_id = o_one["organism"]["id"]
                backend_key = "%s" % (tax_id)
                enzyme_type = k_one.split("_")[1]
                if backend_key in backend_obj["protein"][enzyme_type]:
                    n = backend_obj["protein"][enzyme_type][backend_key]
                    o_one["size"] = n
            #print json.dumps(frontend_obj[k_one], indent=4)
        elif k_one in frontend_key_sets[9]:
            for o_one in frontend_obj[k_one]:
                backend_key = "%s" % (o_one["name"].lower())
                if backend_key in backend_obj["glycan"]["bymotiftype"]:
                    n = backend_obj["glycan"]["bymotiftype"][backend_key]
                    o_one["size"] = n

    return


def get_data_statistics(config_obj):

    db_obj =  config_obj[config_obj["server"]]["dbinfo"]
   
    backend_obj = {
        "protein":{
            "total":{},
            "byproteintype":{},
            "bysequencetype":{},
            "bysitetype":{},
            "glycohydrolases":{},
            "glycosyltransferases":{}
        },
        "glycan":{
            "total":{},
            "byglycantype":{},
            "bymotiftype":{},
            "bar_mass_ranges":[1000000,1000000,1000000],
            "bar_sugar_ranges":[1000000,1000000,1000000]
        }
    }
    glycan_type_list = []
    glycan_subtype_list = []
    motif_list = []
    taxid_list = ["9606", "10090", "10116"]
    protein_type_list = ["protein","enzymes", "glycoproteins"]
    sequence_type_list = ["canonical","isoform"]
    site_type_list = ["rwgs", "rwogs", "predicted"]
    t_set_list = [["0"], ["1"], ["2"],["0","1"],["0","2"],["1","2"],["0","1","2"]]
    m_set_list = [["0"], ["1"], ["2"],["0","1"],["0","2"],["1","2"],["0","1","2"]]
    

    backend_obj["protein"]["byproteintype"]["typelist"] = protein_type_list
    backend_obj["protein"]["bysequencetype"]["typelist"] = sequence_type_list
    backend_obj["protein"]["bysitetype"]["typelist"] = site_type_list



    dbh, error_obj = get_mongodb()

    for doc in dbh["c_glycan"].find({}):
        for o in doc["classification"]:
            g_type = o["type"]["name"].lower()
            g_subtype = o["subtype"]["name"].lower()
            if g_type not in glycan_type_list:
                glycan_type_list.append(g_type)
            if g_subtype not in glycan_subtype_list: 
                glycan_subtype_list.append(g_subtype)
        for o in doc["motifs"]:
            motif_name = o["name"].lower()
            if motif_name != "" and motif_name not in motif_list:
                motif_list.append(motif_name)


    for idx_set in t_set_list:
        backend_key = "%s" % ("|".join(idx_set))
        backend_obj["glycan"][backend_key] = 10000000
    
    for tax_id in taxid_list:
        backend_obj["protein"]["total"][tax_id] = 1000000
        backend_obj["protein"]["glycohydrolases"][tax_id] = 1000000
        backend_obj["protein"]["glycosyltransferases"][tax_id] = 1000000
        for idx_set in m_set_list:
            backend_key = "%s_%s" % (tax_id, "|".join(idx_set))
            backend_obj["protein"]["byproteintype"][backend_key] = 10000000
        for seq_type in sequence_type_list:
            backend_key = "%s_%s" % (tax_id, seq_type)
            backend_obj["protein"]["bysequencetype"][backend_key] = 10000000
        for site_type in site_type_list:
            backend_key = "%s_%s" % (tax_id, site_type)
            backend_obj["protein"]["bysitetype"][backend_key] = 10000000
        for g_type in glycan_type_list:
            backend_key = "%s_%s" % (tax_id, g_type)
            backend_obj["glycan"]["byglycantype"][backend_key] = 10000000
            
    for g_type in glycan_type_list:
        for g_subtype in glycan_subtype_list:
            backend_key = "%s_%s" % (g_type, g_subtype)
            backend_obj["glycan"]["byglycantype"][backend_key] = 10000000
    
    for motif_type in motif_list:
        backend_key = "%s" % (motif_type)
        backend_obj["glycan"]["bymotiftype"][backend_key] = 10000000


    return backend_obj



