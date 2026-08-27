import os,sys
import csv
import json
import traceback
import pymongo
from flask import (current_app)
from bmkb.db import get_mongodb, log_error, next_sequence_value
from collections import OrderedDict
import datetime




def get_one(req_obj):

    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, "conf/config.json")
    config_obj = json.load(open(json_url))

    try:
        mongo_dbh, error_obj = get_mongodb()
        if error_obj != {}:
            return error_obj
        if "coll" not in req_obj:
            return {"status":0, "error":"no collection specified"}
        if req_obj["coll"] not in config_obj["collinfo"]:
            return {"status":0, "error":"unknown collection name"}
        
        init_obj = mongo_dbh["c_init"].find_one({})

        coll_name =  req_obj["coll"]
        prj_obj = config_obj["collinfo"][coll_name]["get_one"]["prj"]
        qf_dict = config_obj["collinfo"][coll_name]["get_one"]["queryfields"]
        qry_obj = get_mongo_query(qf_dict, req_obj)
        if "error" in qry_obj:
            return qry_obj
        #return {"error":"xxxxx", "query":qry_obj, "qf":qf_dict}

        res_obj = {"status":1}
        doc = {}
        if prj_obj != {}:
            doc = mongo_dbh[coll_name].find_one(qry_obj, prj_obj)
        else:
            doc = mongo_dbh[coll_name].find_one(qry_obj)
        if doc == None:
            msg = "No '%s' record found for your query" % (coll_name)
            #return {"status":0, "error":msg, "query":qry_obj}
            return {"status":0, "error":msg}
        
        for k in ["_id", "password"]:
            if k in doc:
                doc.pop(k)
        for k in ["createdts", "modifiedts"]:
            if k in doc:
                ts_format = "%Y-%m-%d %H:%M:%S %Z%z"
                doc[k] = doc[k].strftime(ts_format)
        res_obj["record"] = doc
        #res_obj["query"] = req_obj
    except Exception as e:
        res_obj =  log_error(traceback.format_exc())

    return res_obj


def delete_one(req_obj):

    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, "conf/config.json")
    config_obj = json.load(open(json_url))

    try:
        mongo_dbh, error_obj = get_mongodb()
        if error_obj != {}:
            return error_obj
        if "coll" not in req_obj:
            return {"status":0, "error":"no collection specified"}
        if req_obj["coll"] not in config_obj["collinfo"]:
            return {"status":0, "error":"unknown collection name"}
        init_obj = mongo_dbh["c_init"].find_one({})
        coll_name =  req_obj["coll"]
        res_obj = {"status":0}
        req_obj.pop("coll")
        res = mongo_dbh[coll_name].delete_one(req_obj)
        doc = mongo_dbh[coll_name].find_one(req_obj)
        if doc == None:
            res_obj["status"] = 1

    except Exception as e:
        res_obj =  log_error(traceback.format_exc())

    return res_obj



def get_many(req_obj):

    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, "conf/config.json")
    config_obj = json.load(open(json_url))

    try:
        mongo_dbh, error_obj = get_mongodb()
        if error_obj != {}:
            return error_obj
        if "coll" not in req_obj:
            return {"status":0, "error":"no collection specified"}
        if req_obj["coll"] not in config_obj["collinfo"]:
            return {"status":0, "error":"unknown collection name"}

        init_obj = mongo_dbh["c_init"].find_one({})
        
        coll_name =  req_obj["coll"]
        prj_obj = config_obj["collinfo"][coll_name]["get_many"]["prj"]
        sort_field = ""
        if "sortfield" in config_obj["collinfo"][coll_name]["get_many"]:
            sort_field = config_obj["collinfo"][coll_name]["get_many"]["sortfield"]

        qf_dict = config_obj["collinfo"][coll_name]["get_many"]["queryfields"]
        qry_obj = get_mongo_query(qf_dict, req_obj)
        if "error" in qry_obj:
            return qry_obj

        #return {"error":"xxx", "qry":qry_obj} 


        #####
        max_batch_size = config_obj["collinfo"][coll_name]["max_batch_size"]
        batch_size = req_obj["limit"] if "limit" in req_obj else max_batch_size
        batch_size = max_batch_size if batch_size > max_batch_size else batch_size
        offset = req_obj["offset"] - 1 if "offset" in req_obj else 0
        skips = batch_size * offset

        res_obj = {"status":1,  "coll":coll_name, "recordlist":[]}
        doc_list = []
        prj_obj["_id"] = 0
        cur = mongo_dbh[coll_name].find(qry_obj, prj_obj)
        total = cur.count()
        #cur = mongo_dbh[coll_name].find(qry_obj, prj_obj).limit(batch_size).skip(skips)
        cur = cur.limit(batch_size).skip(skips)

        cur = cur.sort([(sort_field, pymongo.DESCENDING)]) if sort_field != "" else cur
        doc_list = list(cur)

        for doc in doc_list:
            for k in ["_id", "password"]:
                if k in doc:
                    doc.pop(k)
            for k in ["createdts", "modifiedts"]:
                if k in doc:
                    ts_format = "%Y-%m-%d %H:%M:%S %Z%z"
                    if type(doc[k]) is not str:
                        doc[k] = doc[k].strftime(ts_format)
            else:
                res_obj["recordlist"].append(doc)
        res_obj["query"] = req_obj
        res_obj["summary"] = {
            "total":total,
            "batchsize":batch_size,
            "offset":offset + 1
        }
    except Exception as e:
        res_obj =  log_error(traceback.format_exc())

    return res_obj




