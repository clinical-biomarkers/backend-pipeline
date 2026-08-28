import os
import string
import random
import hashlib
import json
import datetime,time
import pytz
from collections import OrderedDict
from bson import json_util, ObjectId


from bmkb.db import get_mongodb
from bmkb.util import get_errors_in_query, sort_objects, order_obj, clean_obj, get_paginated_sections, cache_hitlist, transform_query_term, get_hash_id
from bmkb.indexlib import use_indexed_search, parse_sent, get_result_dict_one


def biomarker_search_init(config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("biomarker_searchinit",{}, config_obj)
    if error_list != []:
        return {"error_list":error_list}

    collection = "c_searchinit"
    doc =  dbh[collection].find_one({})
    for f in ["_id"]:
        if f in doc:
            doc.pop(f)

    return doc



def biomarker_detail(query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj


    #Collect errors 
    error_list = get_errors_in_query("biomarker_detail", query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}
    collection = "c_biomarker"




    mongo_query = {"biomarker_id":{"$eq":query_obj["biomarker_id"]}}
    obj = dbh[collection].find_one(mongo_query)
    #check for post-access error, error_list should be empty upto this line
    post_error_list = []
    if obj == None:
        post_error_list.append({"error_code":"non-existent-record"})
        res_obj = {"error_list":post_error_list}
        q = {"biomarker_id":{'$eq': query_obj["biomarker_id"]}}
        history_obj = dbh["c_idtrack"].find_one(q)
        if history_obj != None:
            o = {"type":"unknown","description":"unknown"}
            if "history" in history_obj:
                if "text" in history_obj["history"]:
                    o["description"] = history_obj["history"]["text"] 
                    o["type"] = "discontinued"
                if "replacement_id" in history_obj:
                    o["type"] = "replaced"
                    o["replacement_id_list"] = [history_obj["replacement_id"]] 
            res_obj["reason"] = o
        else:
            res_obj["reason"] = {"type":"invalid","description": "Invalid accession"}
        return res_obj


    #"reason": {"type": "discontinued", "description": "Discontinued in release 3.1.1"}
    #"reason": {"type": "replaced", "description": "Replaced by AN5582-6 as of release 3.1.1",
    #    "replacement_id_list": ["AN5582-6"]
        



    
    if "paginated_tables" in query_obj:
        table_id_list = []
        for o in query_obj["paginated_tables"]:
            if o["table_id"] not in table_id_list:
                table_id_list.append(o["table_id"])
        sec_tables = get_paginated_sections(obj, query_obj, table_id_list, True)
        if "error_list" in sec_tables:
            return sec_tables
        for sec in sec_tables:
            obj[sec] = sec_tables[sec]


    clean_obj(obj, config_obj["removelist"]["c_biomarker"], "c_biomarker")
    #obj["crossref"] = []

    if "condition" in obj:
        if "synonyms" in obj["condition"]:
            obj["condition"].pop("synonyms")


    return obj




def biomarker_search(query_obj, config_obj, original_query):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("biomarker_search", query_obj,config_obj)
    if error_list != []:
        return {"error_list":error_list}




    record_type = "biomarker"
    api_name = "biomarker_search"
    list_id = get_hash_id(api_name, record_type, query_obj)

    #Get cached object
    cache_coll = "c_initcache"
    mongo_query = {"list_id":list_id}
    cached_obj = dbh[cache_coll].find_one(mongo_query)
    if cached_obj == None:
        cache_coll = "c_usercache"
        cached_obj = dbh[cache_coll].find_one(mongo_query)
    
    if cached_obj != None:
        if len(cached_obj["results"]) > 0:
            res = {"list_id":list_id}
            for k in ["query", "resultcount"]:
                if k in cached_obj["cache_info"]:
                    res[k] = cached_obj["cache_info"][k]
            return res


    ts_format = "%Y-%m-%d %H:%M:%S %Z%z"
    ts_list = []
    field2sec = {}
    field2sec = {
        "biomarker_id":"biomarker_id",
        "canonical_id":"biomarker_canonical_id",  
        "biomarker":"biomarker_vocab",
        "biomarker_entity_id":"entity_id",
        "biomarker_entity_name":"entity_name",
        "biomarker_entity_type":"entity_type",
        "best_biomarker_role":"best_biomarker_role",
        "condition_name":"condition_name",
        "condition_id":"condition_id",
        "specimen_id":"specimen_id",
        "specimen_loinc_code":"loinc_code",
        "specimen_name":"specimen_name",
        "publication_id":"publication",
        "keywords":"keywords",
        "data_source":"source_list"
    }




    f_list = []
    for f in  query_obj:
        if f in field2sec:
            f_list.append(f)
    
    debug_list = []
    record_list = []
    for f in f_list:
        sec = field2sec[f]
        val = query_obj[f]
        ts_list.append("1a-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))
        query_obj_new = {"term":val,"term_category":sec}
        quote_flag = False
        for c in ["\"", "\'"]:
            if val[0] == c and val[-1] == c:
                quote_flag = True
        phrase_dict = parse_sent(val, 6, 1)
        result_dict, used_phrase_list = get_result_dict_one(dbh,phrase_dict,[sec],quote_flag,record_type,1,False)
        tmp_list = list(result_dict[sec].keys()) if sec in result_dict else []
        debug_list.append({"f":f, "sec":sec, "resultcount":len(tmp_list)})
        if record_list == []:
            record_list = tmp_list
        else:
            record_list = list(set(record_list).intersection(set(tmp_list))) 
     
    #return debug_list
    #return record_list

    ts_list.append("0-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))


    ts_list.append("1-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))

    ts_format = "%Y-%m-%d %H:%M:%S %Z%z"
    ts = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format)
    cache_coll = "c_usercache"
    list_id = "" if len(record_list) == 0 else list_id
    if len(record_list) != 0:
        cache_info = {
            "query":query_obj,
            "resultcount":len(record_list),
            "ts":ts,
            "record_type":record_type,
            "search_type":"biomarker_search"
        }
        if original_query != "":
            cache_info["ai_parsing"] = {"original_query": original_query, "parsed_parameters": query_obj}
        cache_hitlist(dbh,list_id,record_list,cache_info,cache_coll,config_obj)
    res_obj = {"list_id":list_id, "query":query_obj, "resultcount":len(record_list)}
    #return {"tslist":ts_list, "mong":mongo_query}


    return res_obj




def get_mongo_query(query_obj):


    f_map = {
        "biomarker_id":"biomarker_id",
        "biomarker":"biomarker_component.biomarker",
        "biomarker_entity_name":"biomarker_component.assessed_biomarker_entity.recommended_name",
        "biomarker_entity_id":"biomarker_component.assessed_biomarker_entity_id",
        "biomarker_entity_type":"biomarker_component.assessed_entity_type",
        "specimen_name":"biomarker_component.specimen.name",
        "specimen_id":"biomarker_component.specimen.id",
        "specimen_loinc_code":"biomarker_component.specimen.loinc_code",
        "best_biomarker_role":"best_biomarker_role.role",
        "condition_id":"condition.recommended_name.id",
        "condition_name":"condition.recommended_name.name",
        "publication_id":"citation.reference.id",
        "data_source":"source_list"
    }



                        
    cond_objs = []
    for f in f_map:
        if f in query_obj:
            val = query_obj[f]
            path = f_map[f]
            if f == "condition_id":
                cond_objs.append({"$or":[
                    {"condition.recommended_name.id":{'$eq': val}},
                    {"condition.synonyms.id":{'$eq': val}}
                ]})
            elif f == "condition_name":
                cond_objs.append({"$or":[
                    {"condition.recommended_name.name":{'$regex': val, '$options': 'i'}},
                    {"condition.synonyms.name":{'$regex': val, '$options': 'i'}}
                ]}) 
            elif f in ["biomarker_id","biomarker_entity_id","biomarker_entity_type","specimen_id","best_biomarker_role","publication_id", "data_source"]:
                cond_objs.append({path:{'$eq': val}})
            else:
                cond_objs.append({path:{'$regex': val, '$options': 'i'}})


    operation = query_obj["operation"].lower() if "operation" in query_obj else "and"
    mongo_query = {}
    mongo_query = cond_objs[0] if len(cond_objs) == 1 else mongo_query
    mongo_query = { "$"+operation+"": cond_objs } if len(cond_objs) > 1 else mongo_query

    return mongo_query











def get_simple_mongo_query(query_obj):


    f_map = {
        "biomarker_id":"biomarker_id",
        "biomarker":"biomarker_component.biomarker",
        "biomarker_entity_name":"biomarker_component.assessed_biomarker_entity.recommended_name",
        "biomarker_entity_id":"biomarker_component.assessed_biomarker_entity_id",
        "biomarker_entity_type":"biomarker_component.assessed_entity_type",
        "specimen_name":"biomarker_component.specimen.name",
        "specimen_id":"biomarker_component.specimen.id",
        "specimen_loinc_code":"biomarker_component.specimen.loinc_code",
        "best_biomarker_role":"best_biomarker_role.role",
        "publication_id":"citation.reference.id"
    }


    #query_term = "\"%s\"" % (query_obj["term"])
    query_term = query_obj["term"]
    cond_objs = []
    if query_obj["term_category"] == "any":
        return {'$text': { '$search': query_term}}
    elif query_obj["term_category"] == "biomarker":
        for f in f_map:
            if f in ["condition_id", "condition_name"]:
                continue    
            path = f_map[f]
            cond_objs.append({path:{'$regex': query_term, '$options': 'i'}})   
    elif query_obj["term_category"] == "condition":
        cond_objs = [
            {"condition.recommended_name.id":{'$regex': query_term, '$options': 'i'}},
            {"condition.synonyms.id":{'$regex': query_term, '$options': 'i'}},
            {"condition.recommended_name.name":{'$regex': query_term, '$options': 'i'}},
            {"condition.synonyms.name":{'$regex': query_term, '$options': 'i'}}
        ]

    mongo_query = {} if cond_objs == [] else { "$or": cond_objs }

    return mongo_query



