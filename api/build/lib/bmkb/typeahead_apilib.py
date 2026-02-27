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




def global_typeahead(query_obj, config_obj, path_dict):
    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("global_typeahead",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}


    record_type_list = path_dict.keys()
    if "target" in query_obj:
        if query_obj["target"] in path_dict:
            record_type_list = [query_obj["target"]]


    res_obj = []
    for record_type in record_type_list:
        for path in path_dict[record_type]:
            prop_list = path.split(".")
            path_obj = path_dict[record_type][path]
            mongo_query = {path:{'$regex': query_obj["value"], '$options': 'i'}}
            prj_obj = {prop_list[0]:1}
            coll = "c_" + record_type
            for doc in dbh[coll].find(mongo_query, prj_obj):
                if path_obj["type"] == "string":
                    val = doc[prop_list[0]]
                    if val.lower().find(query_obj["value"].lower()) != -1:
                        if val not in res_obj:
                            res_obj.append(val)
                            if len(res_obj) >= query_obj["limit"]:
                                return sorted(res_obj)
                elif path_obj["type"] == "objlist":
                    for o in doc[prop_list[0]]:
                        val = o[prop_list[1]]
                        if path == "gene_names.name":
                            for val in o[prop_list[1]].split(";"):
                                val = val.replace(".", "").strip() 
                                if val.lower().find(query_obj["value"].lower()) != -1:
                                    if val not in res_obj:
                                        res_obj.append(val)
                                        if len(res_obj) >= query_obj["limit"]:
                                            return sorted(res_obj)
                        else:
                            val = o[prop_list[1]]
                            if len(prop_list) == 3:
                                val = o[prop_list[1]][prop_list[2]]
                            if val.lower().find(query_obj["value"].lower()) != -1:
                                if val not in res_obj:
                                    res_obj.append(val)
                                    if len(res_obj) >= query_obj["limit"]:
                                        return sorted(res_obj)
                elif path_obj["type"] == "objlistobjlist":
                    for o in doc[prop_list[0]]:
                        for oo in o[prop_list[1]]:
                            val = oo[prop_list[2]]
                            if val.lower().find(query_obj["value"].lower()) != -1:
                                if val not in res_obj:
                                    res_obj.append(val)
                                    if len(res_obj) >= query_obj["limit"]:
                                        return sorted(res_obj)
                elif path_obj["type"] == "goterms":
                    for cat_obj in doc["go_annotation"]["categories"]:
                        for term_obj in cat_obj["go_terms"]:
                            val = term_obj[prop_list[-1]]
                            if val.lower().find(query_obj["value"].lower()) != -1:
                                if val not in res_obj:
                                    res_obj.append(val)
                                    if len(res_obj) >= query_obj["limit"]:
                                        return sorted(res_obj)


    return sorted(set(res_obj))



