import os,sys
from flask_restx import Namespace, Resource, fields
from flask import (request, current_app, send_file)
from bmkb.db import log_error, log_request
from werkzeug.utils import secure_filename
import datetime
import time
import subprocess
import json
import bcrypt

from bmkb.typeahead_apilib import biomarker_typeahead
from bmkb.util import get_req_obj
import traceback



api = Namespace("typeahead", description="Typeahead APIs")

typeahead_query_model = api.model(
    'Typeahead Query', 
    {
        "field": fields.String(required=True, default="biomarker_id"),
        "value": fields.String(required=True, default="A"),
        "limit": fields.Integer(required=True, default=10)
    }
)


@api.route('/typeahead/')
class Typeahead(Resource):
    @api.doc('typeahead')
    @api.expect(typeahead_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            data_path = os.environ["DATA_PATH"]
            field_list = [
                "biomarker_id", "biomarker_canonical_id"
                "biomarker",
                "biomarker_entity_name",
                "biomarker_entity_id",
                "biomarker_entity_type",
                "specimen_name",
                "specimen_id",
                "specimen_loinc_code",
                "best_biomarker_role",
                "condition_id",
                "condition_name",
                "publication_id"
            ]
            res_obj = log_request(req_obj, "/typeahead/typeahead/", request)
            if "error_list" not in res_obj:
                tmp_obj = []
                req_field_list = [req_obj["field"]] if "field" in req_obj else []
                req_field_list += req_obj["field_list"] if "field_list" in req_obj else []
                req_field_list = list(set(req_field_list))
                req_obj["field_list"] = req_field_list
                flag = len(set(req_field_list).intersection(set(field_list))) > 0 
                if flag:
                    tmp_obj = biomarker_typeahead(req_obj, config_obj)
                if "error_list" in tmp_obj:
                    res_obj = tmp_obj
                else:
                    res_obj = sorted(list(set(tmp_obj)))
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()





