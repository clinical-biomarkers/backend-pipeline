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

from bmkb.typeahead_apilib import glycan_typeahead, protein_typeahead, biomarker_typeahead,global_typeahead, categorized_typeahead
from bmkb.util import get_req_obj, make_list_objects_direct, get_errors_in_query
import traceback



api = Namespace("typeahead", description="IDmapping APIs")

typeahead_query_model = api.model(
    'Search Init Query', 
    {
        "field": fields.String(required=True, default="glytoucan_ac"),
        "value": fields.String(required=True, default="G"),
        "limit": fields.Integer(required=True, default=10)
    }
)

categorized_typeahead_query_model = api.model(
    'Categorized Typeahead Query',
    {
        "field": fields.String(required=True, default="go_term"),
        "value": fields.String(required=True, default="kinase"),
        "total_limit": fields.Integer(required=True, default=15),
        "categorywise_limit": fields.Integer(required=True, default=5)
    }    
 
)

global_typeahead_query_model = api.model(
    'Global Typeahead Query',
    {   
        "target": fields.String(required=True, default="glycan"),
        "value": fields.String(required=True, default="G"),
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
            field_list_one = ["glytoucan_ac", "motif_name", "enzyme_uniprot_canonical_ac", 
                "glycan_pmid", "enzyme", 
                "biomarker_id", "biomarker_name","biomarker_type",
                "biomarker_disease_id", "biomarker_disease_name"
            ]
            field_list_two = ["uniprot_canonical_ac", "uniprot_id", "refseq_ac", "protein_id",
                "protein_name", "gene_name", "pdb_id", "pathway_id", "pathway_name", 
                "disease_name","disease_id", 
                "go_id", "go_term", "protein_pmid",
                "biomarker_id", "biomarker_name","biomarker_type",
                "biomarker_disease_id", "biomarker_disease_name",
                "tax_id",
                "tax_name"
            ] 
            field_list_three = [
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
                #Collect errors 
                error_list = get_errors_in_query("typeahead_protein",req_obj, config_obj)
                if error_list != []:
                    return {"error_list":error_list}

                tmp_obj_one, tmp_obj_two, tmp_obj_three = [], [], []
                
                req_field_list = [req_obj["field"]] if "field" in req_obj else []
                req_field_list += req_obj["field_list"] if "field_list" in req_obj else []
                req_field_list = list(set(req_field_list))
                req_obj["field_list"] = req_field_list

                flag_one = len(set(req_field_list).intersection(set(field_list_one))) > 0
                flag_two = len(set(req_field_list).intersection(set(field_list_two))) > 0
                flag_three = len(set(req_field_list).intersection(set(field_list_three))) > 0 
                if flag_one:
                    tmp_obj_one = glycan_typeahead(req_obj, config_obj)
                if flag_two:
                    tmp_obj_two = protein_typeahead(req_obj, config_obj)
                if flag_three:
                    tmp_obj_three = biomarker_typeahead(req_obj, config_obj)
                if "error_list" in tmp_obj_one:
                    res_obj = tmp_obj_one
                elif "error_list" in tmp_obj_two: 
                    res_obj = tmp_obj_two
                elif "error_list" in tmp_obj_three:
                    res_obj = tmp_obj_three
                else:
                    res_obj = sorted(list(set(tmp_obj_one + tmp_obj_two + tmp_obj_three)))
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        
        return res_obj, http_code


    @api.doc(False)
    def get(self):
        return self.post()



@api.route('/categorized_typeahead/')
class Typeahead(Resource):
    @api.doc('categorized_typeahead')
    @api.expect(categorized_typeahead_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            res_obj = log_request(req_obj, "/typeahead/categorized_typeahead/", request)
            if "error_list" not in res_obj:
                tmp_obj = categorized_typeahead(req_obj, config_obj)
                if "error_list" in tmp_obj:
                    res_obj = tmp_obj
                else:
                    res_obj = tmp_obj
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()

@api.route('/global_typeahead/')
class Typeahead(Resource):
    @api.doc('global_typeahead')
    @api.expect(global_typeahead_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        json_url = os.path.join(SITE_ROOT, "conf/global_typeahead.json")
        path_dict = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            res_obj = log_request(req_obj, "/typeahead/global_typeahead/", request)
            if "error_list" not in res_obj:
                tmp_obj = global_typeahead(req_obj, config_obj, path_dict)
                if "error_list" in tmp_obj:
                    res_obj = tmp_obj
                else:
                    res_obj = tmp_obj
        except Exception as e:
            res_obj = log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()




