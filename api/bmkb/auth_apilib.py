import os
import string
import random
import hashlib
import json
import datetime,time
import bcrypt
import base64
import pytz
import requests
from collections import OrderedDict
from bson.objectid import ObjectId

from flask import (request, current_app)

import smtplib
from email.mime.text import MIMEText

from bmkb.db import get_mongodb
from bmkb.util import clean_obj, extract_name, get_errors_in_query, get_random_string



def make_hash_string():
    m = hashlib.md5()
    s = str(time.time())
    m.update(s.encode('utf-8'))
    s = str(os.urandom(64))
    m.update(s.encode('utf-8'))

    s = base64.encodestring(m.digest())[:-3]
    s = str(s).replace('/', '$')
    s = s.replace("+", "$")
    return s.decode()




def auth_userid(config_obj):
    
    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("auth_userid",{}, config_obj)
    if error_list != []:
        return {"error_list":error_list}
    collection = "c_userid"
    res_obj = {}
    i = 0
    while True:
        user_id = get_random_string(32).lower()
        user_obj = {"userid":user_id}
        doc_list = list(dbh[collection].find(user_obj))
        if len(doc_list) == 0:
            ts = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S %Z%z')
            user_obj["created_ts"] = ts
            result = dbh[collection].insert_one(user_obj)
            return {"user":user_id}
        if i > 100000:
            return {"error_list":[{"error_code":"userid-generator-failed"}]}
        i += 1




