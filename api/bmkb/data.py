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

from bmkb.data_apilib import list_download, detail_download, section_download
from bmkb.util import get_req_obj
import traceback


api = Namespace("data", description="Data Download APIs")

list_download_query_model = api.model(
    "List Download Query", 
    { 
        "id": fields.String(required=True, default=""),
        "download_type": fields.String(required=True, default="glycan_list"),
        "format": fields.String(required=True, default="csv"),
        "compressed": fields.Boolean(required=True, default=False)
    }
)

detail_download_query_model = api.model(
    "Detail Download Query",
    {
        "id": fields.String(required=True, default="G17689DH"),
        "download_type": fields.String(required=True, default="glycan_detail"),
        "format": fields.String(required=True, default="json"),
        "compressed": fields.Boolean(required=True, default=False)
    }
)

section_download_query_model = api.model(
    "Section Download Query",
    {
        "id": fields.String(required=True, default="G17689DH"),
        "download_type": fields.String(required=True, default="glycan_section"),
        "section": fields.String(required=True, default="glycoprotein"),
        "format": fields.String(required=True, default="csv"),
        "compressed": fields.Boolean(required=True, default=False)
    }
)






@api.route('/list_download/')
class Data(Resource):
    @api.expect(list_download_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        config_obj["server"] = os.environ["SERVER"]
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            data_path = os.environ["DATA_PATH"]
            res_obj = log_request(req_obj, "/data/list_download/", request)
            if "error_list" not in res_obj:
                res_obj = list_download(req_obj, config_obj, data_path)
                if type(res_obj) is not dict:
                    return res_obj
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()


@api.route('/detail_download/')
class Data(Resource):
    @api.expect(detail_download_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            data_path = os.environ["DATA_PATH"]
            res_obj = log_request(req_obj, "/data/detail_download/", request)
            if "error_list" not in res_obj:
                res_obj = detail_download(req_obj, config_obj, data_path)
                if type(res_obj) is not dict:
                    return res_obj
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()


@api.route('/section_download/')
class Data(Resource):
    @api.expect(section_download_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        json_url = os.path.join(SITE_ROOT, "conf/section.json")
        sec_info = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            data_path = os.environ["DATA_PATH"]
            res_obj = log_request(req_obj, "/data/section_download/", request)
            if "error_list" not in res_obj:
                res_obj = section_download(req_obj, config_obj, sec_info, data_path)
                if type(res_obj) is not dict:
                    return res_obj
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()





