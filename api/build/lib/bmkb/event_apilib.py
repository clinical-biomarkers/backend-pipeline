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
from bmkb.util import get_errors_in_query, sort_objects, cache_hitlist




def event_addnew(logged_user, query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("event_addnew",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}

    error_list = []
    for k in ["start_date", "end_date"]:
        date_parts = query_obj[k].strip().split(" ")[0].strip().split("/")
        time_parts = query_obj[k].strip().split(" ")[1].strip().split(":")
        if len(date_parts) != 3:
            error_list.append({"error_code":"invalid-date-format for %s" % (k)})
        elif len(time_parts) != 3:
            error_list.append({"error_code":"invalid-time-format for %s" % (k)})
        else:
            for j in range(0, len(date_parts)):
                if date_parts[j].isdigit() == False:
                    error_list.append({"error_code":"invalid-date-format for %s" % (k)})
                elif time_parts[j].isdigit() == False:
                    error_list.append({"error_code":"invalid-time-format for %s" % (k)})
                else:
                    date_parts[j] = int(date_parts[j])
                    time_parts[j] = int(time_parts[j])

            if error_list == []:
                if date_parts[0] < 1 or date_parts[0] > 12:
                    error_list.append({"error_code":"invalid-month-value in %s" % (k)})
                if date_parts[1] < 1 or date_parts[1] > 31:
                    error_list.append({"error_code":"invalid-day-value in %s" % (k)})
                if date_parts[2] < 2021:
                    error_list.append({"error_code":"invalid-year-value in %s" % (k)})
                if time_parts[0] < 0 or time_parts[0] > 23:
                    error_list.append({"error_code":"invalid-hour-value in %s" % (k)})
                if time_parts[1] < 0 or time_parts[1] > 59:
                    error_list.append({"error_code":"invalid-minute-value in %s" % (k)})
                if time_parts[2] < 0 or time_parts[2] > 59:
                    error_list.append({"error_code":"invalid-second-value in %s" % (k)})
        if error_list == []:
            dt, tm = query_obj[k].split(" ")[0], query_obj[k].split(" ")[1]
            mm, dd, yy = dt.split("/")
            hr, mn, sc = tm.split(":")
            seconds = int(yy)*365*24*3600 + int(mm)*31*24*3600 + int(dd)*1*24*3600 + int(hr)*1*3600 + int(mn)*60 + int(sc)
            query_obj[k + "_s"] = seconds
            query_obj[k] = datetime.datetime.strptime(query_obj[k],"%m/%d/%Y %H:%M:%S")
                

    if error_list != []:
        return {"error_list":error_list}


    #check write-access
    user_info = dbh["c_users"].find_one({'email' : logged_user})
    if "access" not in user_info:
        return {"error_list":[{"error_code":"no-write-access"}]}
    if user_info["access"] != "write":
        return {"error_list":[{"error_code":"no-write-access"}]}

    res_obj = {}
    try:
        query_obj["createdts"] = datetime.datetime.now(pytz.timezone('US/Eastern'))
        query_obj["updatedts"] = query_obj["createdts"]
        res = dbh["c_event"].insert_one(query_obj)
        res_obj = {"type":"success"}
    except Exception as e:
        res_obj = {"error_list":[{"error_code":str(e)}]}

    return res_obj


    
def event_detail(query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("event_detail",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}
   

    res_obj = {}
    try:
        q_obj = {"_id":ObjectId(query_obj["id"])}
        res_obj = dbh["c_event"].find_one(q_obj)
        if res_obj == None:
            return {"error_list":[{"error_code":"record-not-found"}]}
        res_obj["id"] = str(res_obj["_id"])
        res_obj.pop("_id")
        for k in ["createdts", "updatedts", "start_date", "end_date"]:
            if k not in res_obj:
                continue
            res_obj[k] = res_obj[k].strftime('%Y-%m-%d %H:%M:%S %Z%z')
    except Exception as e:
        res_obj = {"error_list":[{"error_code":str(e)}]}

    return res_obj


def event_list(query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("event_list",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}

    now_est = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime('%m/%d/%Y %H:%M:%S')
    dt, tm = now_est.split(" ")[0], now_est.split(" ")[1]
    mm, dd, yy = dt.split("/")
    hr, mn, sc = tm.split(":")
    seconds = int(yy)*365*24*3600 + int(mm)*31*24*3600 + int(dd)*1*24*3600 + int(hr)*1*3600 + int(mn)*60 + int(sc)
            

    

    import pymongo
    res_obj = []
    try:
        cond_list = []
        if query_obj["visibility"] != "all":
            cond_list.append({"visibility":{"$eq":query_obj["visibility"]}})
        if "status" in query_obj:
            if query_obj["status"] == "current":
                cond_list.append({"start_date_s":{"$lte":seconds}})
                cond_list.append({"end_date_s":{"$gte":seconds}})
        q_obj = {} if cond_list == [] else  {"$and":cond_list}
        doc_list = dbh["c_event"].find(q_obj).sort('createdts', pymongo.DESCENDING)
        for doc in doc_list:
            if "title" not in doc:
                continue
            if "start_date_s" not in doc:
                continue
            doc["id"] = str(doc["_id"])
            doc.pop("_id")
            for k in ["now_est", "now_utc", "createdts", "updatedts", "start_date", "end_date"]:
                if k not in doc:
                    continue
                doc[k] = doc[k].strftime('%Y-%m-%d %H:%M:%S %Z%z')
            doc["now_ts"] = seconds
            res_obj.append(doc)
    except Exception as e:
        res_obj = {"error_list":[{"error_code":str(e)}]}

 
    return res_obj


def event_update(logged_user, query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("event_update",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}


    #check write-access
    user_info = dbh["c_users"].find_one({'email' : logged_user})
    if "access" not in user_info:
        return {"error_list":[{"error_code":"no-write-access"}]}
    if user_info["access"] != "write":
        return {"error_list":[{"error_code":"no-write-access"}]}

    res_obj = {}
    try: 
        q_obj = {"_id":ObjectId(query_obj["id"])}
        update_obj = {}
        for k in query_obj:
            if k not in ["id"]:
                update_obj[k] = query_obj[k]
        res = dbh["c_event"].update_one(q_obj, {'$set':update_obj}, upsert=True)
        res_obj = {"type":"success"}
    except Exception as e:
        res_obj = {"error_list":[{"error_code":str(e)}]}


    return res_obj



def event_delete(logged_user, query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("event_delete",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}


    #check write-access
    user_info = dbh["c_users"].find_one({'email' : logged_user})
    if "access" not in user_info:
        return {"error_list":[{"error_code":"no-write-access"}]}
    if user_info["access"] != "write":
        return {"error_list":[{"error_code":"no-write-access"}]}


    res_obj = {}
    try:
        q_obj = {"_id":ObjectId(query_obj["id"])}
        doc = dbh["c_event"].find_one(q_obj)
        if doc == None:
            res_obj =  {"error_list":[{"error_code":"record-not-found"}]}
        else:
            update_obj = {"visibility":"hidden"}
            res = dbh["c_event"].update_one(q_obj, {'$set':update_obj}, upsert=True)
            res_obj = {"type":"success"}
    except Exception as e:
        res_obj = {"error_list":[{"error_code":str(e)}]}

    return res_obj


