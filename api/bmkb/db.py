import os
import pymongo
import datetime
import string
import pytz
import sqlite3
import random
import traceback
import json

import click
from flask import current_app, g, Flask, Request
from flask.cli import with_appcontext
from user_agents import parse






def get_mongodb():

    ret_obj, error_obj = {}, {}
    try: 
        conn_str, db_name = os.environ['MONGODB_CONNSTRING'], os.environ['DB_NAME']
        client = pymongo.MongoClient(conn_str)
        #client.server_info()
        ret_obj = client[db_name]
    except pymongo.errors.ServerSelectionTimeoutError as err:
        error_obj = {"status":0, "error":"Connection to MongoDB failed", "details":err.details}
    except pymongo.errors.OperationFailure as err:
        error_obj = {"status":0, "error":"Connection to MongoDB failed", "details":err.details}
    return ret_obj, error_obj


def load_network_docs():

    #doc_list = []
    dbh, error_obj = get_mongodb()
    doc_list = list(dbh["c_network"].find({}))
    
    return doc_list


def log_request(req_obj, api_name, request):

    mongo_dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj
    
    if api_name == "/job/addnew/" and "intable" in req_obj:
        req_obj["intable"] = "removed"
    
    if len(json.dumps(req_obj)) > 20000:
        return {"error_list":[{"error_code": "Too long request, unable to log request!"}]}


    header_dict = {}
    header_dict["user_agent"] = request.headers.get('User-Agent')
    header_dict["referer"] = request.headers.get('referer')
    header_dict["origin"] = request.headers.get('Origin')
    header_dict["ip"] = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)

    header_dict["is_bot"] = False
    user_agent = request.headers.get('User-Agent')
    if type(user_agent) is str:
        ug = parse(user_agent)
        header_dict["is_bot"] = ug.is_bot
    
 
    try:
        ts_format = "%Y-%m-%d %H:%M:%S %Z%z"
        ts = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format)
        log_obj = {"api":api_name, "req":req_obj, "ts":ts, "headers":header_dict}
        res = mongo_dbh["c_request"].insert_one(log_obj)
        return {}
    except Exception as e:
        return {"error_list":[{"error_code": "Unable to log error!"}]}






def log_error(error_log):

    mongo_dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj
    ts_format = "%Y-%m-%d %H:%M:%S %Z%z"
    ts = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format)
    try:
        error_id = get_random_string(6)
        error_obj = {"id":error_id, "log":error_log, "ts":ts}
        res = mongo_dbh["c_log"].insert_one(error_obj)
        return {"error_list":[{"error_code": "exception-error-" + error_id}]}
    except Exception as e:
        return {"error_list":[{"error_code": "Unable to log error!"}]}


def get_random_string(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def reset_sequence_value(coll_obj, sequence_name):
    seq_doc = coll_obj.find_and_modify(
        query={'sequence_name': sequence_name},
        update={'$set': {'sequence_value': 0}},
        upsert=True,
        new=True
    )
    return


def next_sequence_value(coll_obj, sequence_name):
    seq_doc = coll_obj.find_and_modify(
        query={'sequence_name': sequence_name},
        update={'$inc': {'sequence_value': 1}},
        upsert=True,
        new=True
    )
    return int(seq_doc["sequence_value"])









def get_userinfo(user_name):

    try:
        mongo_dbh, error_obj = get_mongodb()
        user_doc = mongo_dbh["c_users"].find_one({'email' : user_name })
        user_info = {
            "fname":user_doc["fname"],
            "lname":user_doc["lname"],
            "email":user_doc["email"],
            "status":user_doc["status"]
        }
        return user_info, {}, 1
    except Exception as e:
        err_obj =  log_error(traceback.format_exc())
        return {}, err_obj, 0





