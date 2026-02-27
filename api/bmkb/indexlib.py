import os
import random
import hashlib
import json
import datetime,time
import pytz
from bmkb.db import get_mongodb
from bmkb.util import  get_errors_in_query, get_random_string, cache_hitlist, get_hash_id







def parse_glycan_seq(phrase_dict, seq_type, seq, max_word_count, min_word_count):

    if seq.strip() == "":
        return

    s_dict = {
        "byonic":")", "iupac":")", "inchi":")"
    }

    tmp_w_list = seq.split(" ")
    for s_type in s_dict:
        tmp_w_list = seq.split(s_dict[s_type])
        for j in range(0, len(tmp_w_list) - 1):
            tmp_w_list[j] = tmp_w_list[j] + s_dict[s_type]

    for j in range(0, len(tmp_w_list)):
        tmp_w_list[j] = tmp_w_list[j].lower().replace(",", " ")
        tmp_w_list[j] = tmp_w_list[j].replace("-", " ").replace(";", " ")
        tmp_w_list[j] = tmp_w_list[j].replace("(", " ").replace(")", " ")
        tmp_w_list[j] = tmp_w_list[j].replace("[", " ").replace("]", " ")

    w_list = []
    for w in tmp_w_list:
        w_list += w.strip().split(" ")

    word_count = len(w_list) + 1
    word_count = max_word_count if word_count > max_word_count else word_count



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
                p = " ".join(l)
                if len(p) == 1:
                    continue
                phrase_dict[p] = True
                #print (len(p), seq_type, "phrase", p)

    #print (json.dumps(phrase_dict, indent=4))

    return



def parse_sent(s,  max_word_count, min_word_count):

    tmp_dict = {}
    if s.strip() == "":
        return
    s = s.lower().replace(",", " ").replace("-", " ").replace(";", " ")
    s = s.replace("(", " ").replace(")", " ").replace("[", " ").replace("]", " ")
    w_list = s.strip().split(" ")

    word_count = len(w_list) + 1
    word_count = max_word_count if word_count > max_word_count else word_count
    for wlen in range(0, word_count + 1):
        if wlen > len(w_list):
            continue
        for i in range(0, len(w_list)):
            l = []
            for ww in w_list[i:i+wlen]:
                ww = ww.strip()
                if ww != "":
                    l.append(ww)
            if len(l) >= min_word_count:
                phrase = " ".join(l)
                if len(phrase) == 1:
                    continue
                tmp_dict[phrase] = True
    phrase_dict = {}
    for phrase in tmp_dict:
        n = len(phrase.split(" "))
        phrase_dict[n] = phrase
    return phrase_dict


def get_termcat2sec_dict(record_type):

    tmp_dict = {
        "biomarker":{
            "biomarker":["biomarker_id","entity_id", "entity_name","biomarker_vocab"],
            "condition":["condition_id","condition_name"]
        }
    }
 
    ret_obj = {}
    if record_type in tmp_dict:
        term_cat_list = list(tmp_dict[record_type].keys())
        for term_cat in term_cat_list:
            for sec in tmp_dict[record_type][term_cat]:
                if sec not in tmp_dict[record_type]:
                    tmp_dict[record_type][sec] = [sec]

        ret_obj = tmp_dict[record_type]

    return ret_obj

def get_result_dict_all(dbh, phrase_dict,  quote_flag, query_obj, max_p):

    exact_match_obj_list = []
    seen_exact_match = {}
    prj_obj = {"record_type":1, "record_id":1, "section":1, "glycoflag":1}
    result_dict = {}
    hit_count = 0
    i = 0
    for word_count in sorted(phrase_dict, reverse=True):
        i += 1
        #if i > max_p:
        #    break
        if hit_count > 0:
            break
        phrase = phrase_dict[word_count]
        if quote_flag:
            for c in ["\"", "\'"]:
                phrase = phrase.replace(c, "")
        qry_obj = {"phraselist":{"$eq":phrase}}
        for doc in dbh["c_index"].find(qry_obj, prj_obj):
            hit_count += 1
            record_id, sec = doc["record_id"], doc["section"]
            glyco_flag = False
            glyco_flag = doc["glycoflag"] if "glycoflag" in doc else glyco_flag
            record_type_list = [doc["record_type"]]
            if glyco_flag == True:
                record_type_list.append("glycoprotein")
            for record_type in record_type_list:
                if record_type not in result_dict:
                    result_dict[record_type] = {"all":{}}
                result_dict[record_type]["all"][record_id] = word_count
                if sec not in result_dict[record_type]:
                    result_dict[record_type][sec] = {}
                result_dict[record_type][sec][record_id] = word_count
                record_id_list = [record_id.lower()]
                if record_type in ["protein"]:
                    record_id_list = [record_id.split("-")[0].lower()]
                if query_obj["term"].lower() in record_id_list:
                    if record_id not in seen_exact_match:
                        exact_obj = {"id":record_id, "type":record_type, "name":record_id}
                        exact_match_obj_list.append(exact_obj)
                        seen_exact_match[record_id] = True
            if quote_flag:
                break    


    return result_dict, exact_match_obj_list


