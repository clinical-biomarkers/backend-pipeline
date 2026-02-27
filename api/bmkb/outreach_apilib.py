import os
import string
import random
import hashlib
import json
import datetime,time
import bcrypt
import base64
import pytz
from collections import OrderedDict
from bson.objectid import ObjectId


from bmkb.db import get_mongodb
from bmkb.util import get_errors_in_query, sort_objects




def outreach_addnew(logged_user, query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    #for obj in query_obj:
    #    error_list = get_errors_in_query("outreach_addnew",obj, config_obj)
    #    if error_list != []:
    #        return {"error_list":error_list}

    #check write-access
    user_info = dbh["c_users"].find_one({'email' : logged_user})
    if "access" not in user_info:
        return {"error_list":[{"error_code":"no-write-access"}]}
    if user_info["access"] != "write":
        return {"error_list":[{"error_code":"no-write-access"}]}


    max_job_id = 0
    if dbh["c_outreach"].find_one({"id":1}) != None:
        agg_obj = {"$group":{"_id":"","max_id":{"$max":"$id"}}}
        res = list(dbh["c_outreach"].aggregate([agg_obj]))
        max_job_id = res[0]["max_id"]


    res_obj = {}
    try:
        ts = datetime.datetime.now()
        idx = 1
        for doc in query_obj:
            doc["createdts"] = ts
            doc["visibility"] = "visible"
            doc["id"] = max_job_id + idx
            res = dbh["c_outreach"].insert_one(doc)
            idx += 1
        res_obj = {"type":"success"}
    except Exception as e:
        res_obj = {"error_list":[{"error_code":str(e)}]}

    return res_obj



def outreach_update(logged_user, query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    #error_list = get_errors_in_query("outreach_update",query_obj, config_obj)
    #if error_list != []:
    #    return {"error_list":error_list}
        
    #check write-access
    user_info = dbh["c_users"].find_one({'email' : logged_user})
    if "access" not in user_info:
        return {"error_list":[{"error_code":"no-write-access"}]}
    if user_info["access"] != "write":
        return {"error_list":[{"error_code":"no-write-access"}]}


    res_obj = {}
    try:
        ts = datetime.datetime.now()
        for doc in query_obj:
            if "id" not in doc:
                return {"error_list":[{"error_code":"missing-required-field (id)"}]}
            q_obj = {"id":doc["id"]}
            res = dbh["c_outreach"].find_one(q_obj)
            if res == None:
                return {"error_list":[{"error_code":"record-not-found(id=%s)" % (doc["id"])}]}

            doc["updatedts"] = ts
            update_obj = doc
            update_obj.pop("id")
            res = dbh["c_outreach"].update_one(q_obj, {'$set':update_obj}, upsert=True)
    except Exception as e:
        res_obj = {"error_list":[{"error_code":str(e)}]}

    return res_obj

    




def outreach_list(query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    #error_list = get_errors_in_query("outreach_list",query_obj, config_obj)
    #if error_list != []:
    #    return {"error_list":error_list}


    import pymongo
    res_obj = []
    try:
        cond_list = []
        cond_list.append({"visibility":{"$eq":"visible"}})
        q_obj = {"$and":cond_list}
        doc_list = dbh["c_outreach"].find(q_obj).sort('createdts', pymongo.DESCENDING)
        for doc in doc_list:
            doc.pop("_id")
            for k in ["createdts", "updatedts", "start_date", "end_date"]:
                if k in doc:
                    doc[k] = str(doc[k])
            res_obj.append(doc)
    except Exception as e:
        res_obj = {"error_list":[{"error_code":str(e)}]}


    return res_obj




