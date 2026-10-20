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

from bmkb.indexlib import search_one
from bmkb.biomarker_apilib import biomarker_detail, biomarker_search, biomarker_search_init

from bmkb.util import get_req_obj, make_list_objects_indirect, get_hash_id, cache_list_objects, retrieve_cached_list_objects, apply_pagination
import traceback


from .llm import LLM
from .llm.openai_api import OpenAILLM
from .llm.rate_limiter import ai_search_rate_limiter

from .ai_search import transform_ai_query





api = Namespace("biomarker", description="Biomarker APIs")


search_init_query_model = api.model("Biomarker Search Init Query", {})

search_simple_query_model = api.model("Biomarker Simple Search Query",
    {
        "term_category": fields.String(required=True, default="biomarker"),
        "term": fields.String(required=True, default="AN6278-5")
    }
)

search_global_query_model = api.model("Biomarker Global Search Query",
    {
        "term": fields.String(required=True, default="AN6278-5")
    }
)


ai_search_query_model = api.model("Biomarker AI Search Query",
    {
        "query": fields.String(required=True, default="Can you show me protein biomarkers related to prostate cancer")
    }
)


detail_query_model = api.model("Biomarker Detail Query", 
    { 
        "biomarker_id": fields.String(required=True, default="AN6278-5")
    }
)

search_query_model = api.model("Biomarker Search Query",
    { 
        "biomarker_id": fields.String(required=True, default="AN6278-5"),
        "biomarker":fields.String(required=True, default="Increased level of protein IL6"),
        "biomarker_entity_name":fields.String(required=True, default="Interleukin-6"),
        "biomarker_entity_id":fields.String(required=True, default="UPKB:P05231"),
        "biomarker_entity_type":fields.String(required=True, default="protein"),
        "specimen_name":fields.String(required=True, default="blood"),
        "specimen_id":fields.String(required=True, default="UBERON:0000178"),
        "specimen_loinc_code":fields.String(required=True, default="26881-3"),
        "best_biomarker_role":fields.String(required=True, default="prognostic"),
        "condition_id":fields.String(required=True, default="DOID:0080600"),
        "condition_name":fields.String(required=True, default="COVID-19"),
        "publication_id":fields.String(required=True, default="32479790"),
        "data_source":fields.String(required=True, default="oncomx")
    }
)


list_query_model = api.model("Biomarker List Query",{ "id": fields.String(required=True, default="")})




@api.route('/search_global/')
class Biomarker(Resource):
    @api.doc('search_global')
    @api.expect(search_global_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            res_obj = log_request(req_obj, "/biomarker/search_global/", request)
            if "error_list" not in res_obj:
                cache_flag, exact_match_flag = True, True
                res_obj = search_one("biomarker_search_global",req_obj,config_obj,cache_flag, exact_match_flag)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()


@api.route('/search_simple/')
class Biomarker(Resource):
    @api.doc('search_simple')
    @api.expect(search_simple_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            res_obj = log_request(req_obj, "/biomarker/search_simple/", request)
            if "error_list" not in res_obj:
                cache_flag, exact_match_flag = True, True
                res_obj = search_one("biomarker_search_simple",req_obj,config_obj,cache_flag, exact_match_flag)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()




@api.route('/search_init/')
class Biomarker(Resource):
    @api.doc('search_init')
    @api.expect(search_init_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            res_obj = log_request({}, "/biomarker/search_init/", request)
            if "error_list" not in res_obj:
                res_obj = biomarker_search_init(config_obj)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200 
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()



@api.route('/detail/<biomarker_id>/')
@api.doc(params={"biomarker_id": {"in": "query", "default": "AN6278-5"}})
class Biomarker(Resource):
    @api.doc('detail')
    @api.expect(detail_query_model)
    def post(self, biomarker_id):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = {"biomarker_id":biomarker_id}
            req_obj_extra = get_req_obj(request)
            if req_obj_extra != None:
                if "paginated_tables" in req_obj_extra:
                    req_obj["paginated_tables"] = req_obj_extra["paginated_tables"]
            res_obj = log_request(req_obj, "/biomarker/detail/", request)
            if "error_list" not in res_obj:
                res_obj = biomarker_detail(req_obj, config_obj)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self, biomarker_id):
        return self.post(biomarker_id)



@api.route('/search/')
class Biomarker(Resource):
    @api.doc('search')
    @api.expect(search_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            res_obj = log_request(req_obj, "/biomarker/search/", request)
            if "error_list" not in res_obj:
                res_obj = biomarker_search(req_obj, config_obj, "")
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200 
        return res_obj, http_code
    
    @api.doc(False)
    def get(self):
        return self.post()




@api.route('/ai_search/')
class Biomarker(Resource):
    @api.doc('ai_search')
    @api.expect(ai_search_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            ai_req_obj = get_req_obj(request)
            res_obj = log_request(ai_req_obj, "/biomarker/search/", request)
            if "error_list" not in res_obj:
                res_obj, http_code = transform_ai_query(ai_req_obj)
                if "error_list" not in res_obj:
                    res = biomarker_search(res_obj, config_obj, ai_req_obj["query"])
                    if "error_list" not in res:
                        res_obj = {
                            "list_id":res["list_id"],
                            "resultcount":res["resultcount"],
                            "ai_parsing":{
                                "original_query":ai_req_obj["query"],
                                "parsed_parameters":res["query"] if "query" in res else {}
                            }
                        }   
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()




@api.route('/list/')
class Biomarker(Resource):
    @api.doc('list')
    @api.expect(list_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            res_obj = log_request(req_obj, "/biomarker/list/", request)
            if "error_list" not in res_obj:
                api_name = "biomarker_list"
                cache_id = req_obj["id"] if "id" in req_obj else ""
                listcache_id = get_hash_id(api_name, "", req_obj)
                in_dict = {"cache_id":cache_id,"listcache_id":listcache_id,"api_name":api_name}
                res_obj = retrieve_cached_list_objects(in_dict,req_obj,config_obj,"paginated")
                if res_obj == None:
                    res_obj = make_list_objects_indirect(req_obj, config_obj, False)
                    return res_obj
                    if "error_list" not in res_obj:
                        res = cache_list_objects(api_name, cache_id, listcache_id, res_obj, config_obj)
                        if "error_list" in res:
                            res_obj = res
                            return {"flag":1}
                        else:
                            res_obj = retrieve_cached_list_objects(in_dict,req_obj,config_obj,"paginated")
                    #if "results" in res_obj:
                    #    res_obj["results"] = apply_pagination(res_obj["results"], req_obj)
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()