def get_result_dict_one(dbh, phrase_dict, selected_sections, quote_flag, record_type, max_p, debug_flag):
 
    debug_list = [] 
    result_dict = {"all":{}}
    prj_obj = {"record_type":1, "record_id":1, "section":1}
    i = 0
    used_phrase_list = []
    hit_count = 0
    for word_count in sorted(phrase_dict, reverse=True):
        i += 1
        #if i > max_p:
        #    break
        if hit_count > 0:
            break
        phrase = phrase_dict[word_count]
        if quote_flag:
            for c in ["\"", "\'"]:
                phrase = phrase.replace(c, "")
        used_phrase_list.append(phrase)
        qry_obj = {"phraselist":{"$eq":phrase}, "record_type":{"$eq":record_type}}
        n1, n2 = 0, 0
        ignored_sec_list = []
        for doc in dbh["c_index"].find(qry_obj, prj_obj):
            hit_count += 1
            n1 += 1
            record_type, record_id, sec = doc["record_type"], doc["record_id"], doc["section"]
            #if we are doing term_category != "any"
            if selected_sections != [] and sec not in selected_sections:
                ignored_sec_list.append(sec)
                continue
            n2 += 1
            result_dict["all"][record_id] = word_count
            if sec not in result_dict:
                result_dict[sec] = {}
            result_dict[sec][record_id] = word_count
        if result_dict["all"] != {} or quote_flag:
        #if quote_flag:
            break
        ignored_sec_list = list(set(ignored_sec_list))
        debug_list.append({"mongo_query":qry_obj, "n1":n1, "n2":n2, "ignored":ignored_sec_list})
    if debug_flag:
        return debug_list
    return result_dict, used_phrase_list








