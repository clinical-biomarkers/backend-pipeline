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

from bmkb.globalsearch_apilib import globalsearch_search
from bmkb.indexlib import search_all

from bmkb.util import get_req_obj
import traceback


api = Namespace("globalsearch", description="Globalsearch APIs")

search_query_model = api.model(
    'Global Search Query', 
    { 'term': fields.String(required=True, default="Hepatocyte")}
)



@api.route('/search/')
class Globalsearch(Resource):
    @api.expect(search_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        json_url = os.path.join(SITE_ROOT, "conf/path_targets.json")
        config_obj["path_targets"] = json.load(open(json_url))

        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            if "error_list" in req_obj:
                return req_obj
            data_path = os.environ["DATA_PATH"]
            res_obj = log_request(req_obj, "/globalsearch/search/", request)
            if "error_list" not in res_obj:
                res_obj = search_all("globalsearch_search",req_obj,config_obj)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()






