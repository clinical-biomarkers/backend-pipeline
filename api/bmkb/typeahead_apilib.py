import os
import string
import random
import hashlib
import json
import datetime,time
import pytz
from collections import OrderedDict
import re

from bmkb.db import get_mongodb
from bmkb.util import get_errors_in_query



def biomarker_typeahead(query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("typeahead_biomarker",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}
 
    collection = "c_biomarker"
    f_map = {
        "biomarker_id":"biomarker_id",
        "biomarker_canonical_id":"biomarker_canonical_id",
        "biomarker":"biomarker_component.biomarker",
        "biomarker_entity_name":"biomarker_component.assessed_biomarker_entity.recommended_name",
        "biomarker_entity_id":"biomarker_component.assessed_biomarker_entity_id",
        "biomarker_entity_type":"biomarker_component.assessed_entity_type",
        "specimen_name":"biomarker_component.specimen.name",
        "specimen_id":"biomarker_component.specimen.id",
        "specimen_loinc_code":"biomarker_component.specimen.loinc_code",
        "best_biomarker_role":"best_biomarker_role.role",
        "condition_id":"condition.recommended_name.id",
        "condition_name":"condition.recommended_name.name",
        "publication_id":"citation.reference.id"
    }

    res_obj = []
    mongo_query = {}
    for target_field in f_map:
        path = f_map[target_field]
        if query_obj["field_list"] == [target_field]:
            mongo_query = {path:{'$regex': query_obj["value"], '$options': 'i'}}
            path_list = path.split(".")
            for obj in dbh[collection].find(mongo_query):
                val_list = []
                if target_field in ["publication_id"]:
                    for o in obj["citation"]:
                        for oo in o["reference"]:
                            val_list.append(oo["id"])
                elif target_field in ["specimen_id", "specimen_name","specimen_loinc_code"]:
                    for o in obj[path_list[0]]:
                        for oo in o[path_list[1]]:
                            val_list.append(oo[path_list[2]])
                elif target_field in ["best_biomarker_role","biomarker", "biomarker_entity_id", "biomarker_entity_type"]:
                    for o in obj[path_list[0]]:
                        val_list.append(o[path_list[1]])
                elif target_field in ["biomarker_entity_name"]:
                    for o in obj[path_list[0]]:
                        if "recommended_name" in o[path_list[1]]:
                            val_list.append(o[path_list[1]]["recommended_name"])
                elif target_field in ["condition_id", "condition_name"]:
                    o = obj[path_list[0]][path_list[1]]
                    val_list.append(o[path_list[2]])
                elif target_field in ["biomarker_id", "biomarker_canonical_id"]:
                    val_list.append(obj[path_list[0]])
                           
                for val in val_list:
                    if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                        res_obj.append(val)
                        if len(res_obj) >= query_obj["limit"]:
                            return sorted(res_obj)



 
    return sorted(set(res_obj))