def search_one(api_name, query_obj, config_obj, cache_flag, exact_match_flag):


    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors
    error_list = get_errors_in_query(api_name, query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}

    record_type = api_name.split("_")[0]
   

    list_id = get_hash_id(api_name, record_type, query_obj)
    
    #Get cached object
    cache_coll = "c_initcache"
    mongo_query = {"list_id":list_id}
    cached_obj = dbh[cache_coll].find_one(mongo_query)
    if cached_obj == None:
        cache_coll = "c_usercache"
        cached_obj = dbh[cache_coll].find_one(mongo_query)    
   
    if cache_flag and cached_obj != None:
        if len(cached_obj["results"]) > 0:
            return {"list_id":list_id, "resultcount":cached_obj["cache_info"]["total"], "query":query_obj }

    res_obj = {"query":query_obj}
    query_obj["term"] = query_obj["term"].strip()
    quote_flag = False
    for c in ["\"", "\'"]:
        if query_obj["term"][0] == c and query_obj["term"][-1] == c:
            quote_flag = True

    term_category = query_obj["term_category"]
    selected_sections = []
    if term_category != "any":
        tmp_dict = get_termcat2sec_dict(record_type)
        if term_category in tmp_dict:
            selected_sections = tmp_dict[term_category]

    phrase_dict = parse_sent(query_obj["term"], 6, 1)
    max_p = 1 if exact_match_flag else len(phrase_dict.keys())
    result_dict, used_phrase_list = get_result_dict_one(dbh,phrase_dict,selected_sections,quote_flag,record_type,max_p,False)
    #return {"usedphrases":used_phrase_list, "phrase_dict":phrase_dict, "resultdict":result_dict, "selected_sections":selected_sections}
    #xxxx = get_result_dict_one(dbh,phrase_dict,selected_sections,quote_flag,record_type,max_p,True)
    #return xxxx


    section_list = selected_sections if selected_sections != [] else ["all"]
    debug_list = []
    cache_collection = "c_usercache"
    ts = datetime.datetime.now(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d %H:%M:%S %Z%z")
    record_list = []
    for sec in section_list:
        tmp_dict = result_dict[sec] if sec in result_dict else {}
        s_tmp_dict = sorted(tmp_dict.items(), key=lambda item: item[1], reverse=True)
        record_list += [s[0] for s in s_tmp_dict]

    record_list = sorted(set(record_list))
    res = dbh[cache_collection].delete_many({"list_id":list_id})
    result_count = len(record_list)
    query_obj["term"] = query_obj["term"].replace("\\(", "(").replace("\\)",")")
    query_obj["term"] = query_obj["term"].replace("\\[", "[").replace("\\]","]")
    cache_info = {
        "query":query_obj,
        "ts":ts,
        "record_type":record_type,
        "search_type":api_name,
        "total":result_count
    }
    cache_hitlist(dbh,list_id,record_list,cache_info,cache_collection,config_obj)
    debug_list.append("%s|%s" % (list_id,result_count))
    res_obj["list_id"] = list_id if result_count > 0 else ""
    res_obj["resultcount"] = result_count
    #res_obj["debug"] = debug_list

    return res_obj
    



def search_all(api_name, query_obj, config_obj):


    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj


    #Collect errors
    error_list = get_errors_in_query(api_name, query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}




    res_obj = { "exact_match": [], "other_matches": {"total_match_count":0}}
    record_type_list = ["protein", "site", "glycoprotein", "gene", "glycan", "motif", "biomarker", "disease"]
    for record_type in record_type_list:
        res_obj["other_matches"][record_type] = {}
        for sec in ["all"]:
            res_obj["other_matches"][record_type][sec] = {"list_id":"", "count":0}

    query_obj["term"] = query_obj["term"].strip()
    quote_flag = False
    for c in ["\"", "\'"]:
        if query_obj["term"][0] == c and query_obj["term"][-1] == c:
            quote_flag = True

    phrase_dict = parse_sent(query_obj["term"], 6, 1)

    #return phrase_dict
   
    max_p = 1 
    result_dict, res_obj["exact_match"] = get_result_dict_all(dbh, phrase_dict,quote_flag,query_obj,max_p)
    #return result_dict

 
    if result_dict == {}:
        seq_type_list = ["byonic","glycoct", "iupac", "inchi"]
        tmp_phrase_dict = {}
        for seq_type in seq_type_list:
            parse_glycan_seq(tmp_phrase_dict, seq_type, query_obj["term"], 15, 5)
        phrase_dict = {}
        for phrase in tmp_phrase_dict:
            n = len(phrase.split(" "))
            phrase_dict[n] = phrase
        result_dict, res_obj["exact_match"] = get_result_dict_all(dbh,phrase_dict,quote_flag,query_obj,max_p)   

    #return {"resultdict":result_dict}

    debug_list = []
    cache_collection = "c_usercache"
    ts = datetime.datetime.now(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d %H:%M:%S %Z%z")
    for record_type in result_dict:
        for sec in ["all"]:
            sec_qry = {"record_type":record_type, "sec":sec, "query":query_obj}
            list_id = get_hash_id("globalsearch_search", "all", sec_qry)
            tmp_dict = result_dict[record_type][sec]
            s_tmp_dict = sorted(tmp_dict.items(), key=lambda item: item[1], reverse=True)
            record_list = [s[0] for s in s_tmp_dict]
            res = dbh[cache_collection].delete_many({"list_id":list_id})
            result_count = len(record_list)
            query_obj["term"] = query_obj["term"].replace("\\(", "(").replace("\\)",")")
            query_obj["term"] = query_obj["term"].replace("\\[", "[").replace("\\]","]")
            r_type = "protein" if record_type == "glycoprotein" else record_type
            cache_info = {
                "query":query_obj,
                "ts":ts,
                "record_type":r_type,
                "search_type":api_name
            }
            cache_hitlist(dbh,list_id,record_list,cache_info,cache_collection,config_obj)
            res_obj["other_matches"][record_type][sec] = {"list_id":list_id,"count":result_count}
            #res_obj["other_matches"][record_type][sec]["recordlist"] = record_list
            res_obj["other_matches"]["total_match_count"] += result_count
            debug_list.append({"record_type":record_type, "sec":sec})

    #return debug_list

    return res_obj



def use_indexed_search(api_name, req_obj,config_obj, exact_match_flag):

    cache_flag = True
    res_obj = search_one(api_name, req_obj, config_obj, cache_flag, exact_match_flag)
    #for p in ["query", "resultcount"]:
    #    if p in res_obj:
    #        res_obj.pop(p)
    
    return res_obj

