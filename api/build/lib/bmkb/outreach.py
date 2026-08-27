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
from flask_jwt_extended import (
    jwt_required, get_jwt_identity
)

from bmkb.outreach_apilib import outreach_addnew, outreach_update, outreach_list

from bmkb.util import get_req_obj
import traceback

api = Namespace("outreach", description="Outreach APIs")

addnew_query_model = api.model(
    'Outreach Addnew Query', 
        {
        }
)



update_query_model = api.model(
    'Outreach Update Query', { "id": fields.String(required=True, default="63d04393d634c7d21067b32e")}
)
list_query_model = api.model('Outreach List Query', {})



@api.route('/addnew/')
class Outreach(Resource):
    @api.expect(addnew_query_model)
    @jwt_required
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            #current_user, user_info = "rykahsay@gwu.edu", {}
            current_user = get_jwt_identity()
            res_obj = log_request(req_obj, "/outreach/addnew/", request)
            if "error_list" not in res_obj:
                res_obj = outreach_addnew(current_user, req_obj, config_obj)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()


@api.route('/update/')
class Outreach(Resource):
    @api.expect(update_query_model)
    @jwt_required
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            res_obj = log_request(req_obj, "/outreach/update/", request)
            current_user = get_jwt_identity()
            if "error_list" not in res_obj:
                res_obj = outreach_update(current_user, req_obj, config_obj)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()

@api.route('/list/')
class Outreach(Resource):
    @api.expect(list_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            res_obj = log_request(req_obj, "/outreach/list/", request)
            if "error_list" not in res_obj:
                res_obj = outreach_list(req_obj, config_obj)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()







