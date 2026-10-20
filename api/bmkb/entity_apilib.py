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


    
def entity_detail(query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("entity_detail",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}
   
    ref_id = query_obj["ref_id"].upper().replace("_",":")
    entity_id = query_obj["entity_id"].upper().replace("_",":") if "entity_id" in query_obj else ""
 
    res_obj = {}
    try:
        q_obj = {"hgnc_id":ref_id} if ref_id.find("HGNC:") != -1 else {"ref_id":ref_id}
        res_obj = dbh["c_ent"].find_one(q_obj)
        if res_obj == None:
            return {"error_list":[{"error_code":"record-not-found"}]}
        if "_id" in res_obj:
            res_obj.pop("_id")
    except Exception as e:
        res_obj = {"error_list":[{"error_code":str(e)}]}


    res_obj["entity"] = res_obj["entities"][0] if len(res_obj["entities"]) > 0 else {}
    entity_id_list = []
    for obj in res_obj["entities"]:
        if obj["entity_id"].lower() == entity_id.lower():
            res_obj["entity"] = obj
        entity_id_list.append(obj["entity_id"])

    q = {"record_id": res_obj["ref_id"]}
    idx = 0
    for batch_doc in dbh["c_batch"].find(q):
        for obj in batch_doc["sections"]["entities"]:
            if idx == 0 and res_obj["entity"] == {}:
                 res_obj["entity"] = obj
            idx += 1
            if obj["entity_id"].lower() == entity_id.lower():
                res_obj["entity"] = obj
            entity_id_list.append(obj["entity_id"])

    res_obj["entity_id_list"] = entity_id_list
    res_obj.pop("entities")

    #return {"entity_id":res_obj["entity"]["entity_id"], "n":res_obj["entity_id_list"], "first":entity_id_list[0]}
    return res_obj




