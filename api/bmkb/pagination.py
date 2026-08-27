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

from bmkb.pagination_apilib import pagination_page
from bmkb.util import get_req_obj, retrieve_cached_list_objects, cache_list_objects, get_hash_id, apply_pagination
import traceback


api = Namespace("pagination", description="Pagination APIs")

page_query_model = api.model("Pagination Page Query", 
    { 
        "record_type": fields.String(required=True, default="protein"),
        "record_id": fields.String(required=True, default="P14210"),
        "table_id": fields.String(required=True, default="glycosylation_reported_with_glycan"),
        "sort": fields.String(required=True, default="start_pos"),
        "order": fields.String(required=True, default="asc"),
        "offset": fields.Integer(required=True, default=1),
        "limit": fields.Integer(required=True, default=10)
    }
)



@api.route('/page/')
class Pagination(Resource):
    @api.expect(page_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        json_url = os.path.join(SITE_ROOT, "conf/filter_init.json")
        config_obj["filter_init"] = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            res_obj = log_request(req_obj, "/pagination/page/", request)
            if "error_list" not in res_obj:
                api_name = "pagination_page"
                cache_id = req_obj["id"] if "id" in req_obj else ""
                listcache_id = get_hash_id(api_name, "", req_obj)
                in_dict = {"cache_id":cache_id,"listcache_id":listcache_id,"api_name":api_name}
                res_obj = retrieve_cached_list_objects(in_dict,req_obj,config_obj,"paginated")
                if res_obj == None:
                    res_obj = pagination_page(req_obj, config_obj)
                    if "error_list" not in res_obj:
                        res = cache_list_objects(api_name, cache_id, listcache_id, res_obj, config_obj)
                        if "error_list" in res:
                            res_obj = res
                if "results" in res_obj:
                    debug_list = []
                    debug_list.append({"before":len(res_obj["results"])})
                    res_obj["pagination"] = {"total_length":len(res_obj["results"])}
                    for k in ["offset", "limit", "sort", "order"]:
                        if k in req_obj:
                            res_obj["pagination"][k] = req_obj[k]
                    res_obj["results"] = apply_pagination(res_obj["results"], req_obj)
                    debug_list.append({"after":len(res_obj["results"])})
                    #return debug_list

        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()







