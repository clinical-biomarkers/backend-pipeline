import os,sys
from flask_restx import Namespace, Resource, fields
from flask import (request, current_app, send_file)
from bmkb.document import get_one, get_many, insert_one, update_one, delete_one, order_json_obj
from werkzeug.utils import secure_filename
import datetime
import time
import pytz
import subprocess
import json
import bcrypt
import pymongo
import requests

from bmkb.db import get_mongodb, log_error
from bmkb.misc_apilib import verlist
import traceback


api = Namespace("misc", description="Misc APIs")
verlist_query_model = api.model("Misc Version List Query", {})

@api.route('/info/')
class Misc(Resource):
    @api.doc(False)
    def post(self):
        res_obj = {"config":{}}
        try:
            #ip_addr = request.remote_addr
            #ip_addr = request.environ['REMOTE_ADDR']
            #ip_addr = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            #return {"ip":ip_addr}
            for k in ["DB_NAME", "MAIL_SERVER", "MAIL_PORT", "MAIL_SENDER"]:
                if k in os.environ:
                    res_obj["config"][k] = os.environ[k]
                if k in current_app.config:
                    res_obj["config"][k] = current_app.config[k]
            #return res_obj
 
            mongo_dbh, error_obj = get_mongodb()
            res_obj["connection_status"] = "success" if error_obj == {} else error_obj
            #return res_obj
    
            res_obj["user_agent"] = request.headers.get('User-Agent')
            res_obj["referer"] = request.headers.get('referer')
            res_obj["origin"] = request.headers.get('Origin')
            return res_obj
            
            init_obj = mongo_dbh["c_init"].find_one({})
            if "_id" in init_obj:
                init_obj.pop("_id")
            res_obj["initobj"] = init_obj
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code



@api.route('/verlist/')
class Misc(Resource):
    #@api.doc(False)
    @api.expect(verlist_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = {}
            data_path = os.environ["DATA_PATH"]
            res_obj = verlist(config_obj)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code
    @api.doc(False)
    def get(self):
        return self.post()







