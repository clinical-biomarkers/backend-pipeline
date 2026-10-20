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

from bmkb.entity_apilib import entity_detail

from bmkb.util import get_req_obj
import traceback


api = Namespace("entity", description="Entity APIs")


@api.route('/detail/<ref_id>/')
@api.doc(params={
    "ref_id": {"in": "query", "default": "HGNC_6018"}
})

class Entity(Resource):
    def post(self, ref_id):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj, log_obj = {}, {}
        try:
            req_obj = {"ref_id":ref_id}
            req_obj_extra = get_req_obj(request)
            if req_obj_extra != None and "error_list" not in req_obj_extra:
                for k in req_obj_extra:
                    req_obj[k] = req_obj_extra[k]
            log_obj = log_request(req_obj, "/entity/detail/", request)
            #return req_obj
            if "error_list" not in log_obj:
                res_obj = entity_detail(req_obj, config_obj)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self, ref_id):
        return self.post(ref_id)





