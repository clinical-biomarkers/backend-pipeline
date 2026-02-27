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

from bmkb.event_apilib import event_addnew, event_detail, event_update, event_list, event_delete

from bmkb.util import get_req_obj
import traceback


api = Namespace("event", description="Event APIs")

addnew_query_model = api.model(
    'Event Addnew Query', 
    {
        "title":fields.String(required=True, default="some title"),
        "description":fields.String(required=True, default="some description"),
        "start_date":fields.String(required=True, default="01/20/2021 23:59:59"),
        "end_date":fields.String(required=True, default="01/21/2021 07:00:00"),
        "venue":fields.String(required=True, default="some venue"),
        "url":fields.String(required=True, default="some url"),
        "url_name":fields.String(required=True, default="some url name"),
        "visibility":fields.String(required=True, default="visible")
    }
)


detail_query_model = api.model(
    'Event Detail Query', 
    {
        "id":fields.String(required=True, default="")
    }
)

list_query_model = api.model(
    'Event List Query', 
    { 
        "visibility":fields.String(required=True, default="all"),
        "status":fields.String(required=True, default="all")
    }
)

update_query_model = api.model(
    'Event Update Query', 
    {
        "id":fields.String(required=True, default=""),
        "visibility":fields.String(required=True, default="visible")
    }
)


delete_query_model = api.model(
    'Event Delete Query', 
    {
        "id":fields.String(required=True, default="")
    }
)   




@api.route('/addnew/')
class Event(Resource):
    #@api.doc(False)
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
            res_obj = log_request(req_obj, "/event/addnew/", request)
            if "error_list" not in res_obj:
                res_obj = event_addnew(current_user, req_obj, config_obj)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()


@api.route('/detail/')
class Event(Resource):
    @api.expect(detail_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            res_obj = log_request(req_obj, "/event/detail/", request)
            if "error_list" not in res_obj:
                res_obj = event_detail(req_obj, config_obj)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code


    @api.doc(False)
    def get(self):
        return self.post()


@api.route('/list/')
class Event(Resource):
    @api.expect(list_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            res_obj = log_request(req_obj, "/event/list/", request)
            if "error_list" not in res_obj:
                res_obj = event_list(req_obj, config_obj)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()


@api.route('/update/')
class Event(Resource):
    #@api.doc(False)
    @api.expect(update_query_model)
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
            res_obj = log_request(req_obj, "/event/update/", request)
            if "error_list" not in res_obj:
                res_obj = event_update(current_user, req_obj, config_obj)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()



@api.route('/delete/')
class Event(Resource):
    #@api.doc(False)
    @api.expect(delete_query_model)
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
            res_obj = log_request(req_obj, "/event/delete/", request)
            if "error_list" not in res_obj:
                res_obj = event_delete(current_user, req_obj, config_obj)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    
    @api.doc(False)
    def get(self):
        return self.post()