def get_mongo_query(qf_dict, req_obj):

    tmp_list_one = []
    for f in qf_dict:
        qf_obj = qf_dict[f]
        if qf_obj["required"] == True and f not in req_obj:
            msg = "field=%s is required query field"%(f)
            return {"status":0, "error":msg}
        if f in req_obj:
            query_val = req_obj[f].strip()
            if f == "query" and query_val == "":
                continue
            query_val = int(query_val) if qf_obj["datatype"] == "int" else query_val
            query_val = float(query_val) if qf_obj["datatype"] == "float" else query_val
            tmp_list_two = []
            for p_obj in qf_obj["pathlist"]:
                o = {p_obj["path"]:{p_obj["operator"]:query_val}}
                if p_obj["operator"] == "$regex":
                    o = {p_obj["path"]:{p_obj["operator"]:query_val, "$options":"i"}}
                tmp_list_two.append(o)
            tmp_list_one.append({qf_obj["junction"]:tmp_list_two})

    o = {"$and":tmp_list_one} if tmp_list_one != [] else {}
    return o




def order_json_obj(json_obj, ordr_dict):

    for k1 in json_obj:
        ordr_dict[k1] = ordr_dict[k1] if k1 in ordr_dict else 1000
        if type(json_obj[k1]) is dict:
            for k2 in json_obj[k1]:
                ordr_dict[k2] = ordr_dict[k2] if k2 in ordr_dict else 1000
                if type(json_obj[k1][k2]) is dict:
                    for k3 in json_obj[k1][k2]:
                        ordr_dict[k3] = ordr_dict[k3] if k3 in ordr_dict else 1000
                    json_obj[k1][k2] = OrderedDict(sorted(json_obj[k1][k2].items(),key=lambda x: float(ordr_dict.get(x[0]))))
                elif type(json_obj[k1][k2]) is list:
                    for j in range(0, len(json_obj[k1][k2])):
                        if type(json_obj[k1][k2][j]) is dict:
                            for k3 in json_obj[k1][k2][j]:
                                ordr_dict[k3] = ordr_dict[k3] if k3 in ordr_dict else 1000
                                for kk in json_obj[k1][k2][j].keys():
                                    ordr_dict[kk] = ordr_dict[kk] if kk in ordr_dict else 1000
                                keyList = sorted(json_obj[k1][k2][j].keys(), key=lambda x: float(ordr_dict[x]))
                                json_obj[k1][k2][j] = OrderedDict(sorted(json_obj[k1][k2][j].items(), key=lambda x: float(ordr_dict.get(x[0]))))
            json_obj[k1] = OrderedDict(sorted(json_obj[k1].items(),key=lambda x: float(ordr_dict.get(x[0]))))

    return OrderedDict(sorted(json_obj.items(), key=lambda x: float(ordr_dict.get(x[0]))))





def insert_one(req_obj):

    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, "conf/config.json")
    config_obj = json.load(open(json_url))

    if "recaptcha_token" in req_obj:
        recaptcha_token = req_obj["recaptcha_token"]
        ver_obj = verify_recaptcha(recaptcha_token)
        if ver_obj != {}:
            return ver_obj

    try:
        mongo_dbh, error_obj = get_mongodb()
        if error_obj != {}:
            return error_obj
        if "coll" not in req_obj:
            return {"status":0, "error":"no collection specified"}
        if req_obj["coll"] not in config_obj["collinfo"]:
            return {"status":0, "error":"unknown collection name"}

        res_obj = {"status": 1, "error":""}
        coll_name = req_obj["coll"]
        sequence_name = "%s.id" % (coll_name)
        primary_id = config_obj["collinfo"][coll_name]["primaryid"]
        doc = req_obj["record"]
        doc[primary_id] = next_sequence_value(mongo_dbh["c_counter"], sequence_name)
        doc["createdts"] = datetime.datetime.now()
        doc["modifiedts"] = doc["createdts"]
        if coll_name == "c_glycan":
            pid_str = str(doc[primary_id])
            doc["gsa_id"] = "GSA000000000"[0:9-len(str(pid_str))] + pid_str
            doc["sort_score"] = int(doc[primary_id])

        res = mongo_dbh[coll_name].insert_one(doc)
        for k in ["_id", "password"]:
            if k in doc:
                doc.pop(k)
        for k in ["createdts", "modifiedts"]:
            if k in doc:
                ts_format = "%Y-%m-%d %H:%M:%S %Z%z"
                doc[k] = doc[k].strftime(ts_format)
        res_obj["record"] = doc
        res_obj["query"] = req_obj
    except Exception as e:
        res_obj =  log_error(traceback.format_exc())

    return res_obj



def update_one(coll_name, qry_obj, update_obj):


    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, "conf/config.json")
    config_obj = json.load(open(json_url))

    try:
        mongo_dbh, error_obj = get_mongodb()
        if error_obj != {}:
            return error_obj
        res_obj = {"status": 1, "error":""}
        update_obj["modifiedts"] = datetime.datetime.now()
        res = mongo_dbh[coll_name].update_one(qry_obj, {"$set":update_obj})
        doc = mongo_dbh[coll_name].find_one(qry_obj)
        for k in ["_id", "password"]:
            if k in doc:
                doc.pop(k)
        for k in ["createdts", "modifiedts"]:
            if k in doc:
                ts_format = "%Y-%m-%d %H:%M:%S %Z%z"
                doc[k] = doc[k].strftime(ts_format)
        res_obj["record"] = doc
        #res_obj["query"] = {}

    except Exception as e:
        res_obj =  log_error(traceback.format_exc())

    return res_obj