def glycan_typeahead(query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("typeahead_glycan",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}

    collection = "c_glycan"

    res_obj = []
    mongo_query = {}
    if query_obj["field_list"] == ["glytoucan_ac"]:
        cond_list = [
            {"glytoucan_ac":{'$regex': query_obj["value"], '$options': 'i'}},
            {"crossref.id":{"$regex": query_obj["value"], "$options":"i"}}
        ]
        mongo_query = { "$or":cond_list}
        prj_obj = {"glytoucan_ac":1, "crossref":1}
        for obj in dbh[collection].find(mongo_query, prj_obj):
            val = obj["glytoucan_ac"]
            if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                res_obj.append(val)
                if len(res_obj) >= query_obj["limit"]:
                    return sorted(res_obj)
            for o in obj["crossref"]:
                val = o["id"]
                if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                    res_obj.append(val)
                    if len(res_obj) >= query_obj["limit"]:
                        return sorted(res_obj)
    elif query_obj["field_list"] == ["enzyme"]:
        cond_list = [
            {"enzyme.uniprot_canonical_ac": {'$regex': query_obj["value"], '$options': 'i'}},
            {"enzyme.gene": {'$regex': query_obj["value"], '$options': 'i'}},
        ]
        mongo_query = { "$or":cond_list}
        prj_obj = {"enzyme":1}
        for obj in dbh[collection].find(mongo_query, prj_obj):
            for o in obj["enzyme"]:
                for val in [o["uniprot_canonical_ac"], o["gene"]]:
                    if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                        res_obj.append(val)
                        if len(res_obj) >= query_obj["limit"]:
                            return sorted(res_obj)
    elif query_obj["field_list"] == ["enzyme_uniprot_canonical_ac"]:
        mongo_query = {"enzyme.uniprot_canonical_ac": {'$regex': query_obj["value"], '$options': 'i'}}
        prj_obj = {"enzyme":1}
        for obj in dbh[collection].find(mongo_query, prj_obj):
            for o in obj["enzyme"]:
                val = o["uniprot_canonical_ac"]
                if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                    res_obj.append(val)
                    if len(res_obj) >= query_obj["limit"]:
                        return sorted(res_obj)
    elif query_obj["field_list"] == ["motif_name"]:
        mongo_query = {"motifs.name": {'$regex': query_obj["value"], '$options': 'i'}}
        prj_obj = {"motifs":1}
        for obj in dbh[collection].find(mongo_query, prj_obj):
            for o in obj["motifs"]:
                val = o["name"]
                if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                    res_obj.append(val)
                    if len(res_obj) >= query_obj["limit"]:
                        return sorted(res_obj)
    elif query_obj["field_list"] == ["glycan_pmid"]:
        mongo_query = {"publication.reference.id": {'$regex': query_obj["value"], '$options': 'i'}}
        prj_obj = {"publication":1}
        for obj in dbh[collection].find(mongo_query, prj_obj):
            for o in obj["publication"]:
                for oo in o["reference"]:
                    val = oo["id"]
                    if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                        res_obj.append(val)
                        if len(res_obj) >= query_obj["limit"]:
                            return sorted(res_obj)
    elif "biomarker_id" in query_obj["field_list"] or "biomarker_name" in query_obj["field_list"]:
        tmp_dict = {"biomarker_id":"biomarker_id", "biomarker_name":"assessed_biomarker_entity"}
        f = tmp_dict[query_obj["field_list"][0]]
        p = "biomarkers." + f
        mongo_query = {p: {'$regex': query_obj["value"], '$options': 'i'}}
        prj_obj = {"biomarkers":1}
        for obj in dbh[collection].find(mongo_query, prj_obj):
            for o in obj["biomarkers"]:
                val = o[f]
                if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                    res_obj.append(val)
                    if len(res_obj) >= query_obj["limit"]:
                        return sorted(res_obj)
    elif query_obj["field_list"] ==  ["biomarker_type"]:
        p = "biomarkers.instances.best_biomarker_type"
        mongo_query = {p: {'$regex': query_obj["value"], '$options': 'i'}}
        prj_obj = {"biomarkers":1}
        for obj in dbh[collection].find(mongo_query, prj_obj):
            for o in obj["biomarkers"]:
                for oo in o["instances"]:
                    val = oo["best_biomarker_type"]
                    if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                        res_obj.append(val)
                        if len(res_obj) >= query_obj["limit"]:
                            return sorted(res_obj)
    elif query_obj["field_list"] ==  ["biomarker_disease_name"]:
        mongo_query = {
            "$or":[
             {"biomarkers.instances.disease.recommended_name.name": {'$regex': query_obj["value"], '$options': 'i'}}
            ,{"biomarkers.instances.disease.synonyms.name": {'$regex': query_obj["value"], '$options': 'i'}}
            ]
        }
        prj_obj = {"biomarkers":1}
        for obj in dbh[collection].find(mongo_query,prj_obj):
            for o in obj["biomarkers"]:
                for oo in o["instances"]:
                    ooo = oo["disease"]
                    val_list = []
                    if "recommended_name" in ooo:
                        val_list.append(ooo["recommended_name"]["name"])
                    if "synonyms" in ooo:
                        for oooo in ooo["synonyms"]:
                            val_list.append(oooo["name"])
                    for val in val_list:
                        if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                            val = val.split("[")[0]
                            res_obj.append(val)
                            if len(res_obj) >= query_obj["limit"]:
                                return sorted(res_obj)
    elif query_obj["field_list"] ==  ["biomarker_disease_id"]:
        mongo_query = {
            "$or":[
             {"biomarkers.instances.disease.recommended_name.id": {'$regex': query_obj["value"], '$options': 'i'}}
            ,{"biomarkers.instances.disease.synonyms.id": {'$regex': query_obj["value"], '$options': 'i'}}
            ]
        }
        prj_obj = {"biomarkers":1}
        for obj in dbh[collection].find(mongo_query,prj_obj):
            for o in obj["biomarkers"]:
                for oo in o["instances"]:
                    val_list = []
                    ooo = oo["disease"]
                    if "recommended_name" in ooo:
                        val_list.append(ooo["recommended_name"]["id"])
                    if "synonyms" in ooo:
                        for oooo in ooo["synonyms"]:
                            val_list.append(oooo["id"])
                    for val in val_list:
                        if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                            val = val.split("[")[0]
                            res_obj.append(val)
                            if len(res_obj) >= query_obj["limit"]:
                                return sorted(res_obj)

    return sorted(set(res_obj))



def protein_typeahead(query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("typeahead_protein",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}
  
    collection = "c_protein"


    res_obj = []
    mongo_query = {}
    
    if query_obj["field_list"] ==  ["uniprot_canonical_ac"]:
        mongo_query = {
            "$or":[
                {"uniprot_canonical_ac":{'$regex': query_obj["value"], '$options': 'i'}}
            ]
        }
        prj_obj = {"uniprot_canonical_ac":1}
        for obj in dbh[collection].find(mongo_query,prj_obj):
            val = obj["uniprot_canonical_ac"]
            if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                res_obj.append(val)
                if len(res_obj) >= query_obj["limit"]:
                    return sorted(res_obj)

    if query_obj["field_list"] ==  ["protein_id"]:
        mongo_query = {
            "$or":[
                {"uniprot_canonical_ac":{'$regex': query_obj["value"], '$options': 'i'}},
                {"refseq.ac":{'$regex': query_obj["value"], '$options': 'i'}},
                {"uniprot_id":{'$regex': query_obj["value"], '$options': 'i'}}
            ]
        }
        prj_obj = {"uniprot_canonical_ac":1, "uniprot_id":1, "refseq":1}
        #return prj_obj
        for obj in dbh[collection].find(mongo_query,prj_obj):
            val = obj["uniprot_canonical_ac"]
            if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                res_obj.append(val)
                if len(res_obj) >= query_obj["limit"]:
                    return sorted(res_obj)
            val = obj["uniprot_id"]
            if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                res_obj.append(val)
                if len(res_obj) >= query_obj["limit"]:
                    return sorted(res_obj)
            if "refseq" in obj:
                if "ac" in obj["refseq"]:
                    val = obj["refseq"]["ac"]
                    if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                        res_obj.append(val)
                        if len(res_obj) >= query_obj["limit"]:
                            return sorted(res_obj)

    

    if query_obj["field_list"] ==  ["go_id"]:
        q_obj = {'$regex': query_obj["value"], '$options': 'i'}
        mongo_query = {"go_annotation.categories.go_terms.id":q_obj}
        prj_obj = {"go_annotation":1}
        for obj in dbh[collection].find(mongo_query,prj_obj):
            for cat_obj in obj["go_annotation"]["categories"]:
                for term_obj in cat_obj["go_terms"]:
                    val = term_obj["id"]
                    if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                        res_obj.append(val)
                        if len(res_obj) >= query_obj["limit"]:
                            return sorted(res_obj)
    if query_obj["field_list"] ==  ["go_term"]:
        q_obj = {'$regex': query_obj["value"], '$options': 'i'}
        mongo_query = {"go_annotation.categories.go_terms.name":q_obj}
        prj_obj = {"go_annotation":1}
        for obj in dbh[collection].find(mongo_query,prj_obj):
            for cat_obj in obj["go_annotation"]["categories"]:
                for term_obj in cat_obj["go_terms"]:
                    val = term_obj["name"]
                    if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                        res_obj.append(val)
                        if len(res_obj) >= query_obj["limit"]:
                            return sorted(res_obj)
    if query_obj["field_list"] ==  ["uniprot_id"]:
        mongo_query = {"uniprot_id":{'$regex': query_obj["value"], '$options': 'i'}}
        prj_obj = {"uniprot_id":1}
        for obj in dbh[collection].find(mongo_query,prj_obj):
            val = obj["uniprot_id"]
            if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                res_obj.append(val)
                if len(res_obj) >= query_obj["limit"]:
                    return sorted(res_obj)
    if query_obj["field_list"] ==  ["refseq_ac"]:
        mongo_query = {"refseq.ac":{'$regex': query_obj["value"], '$options': 'i'}}
        prj_obj = {"refseq":1}
        for obj in dbh[collection].find(mongo_query,prj_obj):
            val = obj["refseq"]["ac"] if "ac" in obj["refseq"] else ""
            if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                res_obj.append(val)
                if len(res_obj) >= query_obj["limit"]:
                    return sorted(res_obj)
    elif query_obj["field_list"] ==  ["gene_name"]:
        mongo_query = {"gene_names.name": {'$regex': query_obj["value"], '$options': 'i'}}
        prj_obj = {"gene":1}
        for obj in dbh[collection].find(mongo_query,prj_obj):
            for o in obj["gene"]:
                if o["name"].lower().find(query_obj["value"].lower()) != -1:
                    for name_part in o["name"].split(";"):
                        val = name_part.replace(".", "").strip()
                        if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                            res_obj.append(val)
                            if len(res_obj) >= query_obj["limit"]:
                                return sorted(res_obj)
    elif query_obj["field_list"] ==  ["protein_name"]:
        mongo_query = {"protein_names.name": {'$regex': query_obj["value"], '$options': 'i'}}
        prj_obj = {"protein_names":1}
        for obj in dbh[collection].find(mongo_query,prj_obj):
            for o in obj["protein_names"]:
                val = o["name"]
                if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                    res_obj.append(val)
                    if len(res_obj) >= query_obj["limit"]:
                        return sorted(res_obj)
    elif query_obj["field_list"] ==  ["disease_name"]:
        mongo_query = {
            "$or":[
            {"disease.recommended_name.name": {'$regex': query_obj["value"], '$options': 'i'}}
            ,{"disease.synonyms.name": {'$regex': query_obj["value"], '$options': 'i'}}
            ]
        }
        prj_obj = {"disease":1}
        for obj in dbh[collection].find(mongo_query,prj_obj):
            for o in obj["disease"]:
                val_list = []
                if "recommended_name" in o:
                    val_list.append(o["recommended_name"]["name"])
                if "synonyms" in o:
                    for oo in o["synonyms"]:
                        val_list.append(oo["name"])
                for val in val_list:
                    if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                        val = val.split("[")[0]
                        res_obj.append(val)
                        if len(res_obj) >= query_obj["limit"]:
                            return sorted(res_obj)
    elif query_obj["field_list"] ==  ["disease_id"]:
        mongo_query = {
            "$or":[
            {"disease.recommended_name.id": {'$regex': query_obj["value"], '$options': 'i'}}
            ,{"disease.synonyms.id": {'$regex': query_obj["value"], '$options': 'i'}}
            ]
        }
        prj_obj = {"disease":1}
        for obj in dbh[collection].find(mongo_query,prj_obj):
            for o in obj["disease"]:
                val_list = []
                if "recommended_name" in o:
                    val_list.append(o["recommended_name"]["id"])
                if "synonyms" in o:
                    for oo in o["synonyms"]:
                        val_list.append(oo["id"])
                for val in val_list:
                    if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                        val = val.split("[")[0]
                        res_obj.append(val)
                        if len(res_obj) >= query_obj["limit"]:
                            return sorted(res_obj)
    elif query_obj["field_list"] ==  ["pathway_name"]:
        mongo_query = {"pathway.name": {'$regex': query_obj["value"], '$options': 'i'}}
        prj_obj = {"pathway":1}
        for obj in dbh[collection].find(mongo_query,prj_obj):
            for o in obj["pathway"]:
                val = o["name"]
                if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                    res_obj.append(val)
                    if len(res_obj) >= query_obj["limit"]:
                        return sorted(res_obj)
    elif query_obj["field_list"] ==  ["pathway_id"]:
        mongo_query = {"pathway.id": {'$regex': query_obj["value"], '$options': 'i'}}
        prj_obj = {"pathway":1}
        for obj in dbh[collection].find(mongo_query,prj_obj):
            for o in obj["pathway"]:
                val = o["id"]
                if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                    res_obj.append(val)
                    if len(res_obj) >= query_obj["limit"]:
                        return sorted(res_obj)
    elif query_obj["field_list"] ==  ["pdb_id"]:
        prj_obj = {"structures":1}
        qry = query_obj["value"]
        prefix_flag = True
        regex_pattern = f"^{re.escape(qry)}" if prefix_flag else f"{re.escape(qry)}"
        #mongo_query = {"structures.pdb_id": {'$regex': regex_pattern, '$options':'i'}}
        mongo_query = {"structures.pdb_id": {'$regex': regex_pattern}}
        #doc_list = list(dbh[collection].find(mongo_query,prj_obj).limit(100))
        #return [str(len(doc_list))]
        for obj in dbh[collection].find(mongo_query,prj_obj).limit(100):
            for o in obj["structures"]:
                val = o["pdb_id"]
                if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                    res_obj.append(val)
                    if len(res_obj) >= query_obj["limit"]:
                        return sorted(res_obj)
    elif query_obj["field_list"] ==  ["protein_pmid"]:
        mongo_query = {"publication.reference.id": {'$regex': query_obj["value"], '$options': 'i'}}
        prj_obj = {"publication":1}
        for obj in dbh[collection].find(mongo_query, prj_obj):
            for o in obj["publication"]:
                for oo in o["reference"]:
                    val = oo["id"]
                    if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                        res_obj.append(val)
                        if len(res_obj) >= query_obj["limit"]:
                            return sorted(res_obj) 
    elif "biomarker_id" in query_obj["field_list"] or "biomarker_name" in query_obj["field_list"]:
        tmp_dict = {"biomarker_id":"biomarker_id", "biomarker_name":"assessed_biomarker_entity"}
        f = tmp_dict[query_obj["field_list"][0]]
        p = "biomarkers." + f
        mongo_query = {p: {'$regex': query_obj["value"], '$options': 'i'}}
        prj_obj = {"biomarkers":1}
        for obj in dbh[collection].find(mongo_query, prj_obj):
            for o in obj["biomarkers"]:
                val = o[f]
                if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                    res_obj.append(val)
                    if len(res_obj) >= query_obj["limit"]:
                        return sorted(res_obj)
    elif query_obj["field_list"] == ["biomarker_type"]:
        p = "biomarkers.instances.best_biomarker_type"
        mongo_query = {p: {'$regex': query_obj["value"], '$options': 'i'}}
        prj_obj = {"biomarkers":1}
        for obj in dbh[collection].find(mongo_query, prj_obj):
            for o in obj["biomarkers"]:
                for oo in o["instances"]:
                    val = oo["best_biomarker_type"]
                    if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                        res_obj.append(val)
                        if len(res_obj) >= query_obj["limit"]:
                            return sorted(res_obj) 
    elif query_obj["field_list"] ==  ["biomarker_disease_name"]:
        mongo_query = {
            "$or":[
             {"biomarkers.condition.recommended_name.name": {'$regex': query_obj["value"], '$options': 'i'}}
            ,{"biomarkers.condition.name_list": {'$regex': query_obj["value"], '$options': 'i'}}
            ]
        }
        prj_obj = {"biomarkers":1}
        for obj in dbh[collection].find(mongo_query,prj_obj):
            for o in obj["biomarkers"]:
                val_list = []
                d_obj = o["condition"]
                if "recommended_name" in d_obj:
                    val_list.append(d_obj["recommended_name"]["name"])
                if "name_list" in d_obj:
                    for val in d_obj["name_list"]:
                        val_list.append(val)
                for val in val_list:
                    if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                        val = val.split("[")[0]
                        res_obj.append(val)
                        if len(res_obj) >= query_obj["limit"]:
                            return sorted(res_obj)
    elif query_obj["field_list"] ==  ["biomarker_disease_id"]:
        mongo_query = {
            "$or":[
             {"biomarkers.condition.recommended_name.id": {'$regex': query_obj["value"], '$options': 'i'}}
            ,{"biomarkers.condition.id_list": {'$regex': query_obj["value"], '$options': 'i'}}
            ]
        }
        prj_obj = {"biomarkers":1}
        for obj in dbh[collection].find(mongo_query,prj_obj):
            for o in obj["biomarkers"]:
                val_list = []
                d_obj = o["condition"]
                if "recommended_name" in d_obj:
                    val_list.append(d_obj["recommended_name"]["id"])
                if "id_list" in d_obj:
                    for val in d_obj["id_list"]:
                        val_list.append(val)
                for val in val_list:
                    if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                        val = val.split("[")[0]
                        res_obj.append(val)
                        if len(res_obj) >= query_obj["limit"]:
                            return sorted(res_obj)
    elif sorted(query_obj["field_list"]) == sorted(["pathway_id", "pathway_name", "pathway_description"]):
        mongo_query = {"$or":[
                 {"pathway.id": {'$regex': query_obj["value"], '$options': 'i'}}
                ,{"pathway.description": {'$regex': query_obj["value"], '$options': 'i'}}
            ]
        }
        prj_obj = {"pathway":1}

        for obj in dbh[collection].find(mongo_query,prj_obj).limit(100):
            for o in obj["pathway"]:
                for f in ["id", "name","description"]:
                    val = o[f] if f in o else ""
                    if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                        res_obj.append(val)
                        if len(res_obj) >= query_obj["limit"]:
                            return sorted(res_obj)

    elif sorted(query_obj["field_list"]) ==  sorted(["disease_id", "disease_name"]):
        mongo_query = {"$or":[
            {"disease.recommended_name.name": {'$regex': query_obj["value"], '$options': 'i'}}
            ,{"disease.recommended_name.id": {'$regex': query_obj["value"], '$options': 'i'}}
            ,{"disease.synonyms.name": {'$regex': query_obj["value"], '$options': 'i'}}
            ,{"disease.synonyms.id": {'$regex': query_obj["value"], '$options': 'i'}}
        ]}
        prj_obj = {"disease":1}
        for obj in dbh[collection].find(mongo_query,prj_obj):
            for o in obj["disease"]:
                val_list = []
                if "recommended_name" in o:
                    val_list.append(o["recommended_name"]["name"])
                    val_list.append(o["recommended_name"]["id"])
                if "synonyms" in o:
                    for oo in o["synonyms"]:
                        val_list.append(oo["name"])
                        val_list.append(oo["id"])
                for val in val_list:
                    if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                        val = val.split("[")[0]
                        res_obj.append(val)
                        if len(res_obj) >= query_obj["limit"]:
                            return sorted(res_obj)
    elif sorted(query_obj["field_list"]) == sorted(["tax_id", "tax_name"]):
        mongo_query = {"$or":[
                 {"species.taxid": {'$regex': query_obj["value"], '$options': 'i'}}
                ,{"species.name": {'$regex': query_obj["value"], '$options': 'i'}}
                ,{"species.common_name": {'$regex': query_obj["value"], '$options': 'i'}}
                ,{"species.bmkb.name": {'$regex': query_obj["value"], '$options': 'i'}}
                ,{"species.reference_species": {'$regex': query_obj["value"], '$options': 'i'}}
            ]
        }
        prj_obj = {"species":1}
        for obj in dbh[collection].find(mongo_query,prj_obj).limit(100):
            for o in obj["species"]:
                for f in ["taxid", "name", "common_name", "bmkb.name", "reference_species"]:
                    val = str(o[f]) if f in o else ""
                    if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                        res_obj.append(val)
                        if len(res_obj) >= query_obj["limit"]:
                            return sorted(res_obj)
    elif sorted(query_obj["field_list"]) == sorted(["go_id", "go_term"]):
        mongo_query = {"$or":[
                 {"go_annotation.categories.go_terms.id": {'$regex': query_obj["value"], '$options': 'i'}}
                ,{"go_annotation.categories.go_terms.name": {'$regex': query_obj["value"], '$options': 'i'}}
            ]
        }
        prj_obj = {"go_annotation":1}
        for obj in dbh[collection].find(mongo_query,prj_obj):
            for cat_obj in obj["go_annotation"]["categories"]:
                for term_obj in cat_obj["go_terms"]:
                    for f in ["id", "name"]:
                        val = term_obj[f] if f in term_obj else ""
                        if val.lower().find(query_obj["value"].lower()) != -1 and val not in res_obj:
                            res_obj.append(val)
                            if len(res_obj) >= query_obj["limit"]:
                                return sorted(res_obj)


    return sorted(set(res_obj))


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




def categorized_typeahead(query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("categorized_typeahead",query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}
  
    collection = "c_protein"

    mongo_query = {}
    if query_obj["field"] == "go_term":
        mongo_query = {"go_annotation.categories.go_terms.name":{'$regex': query_obj["value"], '$options': 'i'}}
        hit_dict = {}
        seen = {}
        total = 0
        limit_one = query_obj["total_limit"]
        limit_two = query_obj["categorywise_limit"]

        prj_obj = {"go_annotation":1}
        for obj in dbh[collection].find(mongo_query, prj_obj):
            for cat_obj in obj["go_annotation"]["categories"]:
                cat = cat_obj["name"]
                for term_obj in cat_obj["go_terms"]:
                    term = term_obj["name"]
                    if term.lower().find(query_obj["value"].lower()) != -1:
                        if cat not in hit_dict:
                            hit_dict[cat] = []
                            seen[cat] = {}
                        if term not in seen[cat] and len(hit_dict[cat]) < limit_two:
                            o = {"label":term, "category":cat}
                            hit_dict[cat].append(o)
                            seen[cat][term] = True
                            total += 1
                        if total >= limit_one:
                            break
    res_obj = []
    for cat in hit_dict:
        for o in hit_dict[cat]:
            res_obj.append(o)

    return res_obj