def auth_contact(query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj


    #Collect errors 
    error_list = get_errors_in_query("auth_contact",query_obj, config_obj)
    if error_list != []: 
        return {"error_list":error_list}
    
    black_list_emails = ["https://en.wikipedia.org/wiki/Example.com", "example@example.com"]
    if query_obj["email"] in black_list_emails:
        return {"error_list":[{"error_code": "black-listed-email"}]}

    collection = "c_message"
    sender = config_obj[config_obj["server"]]["contactemailreceivers"][0]
    receivers = [query_obj["email"]] + config_obj[config_obj["server"]]["contactemailreceivers"]
    query_obj["page"] = query_obj["page"] if "page" in query_obj else ""

    msg_text = "\n\n%s,\n"  % (query_obj["fname"])
    msg_text += "We have received your message and will make every effort "
    msg_text += "to respond to you within a reasonable amount of time.\n\n"
    param_dict = {
        "fname":"First Name", "lname":"Last Name", "email":"Email", "subject":"Subject", 
        "page":"Page", "message":"Message"
    }
    param_list = ["fname", "lname", "email", "subject", "page", "message"]
    for param in param_list:
        if param in query_obj:
            if query_obj[param].strip() != "":
                msg_text += "%s: %s\n" % (param_dict[param], query_obj[param].strip())
    

    page_url = query_obj["page"] if "page" in query_obj else ""

    res_json = {
        "type":"alert-success",
        "message":msg_text
    }

    msg = MIMEText(msg_text)
    msg['Subject'] = query_obj["subject"]
    msg['From'] = sender
    msg['To'] = receivers[0]
    store_json = {
        "fname":query_obj["fname"],
        "lname":query_obj["lname"],
        "email":sender,
        "subject":query_obj["subject"], 
        "message":query_obj["message"], 
        "page":page_url,
        "agent":"",
        "comment":"",
        "creation_time":"",
        "update_time":"",
        "status":"new",
        "visibility":"visible"
    }
    
    #github_endpoint = "https://api.github.com/repos/glygener/glygen-issues/issues"
    github_endpoint = "https://api.github.com/repos/clinical-biomarkers/biomarker-issue-repo/issues"
    #github_endpoint = "https://github.com/clinical-biomarkers/biomarker-issue-repo/issues"
    
    github_token = current_app.config["GITHUB_TOKEN"]
    github_assignee = current_app.config["GITHUB_ASSIGNEE"]

    issue_obj = {
        "title":query_obj["subject"],
        "body":msg_text,
        "assignees":[github_assignee],
        "labels":["biomarker-frontend"]
    } 
    try:
        if config_obj["server"] != "dev":
            s = smtplib.SMTP('localhost')
            s.sendmail(sender, receivers, msg.as_string())
            s.quit()
        res = create_github_issue(github_endpoint, github_token, issue_obj)
        if "error_list" in res:
            return res
        store_json["github"] = res
        store_json["message_status"] = "success"
    except Exception as e:
        res_json = {"error_list":[{"error_code":str(e)}]}
        store_json["message_status"] = "failed"

    store_json["creation_time"] = datetime.datetime.now()
    store_json["update_time"] = store_json["creation_time"] 
    result = dbh[collection].insert_one(store_json)
    
    return res_json





def auth_notify(query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj


    #Collect errors 
    error_list = get_errors_in_query("auth_notify",query_obj, config_obj)
    if error_list != []: 
        return {"error_list":error_list}
    

    collection = "c_message"
    sender = config_obj[config_obj["server"]]["notifyemailreceivers"][0]
    receivers = [config_obj[config_obj["server"]]["notifyemailreceivers"]]
    query_obj["page"] = query_obj["page"] if "page" in query_obj else ""

    msg_text = "\n\n%s,\n"  % (query_obj["user"])
    msg_text += "We have received your message and will make every effort "
    msg_text += "to respond to you within a reasonable amount of time.\n\n"
    param_dict = {
        "user":"User", "subject":"Subject", 
        "page":"Page", "message":"Message"
    }
    param_list = ["user",  "subject", "page", "message"]
    for param in param_list:
        if param in query_obj:
            if query_obj[param].strip() != "":
                msg_text += "%s: %s\n" % (param_dict[param], query_obj[param].strip())
    

    page_url = query_obj["page"] if "page" in query_obj else ""

    res_json = {
        "type":"alert-success",
        "message":msg_text
    }

    msg = MIMEText(msg_text)
    msg['Subject'] = query_obj["subject"]
    msg['From'] = sender
    msg['To'] = receivers[0]
    store_json = {
        "user":query_obj["user"],
        "email":sender,
        "subject":query_obj["subject"], 
        "message":query_obj["message"], 
        "page":page_url,
        "agent":"",
        "comment":"",
        "creation_time":"",
        "update_time":"",
        "status":"new",
        "visibility":"visible"
    }
    
    github_endpoint = "https://api.github.com/repos/glygener/glygen-issues/issues"
    #github_token = os.environ['GITHUB_TOKEN']
    #github_assignee = os.environ['GITHUB_ASSIGNEE'] 
    github_token = current_app.config["GITHUB_TOKEN"]
    github_assignee = current_app.config["GITHUB_ASSIGNEE"]

    issue_obj = {
        "title":query_obj["subject"],
        "body":msg_text,
        "assignees":[github_assignee],
        "labels":["frontend_user_issue"]
    } 
    try:
        if config_obj["server"] != "dev":
            s = smtplib.SMTP('localhost')
            s.sendmail(sender, receivers, msg.as_string())
            s.quit()
        res = create_github_issue(github_endpoint, github_token, issue_obj)
        if "error_list" in res:
            return res
        store_json["github"] = res
        store_json["message_status"] = "success"
    except Exception as e:
        res_json = {"error_list":[{"error_code":str(e)}]}
        store_json["message_status"] = "failed"

    store_json["creation_time"] = datetime.datetime.now()
    store_json["update_time"] = store_json["creation_time"] 
    result = dbh[collection].insert_one(store_json)
    
    return res_json







def create_github_issue(url, github_token, issue_obj):

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + github_token,
        "X-GitHub-Api-Version":"2022-11-28"
    }

    res_obj = {}
    try:
        response = requests.post(url, data=json.dumps(issue_obj), headers=headers)
        code = response.status_code
        if code == 201:
            res = response.json()
            res_obj = {"number":res["number"], "url":res["url"]}
        else:
            res_obj = {"error_list":[{"error_code": "Bad response status code: %s!" % (code)}]}
    except Exception as e:
        res_obj = {"error_list":[{"error_code":str(e)}]}


    return res_obj






def auth_register(query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("auth_register",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}

    collection = "c_users"

    query_obj["email"] = query_obj["email"].lower()
    query_obj["password"] = bcrypt.hashpw(query_obj["password"].encode('utf-8'), bcrypt.gensalt())

    res_obj = {}
    if len(list(dbh[collection].find({"email":query_obj["email"]}))) != 0:
        res_obj =  {"error_list":[{"error_code":"email-already-regisgered"}]}
    else:
        res = dbh[collection].insert_one(query_obj)
        res_obj = {"type":"success"}

    return res_obj



def auth_aisearch(query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj


    collection = "c_aisearch"

    #If collection does not exit, create one
    if collection not in dbh.list_collection_names():
        qry_obj = {"glycan_ai_search":True,"protein_ai_search": True}
        res = dbh[collection].insert_one(qry_obj)

    #Collect errors 
    error_list = get_errors_in_query("auth_aisearch",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list, "aaaa":"bbbb"}

    res = dbh[collection].update({}, {'$set':query_obj}, upsert=True)
    res_obj = {"type":"success"}

    return res_obj



    
def auth_userinfo(logged_user, query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("auth_userinfo",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}
    logged_user_info = dbh["c_users"].find_one({'email' : logged_user})
    if "role" not in logged_user_info:
        return {"error_list":[{"error_code":"no-admin-access"}]}
    if logged_user_info["role"] != "admin":
        return {"error_list":[{"error_code":"no-admin-access"}]}

    q_obj = {'email' : query_obj["email"]}
    res_obj = dbh["c_users"].find_one(q_obj)
    if res_obj == None:
        return {"error_list":[{"error_code":"user-does-not-exist"}]}
    for k in ["_id", "password"]:
        if k in res_obj:
            res_obj.pop(k)

    return res_obj



def auth_login(query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("auth_login",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}
    collection = "c_users"

    query_obj["email"] = query_obj["email"].lower()
    login_user = dbh[collection].find_one({'email' : query_obj["email"]})
    res_obj = {}
    if login_user:
        stored_password = login_user['password'].encode('utf-8')
        #stored_password = login_user['password']
        submitted_password = query_obj['password'].encode('utf-8')
        if login_user["status"] == 0:
            res_obj =  {"error_list":[{"error_code":"inactive-account"}]}
        else:
            if bcrypt.hashpw(submitted_password, stored_password) != stored_password:
                res_obj =  {"error_list":[{"error_code":"invalid-email/password-combination"}]}
            else:
                token = make_hash_string() + make_hash_string()
                ts = datetime.datetime.now()
                session_obj = {"email":query_obj["email"], "token":token, "createdts":ts}
                res = dbh["c_session"].insert_one(session_obj)
                res_obj = {"type":"success", "token":token}
    else:
        res_obj =  {"error_list":[{"error_code":"invalid-email/password-combination"}]}

    return res_obj



def auth_contactlist(logged_user, query_obj, config_obj):

    dbh, error_obj = get_mongodb()

    #Collect errors 
    error_list = get_errors_in_query("auth_contactlist",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}

    logged_user_info = dbh["c_users"].find_one({'email' : logged_user})
    if "role" not in logged_user_info:
        return {"error_list":[{"error_code":"no-admin-role"}]}
    if logged_user_info["role"] != "admin":
        return {"error_list":[{"error_code":"no-admin-role"}]}
            

    import pymongo
    doc_list = []
    try:
        q_obj = {} if query_obj["visibility"] == "all" else {"visibility":query_obj["visibility"]}
        doc_list = dbh["c_message"].find(q_obj).sort('creation_time', pymongo.DESCENDING)
    except Exception as e:
        return {"error_list":[{"error_code":str(e)}]}

    out_obj = []
    for doc in doc_list:
        doc["id"] = str(doc["_id"])
        doc.pop("_id")
        for k in ["creation_time", "update_time", "ts"]:
            if k not in doc:
                continue
            doc[k] = doc[k].strftime('%Y-%m-%d %H:%M:%S %Z%z')
        out_obj.append(doc)


    return out_obj


def auth_userupdate(logged_user, query_obj, config_obj):
    dbh, error_obj = get_mongodb()

    #Collect errors 
    error_list = get_errors_in_query("auth_userupdate",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}

    try: 
        target_user_name = query_obj["email"]
        target_user_info = dbh["c_users"].find_one({'email' : target_user_name})
        logged_user_info = dbh["c_users"].find_one({'email' : logged_user})

        update_obj = {}
        if target_user_name == logged_user and query_obj and "password" in query_obj:
            p = bcrypt.hashpw(query_obj["password"].encode('utf-8'),  bcrypt.gensalt())
            update_obj["password"] = p
        else:
            if "role" not in logged_user_info:
                return {"error_list":[{"error_code":"no-admin-role"}]}
            if logged_user_info["role"] != "admin":
                return {"error_list":[{"error_code":"no-admin-role"}]}
            for k in query_obj:
                if k == "password":
                    update_obj[k] = bcrypt.hashpw(query_obj[k].encode('utf-8'), bcrypt.gensalt())
                elif k not in ["token", "email"]:
                    update_obj[k] = query_obj[k]

        q_obj = {"email":target_user_name}
        res = dbh["c_users"].update_one(q_obj, {'$set':update_obj}, upsert=True)
        return {"type":"success"}
    except Exception as e:
        return {"error_list":[{"error_code":str(e)}]}




def auth_userdelete(logged_user, query_obj, config_obj):
    dbh, error_obj = get_mongodb()

    #Collect errors
    error_list = get_errors_in_query("auth_userdelete",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}

    try:
        target_user_name = query_obj["email"]
        target_user_info = dbh["c_users"].find_one({'email' : target_user_name})
        logged_user_info = dbh["c_users"].find_one({'email' : logged_user})
        update_obj = {}
        if "role" not in logged_user_info:
            return {"error_list":[{"error_code":"no-admin-role"}]}
        if logged_user_info["role"] != "admin":
            return {"error_list":[{"error_code":"no-admin-role"}]}
        q_obj = {"email":target_user_name}
        user_doc = dbh["c_users"].find_one(q_obj)
        if user_doc == None:
            return {"error_list":[{"error_code":"user-does-not-exist"}]}
        res = dbh["c_users"].delete_one(q_obj)
        return {"type":"success"}
    except Exception as e:
        return {"error_list":[{"error_code":str(e)}]}







def auth_contactupdate(logged_user, query_obj, config_obj):

    dbh, error_obj = get_mongodb()

    #Collect errors 
    error_list = get_errors_in_query("auth_contactupdate",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}

    try: 
        logged_user_info = dbh["c_users"].find_one({'email' : logged_user})
        if "role" not in logged_user_info:
            return {"error_list":[{"error_code":"no-admin-access"}]}
        if logged_user_info["role"] != "admin":
            return {"error_list":[{"error_code":"no-admin-access"}]}

        q_obj = {"_id":ObjectId(query_obj["id"])}
        update_obj = {}
        for k in query_obj:
            if k not in ["id"]:
                update_obj[k] = query_obj[k]
        res = dbh["c_message"].update_one(q_obj, {'$set':update_obj}, upsert=True)
        return {"type":"success", "update_obj":update_obj}
    except Exception as e:
        return {"error_list":[{"error_code":str(e)}]}




def auth_contactdelete(logged_user, query_obj, config_obj):

    dbh, error_obj = get_mongodb()

    #Collect errors 
    error_list = get_errors_in_query("auth_contactdelete",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}

    logged_user_info = dbh["c_users"].find_one({'email' : logged_user})
    if "role" not in logged_user_info:
        return {"error_list":[{"error_code":"no-admin-access"}]}
    if logged_user_info["role"] != "admin":
        return {"error_list":[{"error_code":"no-admin-access"}]}


    try: 
        q_obj = {"_id":ObjectId(query_obj["id"])}
        doc = dbh["c_message"].find_one(q_obj)
        if doc == None:
            return {"error_list":[{"error_code":"message-not-found"}]}
    except Exception as e:
        return {"error_list":[{"error_code":str(e)}]}

    try:
        q_obj = {"_id":ObjectId(query_obj["id"])}
        update_obj = {"visibility":"hidden"}
        res = dbh["c_message"].update_one(q_obj, {'$set':update_obj}, upsert=True)
        return {"type":"success", "update_obj":update_obj}
    except Exception as e:
        return {"error_list":[{"error_code":str(e)}]}

