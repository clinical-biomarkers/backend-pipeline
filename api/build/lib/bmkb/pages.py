import os,sys
from flask_restx import Namespace, Resource, fields
from flask import (request, current_app, send_file)
from bmkb.db import log_error, log_request
from bmkb.document import get_one, get_many, insert_one, update_one, delete_one, order_json_obj
from werkzeug.utils import secure_filename
import datetime
import time
import subprocess
import json
import bcrypt

from bmkb.pages_apilib import home_init, list_init, ontology
from bmkb.util import trim_object, get_req_obj
import traceback


api = Namespace("pages", description="Pages APIs")

home_init_query_model = api.model("Pages Home Init Query", {})
ontology_query_model = api.model("Pages Ontology Query", {})
list_init_query_model = api.model("Pages List Init Query",{ "table_id": fields.String(required=True, default="")})


@api.route('/home_init/')
class Pages(Resource):
    @api.expect(home_init_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            data_path = os.environ["DATA_PATH"]
            res_obj = log_request({}, "/pages/home_init/", request)
            if "error_list" not in res_obj:
                res_obj = home_init(config_obj, data_path)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code
        
    @api.doc(False)
    def get(self):
        return self.post()


@api.route('/ontology/')
class Pages(Resource):
    @api.expect(ontology_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            data_path = os.environ["DATA_PATH"]
            res_obj = log_request({}, "/pages/ontology/", request)
            if "error_list" not in res_obj:
                res_obj = ontology(config_obj)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())

        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()





@api.route('/list_init/', methods=['GET', 'POST'])
class Pages(Resource):
    @api.expect(list_init_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        json_url = os.path.join(SITE_ROOT, "conf/list_init.json")
        config_obj["list_init"] = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            res_obj = log_request(req_obj, "/pages/list_init/", request)
            if "error_list" not in res_obj:
                res_obj = list_init(config_obj, req_obj)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()







