import os
import csv
import string
import json
import random
from collections import OrderedDict
import gzip
import io
import pymongo
import datetime
import pytz
import hashlib




def load_sheet(sheet_obj, in_file, separator):

    seen = {}
    sheet_obj["fields"] = []
    sheet_obj["data"] = []
    with open(in_file, 'r') as FR:
        csv_grid = csv.reader(FR, delimiter=separator, quotechar='\"')
        row_count = 0
        for row in csv_grid:
            if json.dumps(row) in seen:
                continue
            seen[json.dumps(row)] = True
            row_count += 1
            if row_count == 1:
                for j in range(0, len(row)):
                    sheet_obj["fields"].append(row[j].strip().replace("\"", ""))
            else:
                new_row = []
                for j in range(0, len(row)):
                    new_row.append(row[j].strip())
                sheet_obj["data"].append(new_row)
    return


def apply_pagination(obj_list, req_obj):

    offset = req_obj["offset"] if "offset" in req_obj else 1
    limit = req_obj["limit"] if "limit" in req_obj else 20
    start_index = int(offset) - 1
    stop_index = start_index + int(limit)
    start_index = 0 if start_index > len(obj_list) - 1 else start_index
    stop_index = len(obj_list) if stop_index > len(obj_list) else stop_index
    return obj_list[start_index:stop_index]


    


def get_query_filter_code(dbh, query_filters, record_type, filter_conf):


    code_dict = {}
    for grp in sorted(filter_conf[record_type]):
        code_dict[grp] = []
        sorted_dict = dict(sorted(filter_conf[record_type][grp]["order_dict"].items(), key=lambda item: item[1]))
        for val in sorted_dict:
            if val != "":
                code_dict[grp].append({"value":val, "ptrn":"*"})

    for obj in query_filters:
        grp = obj["id"]
        for val in obj["selected"]:
            if grp in code_dict:
                for o in code_dict[grp]:
                    if o["value"] == val:
                        o["ptrn"] = "1"
   
    code_list = []
    grp_id_list = get_grp_id_list(record_type, filter_conf)
    
    for grp in grp_id_list:
        c_list = []
        for o in code_dict[grp]:
            c_list.append(o["ptrn"])
        code_list.append("".join(c_list))

    return {"dict":code_dict, "code":".".join(code_list)}



def validate_uploaded_table(in_table, table_type):

    res = {}
    err_list = []
    if table_type == "isoform_mapper":
        f_list = in_table[0]
        for idx in range(1, len(in_table)):
            row =  in_table[idx]
            if len(row) != len(f_list):
                err_list.append({"error_code":"bad-row", "row_index":idx})
            aa_pos = row[f_list.index("amino_acid_pos")]
            if aa_pos.isdigit() == False:
                err_list.append({"error_code":"bad-amino-acid-pos-value", "row_index":idx}) 
    
    res = {"error_list":err_list, "result_count":0} if len(err_list) > 0 else {}
    return res











def get_req_obj(request):

    query_str, arg = None, "query"
    if request.method == "GET":
        if request.args.get(arg):
            query_str = request.args.get(arg)
    elif request.method == "POST":
        if arg in request.values:
            if request.values[arg]:
                query_str = request.values[arg]
    
    req_obj = {}
    if query_str == None:
        try:
            req_obj = request.json
        except Exception as e:
            return {"error_list":[{"error_code":"bad-request-json"}]}
    else:
        try:
            req_obj = json.loads(query_str)
        except Exception as e:
            return {"error_list":[{"error_code":"bad-request-json"}]}

    if req_obj != None and type(req_obj) is dict:
        trim_object(req_obj)
    return  req_obj




def get_random_string(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))



def is_valid_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
        return False
    return True

def isint(value):
  try:
    int(value)
    return True
  except ValueError:
    return False


def get_hit_score(doc, cache_info, score_dict, selected_p_list, hit_info):

    ms_max, scale = 10000, 400.0
    search_query = cache_info["query"]
    if "concept_query_list" in cache_info["query"]:
        search_query = cache_info["query"]["concept_query_list"]
    record_type = cache_info["record_type"]
    search_type = cache_info["search_type"]

    cond_match_freq = {}
    if record_type == "biomarker":
        cond_group, cond = "direct_boolean", ""
        for cond in score_dict[record_type][cond_group]:
            p_list = score_dict[record_type][cond_group][cond]["fieldlist"]
            for p in p_list:
                if p not in selected_p_list:
                    continue
                if doc[p] == "yes":
                    cond_match_freq[cond] = 1
        cond_group, cond = "direct_numeric", ""
        for cond in score_dict[record_type][cond_group]:
            p_list = score_dict[record_type][cond_group][cond]["fieldlist"]
            for p in p_list:
                if p not in selected_p_list:
                    continue
                n = doc[p]
                if n > 0:
                    cond_match_freq[cond] = n

    debug_list = []
    score = 0.0
    for cond_group in score_dict[record_type]:
        for cond in score_dict[record_type][cond_group]:
            raw_freq = cond_match_freq[cond] if cond in cond_match_freq else 0
            freq = round(float(raw_freq)/100.00,3)
            weight = score_dict[record_type][cond_group][cond]["weight"]
            score += weight * freq
            debug_list.append({"c":cond, "w":weight, "f":freq})
            if freq > 0.0:
                hit_info["freqdict"][cond] = freq

    return round(float(score), 2), cond_match_freq




def get_arg_value(arg, method):


    if method == "GET":
        if request.args.get(arg):
            return request.args.get(arg)
    elif method == "POST":
        if arg in request.values:
            if request.values[arg]:
                return request.values[arg]
    return ""



def trim_object(obj):
    for key in obj:
        if type(obj[key]) is str:
            obj[key] = obj[key].strip()
    
    return




def order_obj(json_obj, ordr_dict):


    for k1 in json_obj:
        ordr_dict[k1] = ordr_dict[k1] if k1 in ordr_dict else 1000
        if type(json_obj[k1]) is dict:
            for k2 in json_obj[k1]:
                ordr_dict[k2] = ordr_dict[k2] if k2 in ordr_dict else 1000
                if type(json_obj[k1][k2]) is dict:
                    for k3 in json_obj[k1][k2]:
                        ordr_dict[k3] = ordr_dict[k3] if k3 in ordr_dict else 1000
                    json_obj[k1][k2] = OrderedDict(sorted(json_obj[k1][k2].items(),
                        key=lambda x: float(ordr_dict.get(x[0]))))
                elif type(json_obj[k1][k2]) is list:
                    for j in range(0, len(json_obj[k1][k2])):
                        if type(json_obj[k1][k2][j]) is dict:
                            for k3 in json_obj[k1][k2][j]:
                                ordr_dict[k3] = ordr_dict[k3] if k3 in ordr_dict else 1000
                                #json_obj[k1][k2][j] = OrderedDict(sorted(json_obj[k1][k2][j].items(),
                                #key=lambda x: float(ordr_dict.get(x[0]))))
            json_obj[k1] = OrderedDict(sorted(json_obj[k1].items(),
                key=lambda x: float(ordr_dict.get(x[0]))))

    return OrderedDict(sorted(json_obj.items(), key=lambda x: float(ordr_dict.get(x[0]))))



def order_list(list_obj, ordr_dict):

    for val in list_obj:
        if val not in ordr_dict:
            ordr_dict[val] = 10000

    return sorted(list_obj, key=lambda ordr: ordr_dict[ordr], reverse=False)



def sort_objects(obj_list, return_fields, field_name, order_type):

    field_list = return_fields["float"] + return_fields["int"] + return_fields["string"]
    grid_obj = {}
    for f in field_list:
        grid_obj[f] = []
    for i in range(0, len(obj_list)):
        obj = obj_list[i]
        if field_name in return_fields["float"]:
            if field_name not in obj:
                obj[field_name] = -1.0
            grid_obj[field_name].append({"index":i, field_name:float(obj[field_name])})
        elif field_name in return_fields["string"]:
            if field_name not in obj:
                obj[field_name] = ""
            grid_obj[field_name].append({"index":i, field_name:obj[field_name]})
        elif field_name in return_fields["int"]:
            if field_name not in obj:
                obj[field_name] = -1
            grid_obj[field_name].append({"index":i, field_name:int(obj[field_name])})
    reverse_flag = True if order_type == "desc" else False
    key_list = []
    sorted_obj_list = sorted(grid_obj[field_name], key=lambda x: x[field_name], reverse=reverse_flag)
    for o in sorted_obj_list:
            key_list.append(o["index"])
    return key_list

def get_field_value(obj, field_name):

    field_value = obj[field_name] if field_name in obj else ""
    if field_name.find(".") != -1:
        ff_list = field_name.split(".")
        field_value = obj[ff_list[0]]
        for ff in ff_list[1:]:
            if ff in field_value:
                field_value = field_value[ff]
    return field_value


def sort_objects_new(obj_list, field_name, order_type):

    return_fields = {"float":[], "int":[], "string":[]}
    for obj in obj_list:
        for k in obj:
            if type(obj[k]) is float:
                return_fields["float"].append(k)
            if type(obj[k]) is int:
                return_fields["int"].append(k)
            if type(obj[k]) is str:
                return_fields["string"].append(k)
            if type(obj[k]) is dict:
                o = obj[k]
                for kk in o:
                    if type(o[kk]) is float:
                        return_fields["float"].append(k + "." + kk)
                    if type(o[kk]) is int:
                        return_fields["int"].append(k + "." + kk)
                    if type(o[kk]) is str:
                        return_fields["string"].append(k + "." + kk)
    for k in return_fields:
        return_fields[k] = list(set(return_fields[k]))


    field_list = return_fields["float"] + return_fields["int"] + return_fields["string"]
    grid_obj = {}
    for f in field_list:
        grid_obj[f] = []
    for i in range(0, len(obj_list)):
        obj = obj_list[i]
        if field_name in return_fields["float"]:
            field_value = get_field_value(obj, field_name)
            field_value = float(field_value) if field_value != "" else -1.0
            grid_obj[field_name].append({"index":i, field_name:field_value})
        elif field_name in return_fields["string"]:
            field_value = get_field_value(obj, field_name)
            field_value = str(field_value) if field_value != "" else ""
            grid_obj[field_name].append({"index":i, field_name:field_value})
        elif field_name in return_fields["int"]:
            field_value = get_field_value(obj, field_name)
            field_value = int(field_value) if field_value != "" else -1
            grid_obj[field_name].append({"index":i, field_name:field_value})
        else:
            if field_name not in grid_obj:
                grid_obj[field_name] = []
            if field_name not in obj:
                obj[field_name] = ""
            grid_obj[field_name].append({"index":i, field_name:obj[field_name]})
   
 
    reverse_flag = True if order_type == "desc" else False
    key_list = []
    sorted_obj_list = sorted(grid_obj[field_name], key=lambda x: x[field_name], reverse=reverse_flag)
    for o in sorted_obj_list:
        key_list.append(o["index"])
    #return {"grid":grid_obj[field_name], "keylist":key_list}
    return key_list


def extract_name(obj_list, name_type, resource):
   
    if obj_list == []:
        return ""
    
    name_list_dict = {"recommended":[], "synonym":[]}
    for obj in obj_list:
        if obj["resource"] == resource:
            name_list_dict[obj["type"]].append(obj["name"])


    
    if name_type == "recommended" and name_list_dict["recommended"] == []:
        name_list_dict["recommended"] += name_list_dict["synonym"]


    if name_type == "all":
        return "; ".join(name_list_dict["recommended"] + name_list_dict["synonym"])
    else:
        return "; ".join(name_list_dict[name_type])




#######################
def clean_obj(obj, prop_list, obj_type):


    #First perform custom cleaning
    if obj_type == "c_protein":
        if "mass" in obj:
            if "monoisotopic_mass" in obj["mass"]:
                obj["mass"].pop("monoisotopic_mass")
        if "sequence" in obj:
            if "header" in obj["sequence"]:
                obj["sequence"].pop("header")
        if "isoforms" in obj:
            for o in obj["isoforms"]:
                if "header" in o["sequence"]:
                    o["sequence"].pop("header")

    for key in prop_list:
        if key in obj:
             obj.pop(key)


    #Now clean up empty valued properties
    if type(obj) is dict:
        key_list = list(obj.keys())
        for k1 in key_list:
            if obj[k1] in["", [], {}]:
                obj.pop(k1)
            elif type(obj[k1]) in [dict, list]:
                clean_obj(obj[k1], [], obj_type)
    elif type(obj) is list:
        for k1 in range(0, len(obj)):
            if obj[k1] in["", [], {}]:
                del obj[k1]
            elif type(obj[k1]) in [dict, list]:
                clean_obj(obj[k1], [], obj_type)
    
   
    return





def gzip_str(string_):
      
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode='w') as fo:
        fo.write(string_.encode())
    bytes_obj = out.getvalue()
    return bytes_obj



def make_list_objects_direct(query_obj, config_obj, limit_flag):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("cached_list", query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}

    cache_collection = "c_initcache"
    res_obj = {}
    default_hash = {"offset":1, "limit":20, "sort":"hit_score", "order":"desc"}
    for key in default_hash:
        if key not in query_obj:
            query_obj[key] = default_hash[key]

    #Get cached object
    mongo_query = {}
    if "id" in query_obj:
        mongo_query["list_id"] = query_obj["id"]
    cached_obj = dbh[cache_collection].find_one(mongo_query)

    #check for post-access error, error_list should be empty upto this line
    post_error_list = []
    if cached_obj == None:
        post_error_list.append({"error_code":"non-existent-search-results"})
        return {"error_list":post_error_list}
  
    if "category" in query_obj:
        k = query_obj["category"] + "_legends"
        cached_obj["cache_info"]["legends"] = cached_obj["cache_info"][k]
        cached_obj["cache_info"].pop("mapped_legends")
        cached_obj["cache_info"].pop("unmapped_legends")


    cached_obj["results"] = [] 
    id_list = []
    x = 0
    for doc in dbh[cache_collection].find(mongo_query):
        for obj in doc["results"]:
            x += 1
            if "hit_score" not in obj:
                obj["hit_score"] = -1
            if "category" in query_obj:
                if query_obj["category"] == obj["category"]:
                    obj.pop("category")
                    cached_obj["results"].append(obj)
            else:
                cached_obj["results"].append(obj)
  
    res_obj = {"cache_info":cached_obj["cache_info"]}
    res_obj["results"] = []
    res_obj["pagination"] = {
        "offset":query_obj["offset"], 
        "limit":query_obj["limit"],
        "total_length":len(cached_obj["results"]), 
        "x":x,
        "sort":query_obj["sort"], 
        "order":query_obj["order"]
    }
    if len(cached_obj["results"]) == 0:
        return res_obj


    return_fields = {"string":[], "int":[], "float":[]}
    f_list = cached_obj["results"][0].keys() if cached_obj["results"] != []  else []
    for f in f_list:
        if type(cached_obj["results"][0][f]) is str:
            return_fields["string"].append(f)
        elif type(cached_obj["results"][0][f]) is int:
            return_fields["int"].append(f)
        elif type(cached_obj["results"][0][f]) is float:
            return_fields["float"].append(f)


    sorted_id_list = sort_objects(cached_obj["results"], return_fields,
                                        query_obj["sort"], query_obj["order"])

    #check for post-access error, error_list should be empty upto this line
    if int(query_obj["offset"]) < 1 or int(query_obj["offset"]) > len(cached_obj["results"]):
        post_error_list.append({"error_code":"invalid-parameter-value", "field":"offset"})
        return {"error_list":post_error_list}

    start_index = int(query_obj["offset"]) - 1
    stop_index = start_index + int(query_obj["limit"])
    sorted_id_list = sorted_id_list[start_index:stop_index] if limit_flag else sorted_id_list
    for obj_id in sorted_id_list:
        obj = cached_obj["results"][obj_id]
        for k in ["_id", "record_id"]:
            if k in obj:
                obj.pop(k)
        res_obj["results"].append(order_obj(obj, config_obj["objectorder"]["glycan"]))
    res_obj["pagination"]["total_length"] = len(cached_obj["results"])

    return res_obj



def make_motif_list_objects_direct(query_obj, config_obj):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    #Collect errors 
    error_list = get_errors_in_query("cached_list", query_obj, config_obj)
    if error_list != []:
        return {"error_list":error_list}

    res_obj = {}
    default_hash = {"offset":1, "limit":20, "sort":"hit_score", "order":"desc"}
    for key in default_hash:
        if key not in query_obj:
            query_obj[key] = default_hash[key]

    #Get cached object
    mongo_query = {"record_type":"motif"}
    cached_obj = {}
    cached_obj["results"] = [] 
    id_list = []
    for doc in dbh["c_list"].find(mongo_query):
        cached_obj["results"].append(doc)

    if len(cached_obj["results"]) == 0:
        return {"error_list":[{"error_code":"no records found"}]}

    return_fields = {"string":[], "int":[], "float":[]}
    for f in cached_obj["results"][0].keys():
        if type(cached_obj["results"][0][f]) is str:
            return_fields["string"].append(f)
        elif type(cached_obj["results"][0][f]) is int:
            return_fields["int"].append(f)
        elif type(cached_obj["results"][0][f]) is float:
            return_fields["float"].append(f)


    sorted_id_list = sort_objects(cached_obj["results"], return_fields,
                                        query_obj["sort"], query_obj["order"])
    
    res_obj = {"cache_info":{"query":{}}}
    if len(cached_obj["results"]) == 0:
        return {}

    #check for post-access error, error_list should be empty upto this line
    if int(query_obj["offset"]) < 1 or int(query_obj["offset"]) > len(cached_obj["results"]):
        post_error_list.append({"error_code":"invalid-parameter-value", "field":"offset"})
        return {"error_list":post_error_list}

    start_index = int(query_obj["offset"]) - 1
    stop_index = start_index + int(query_obj["limit"])
    res_obj["results"] = []
    for obj_id in sorted_id_list[start_index:stop_index]:
        obj = cached_obj["results"][obj_id]
        for k in ["_id", "record_id"]:
            if k in obj:
                obj.pop(k)
        res_obj["results"].append(order_obj(obj, config_obj["objectorder"]["glycan"]))

    res_obj["pagination"] = {"offset":query_obj["offset"], "limit":query_obj["limit"],
        "total_length":len(cached_obj["results"]), "sort":query_obj["sort"], "order":query_obj["order"]}

    return res_obj




def load_species_info(species_obj, in_file):

    data_frame = {}
    load_sheet(data_frame, in_file, ",")
    f_list = data_frame["fields"]
    for row in data_frame["data"]:
        obj = {}
        for f in f_list:
            obj[f] = row[f_list.index(f)]
        tax_id = obj["tax_id"]
        short_name = obj["short_name"]
        if tax_id not in species_obj:
            species_obj[tax_id] = {}
            species_obj[short_name] = {}
        for f in obj:
            species_obj[tax_id][f] = int(obj[f]) if f == "tax_id" else obj[f]
            species_obj[short_name][f] = int(obj[f]) if f == "tax_id" else obj[f]

    return



def get_filter_conf(dbh):


    label_dict, order_dict = {}, {}
    species_obj = {}
    init_obj = dbh["c_init"].find_one({})


    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, "bmkb/conf/list_filters.json")
    filter_conf = json.loads(open(json_url, "r").read())
    for record_type in filter_conf:
        if "by_organism" not in filter_conf[record_type]:
            continue
        filter_conf[record_type]["by_organism"]["label_dict"] = label_dict
        filter_conf[record_type]["by_organism"]["order_dict"] = order_dict

    return filter_conf


def get_final_fields(query_obj, record_type):

    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, "bmkb/conf/list_init.json")
    list_init_conf = json.loads(open(json_url, "r").read())
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, "bmkb/conf/hit_scoring.json")
    score_dict = json.loads(open(json_url, "r").read())

    f_dict = {}
    for rt in list_init_conf:
        f_dict[rt] = {"all":[], "required":[], "default":[]}
        for o in list_init_conf[rt]["columns"]:
            field, is_default, is_required = o["id"], o["default"], o["immutable"]
            if field not in f_dict[rt]["all"]:
                f_dict[rt]["all"].append(field)
            if is_default and field not in f_dict[rt]["default"]:
                f_dict[rt]["default"].append(field)
            if is_required and field not in f_dict[rt]["required"]:
                f_dict[rt]["required"].append(field)
    query_fields = []
    if "columns" in query_obj:
        for f in query_obj["columns"]:
            if f in f_dict[record_type]["all"] and f not in query_fields:
                query_fields.append(f)
    final_fields = ["filter_code","record_id"]
    if record_type in f_dict:
        if len(query_fields) == 0:
            final_fields +=  sorted(set(f_dict[record_type]["required"] + f_dict[record_type]["default"]))
        else:
            final_fields +=  sorted(set(f_dict[record_type]["required"] + query_fields))

    extra_fields = []
    for cat in score_dict[record_type]:
        for f in score_dict[record_type][cat]:
            if "fieldlist" not in score_dict[record_type][cat][f]:
                continue
            ll = score_dict[record_type][cat][f]["fieldlist"]
            for ff in score_dict[record_type][cat][f]["fieldlist"]:
                if ff not in final_fields:
                    extra_fields.append(ff)
    final_fields += extra_fields

    return final_fields, extra_fields





def make_list_objects_indirect(dbh, query_obj, config_obj, limit_flag):


    if "id" not in query_obj:
        return {"error_list":[{"error_code":"missing-parameter-id"}]}

    if query_obj["id"] == "":
        return {"error_list":[{"error_code":"empty-list-id"}]}

    res_obj = {}
    default_hash = {"offset":1, "limit":20, "sort":"hit_score", "order":"desc"}
    for key in default_hash:
        if key not in query_obj:
            query_obj[key] = default_hash[key]



    ts_format = "%Y-%m-%d %H:%M:%S %Z%z"
    ts_list = []
    ts_list.append("0-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))

    #Get cached object
    cache_collection = "c_initcache"
    cache_id = query_obj["id"]
    mongo_query = {"list_id":cache_id}
    cached_obj = dbh[cache_collection].find_one(mongo_query)
   

    #check for post-access error, error_list should be empty upto this line
    post_error_list = []
    if cached_obj == None:
        post_error_list.append({"error_code":"non-existent-search-results"})
        return {"error_list":post_error_list}

    cache_info = cached_obj["cache_info"]
    record_type = cache_info["record_type"]

 
    ts_list.append("1-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))

   
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, "bmkb/conf/hit_scoring.json")
    score_dict = json.loads(open(json_url, "r").read())

    final_fields, extra_fields = get_final_fields(query_obj, record_type)


    prj_obj = {"hit_score":1}
    for f in final_fields:
        prj_obj[f] = 1

    if final_fields == ["filter_code"]:
        prj_obj = {}
    #prj_obj = {"record_id":1, "filter_code":1}


    filter_conf = get_filter_conf(dbh)
    query_filters = query_obj["filters"] if "filters" in query_obj else []
    res = get_query_filter_code(dbh,query_filters, record_type, filter_conf)

    query_filter_code, code_dict = res["code"], res["dict"]

    ts_list.append("2-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))
   
    cached_obj["results"] = get_list_objects(dbh,cache_id, cache_info,cache_collection,
            final_fields,score_dict, prj_obj, config_obj)
 

    ts = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format)
    ts_list.append("3-%s (record_count=%s)" % (ts, len(cached_obj["results"])))
    #ts_list.append(cached_obj["results"][0])
    #return {"error_list":ts_list}

    #Get available list before applying filtering
    available_list_before = []
    #comment for performance testing
    
    #return code_dict

    if "filters" not in cached_obj:
        cached_obj["filters"] = {"applied":[]}
    cached_obj["filters"]["available"] = []
    update_res = update_filters(record_type, cached_obj["results"], cached_obj["filters"], 1, code_dict, filter_conf)
    if "error_list" in update_res:
        return update_res
    #return {"error_list":filter_conf}
    #return {"error_list":code_dict, "av":cached_obj["filters"]["available"], "conf":filter_conf[record_type]}

    ts_list.append("4-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))
    for obj in cached_obj["filters"]["available"]:
        available_list_before.append(obj)

    ts_list.append("5-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))
    #ts_list.append("count_1_%s" % (len(cached_obj["results"])))
    n_one = len(cached_obj["results"])

    #Apply filters
    #comment for performance testing
    res = filter_list(dbh, cached_obj, query_obj, query_filter_code, code_dict)
    if "error_list" in res:
        return res
    n_two = len(cached_obj["results"])

    #return {"n1":n_one, "n2":n_two}
    #return filter_conf
    #return {"code":query_filter_code}
    #return code_dict


    #ts_list.append("count_2_%s" % (len(cached_obj["results"])))
    ts_list.append("6-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))

    #Update filters
    #comment for performance testing
    cached_obj["filters"]["available"] = []
    update_res = update_filters(record_type, cached_obj["results"], cached_obj["filters"], 2, code_dict, filter_conf) 
    #return update_res

 
    ts_list.append("7-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))


    #update available counts
    count_dict = {}
    for obj in cached_obj["filters"]["available"]:
        for o in obj["options"]:
            combo_id = "%s|%s" % (obj["id"], o["id"])
            count_dict[combo_id] = o["count"]
    for obj in available_list_before:
        group_id = obj["id"]
        ordr = 100
        for o in obj["options"]:
            option_id = o["id"]
            combo_id = "%s|%s" % (group_id, option_id)
            if combo_id in count_dict:
                o["count"] = count_dict[combo_id]
            else:
                o["count"] = 0
            if option_id in filter_conf[record_type][group_id]["order_dict"]:
                o["order"] = filter_conf[record_type][group_id]["order_dict"][option_id]
            else:
                o["order"] = ordr
                ordr += 1
            if "label_dict" in filter_conf[record_type][group_id]:
                if option_id in filter_conf[record_type][group_id]["label_dict"]:
                    o["label"] = filter_conf[record_type][group_id]["label_dict"][option_id]

    cached_obj["filters"]["available"] = available_list_before

    ts_list.append("8-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))

    if len(cached_obj["results"]) == 0:
        res_obj = {
            "cache_info":cached_obj["cache_info"], 
            "filters":cached_obj["filters"],
            "results":[]
        }
        return res_obj


    return_fields = {"string":[], "int":[], "float":[]}
    for f in cached_obj["results"][0].keys():
        if type(cached_obj["results"][0][f]) is str:
            return_fields["string"].append(f)
        elif type(cached_obj["results"][0][f]) is int:
            return_fields["int"].append(f)
        elif type(cached_obj["results"][0][f]) is float:
            return_fields["float"].append(f)


    sorted_id_list = sort_objects(cached_obj["results"], return_fields,
            query_obj["sort"], query_obj["order"])
    res_obj = {"cache_info":cached_obj["cache_info"], "filters":cached_obj["filters"]}

    #check for post-access error, error_list should be empty upto this line
    if int(query_obj["offset"]) < 1 or int(query_obj["offset"]) > len(cached_obj["results"]):
        post_error_list.append({"error_code":"invalid-parameter-value", "field":"offset"})
        return {"error_list":post_error_list}


    removed_field_dict = {}
    start_index = int(query_obj["offset"]) - 1
    stop_index = start_index + int(query_obj["limit"])
    res_obj["results"] = []
    sorted_id_list = sorted_id_list[start_index:stop_index] if limit_flag else sorted_id_list
    for obj_id in sorted_id_list:
        obj = cached_obj["results"][obj_id]
        k_list = list(obj.keys())
        for k in k_list:
            if k in ["_id"] or k in extra_fields:
            #if k in ["_id", "record_id"] or k in extra_fields:
                obj.pop(k)
                removed_field_dict[k] = True 
        res_obj["results"].append(obj)
        #res_obj["results"].append(order_obj(obj, config_obj["objectorder"]["glycan"]))

    #return {"error_list":[removed_field_dict]}

    res_obj["pagination"] = {"offset":query_obj["offset"], "limit":query_obj["limit"],
        "total_length":len(cached_obj["results"]), "sort":query_obj["sort"], "order":query_obj["order"]}
    res_obj["query"] = query_obj


    ts_list.append("9-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))
    #return {"error_list":ts_list}
    #return {"error_list":cached_obj["results"]}

    return res_obj



def compare_filter_codes(record_filter_code, query_filter_code, filter_obj_list, code_dict, grp_id_list):

    flag = False    
    op_dict = {}
    for obj in filter_obj_list:
        op_dict[obj["id"]] = obj["operator"]

    record_code_parts, query_code_parts = record_filter_code.split("."), query_filter_code.split(".")
    
    failed_flag_list = []
    debug_list = [] 
    for grp_idx in range(0, len(grp_id_list)):
        grp = grp_id_list[grp_idx]
        if grp not in op_dict:
            continue
        op = op_dict[grp]
        row = []
        for j in range(0, len(query_code_parts[grp_idx])):
            if query_code_parts[grp_idx][j] != "*":
                row.append(query_code_parts[grp_idx][j] == record_code_parts[grp_idx][j])
        debug_list.append({"grp_idx":grp_idx, "row":row, "query_code_parts":query_code_parts[grp_idx]})
        failed = False
        if op.lower() == "or" and len(row) > 0 and True not in row:
            failed = True
        if op.lower() == "and" and len(row) > 0 and False in row:
            failed = True
        failed_flag_list.append(failed)
    flag = True not in failed_flag_list
    #flag = {"error_list":debug_list} 

    return flag


def filter_list(dbh, res_obj, query_obj, query_filter_code, code_dict):

    record_type = res_obj["cache_info"]["record_type"]
    filter_conf = get_filter_conf(dbh)
    if "filters" not in res_obj:
        res_obj["filters"] = {"available":[], "applied":[]}
    if "filters" in query_obj:
        res_obj["filters"]["applied"] = query_obj["filters"]
        if query_obj["filters"] == []:
            return {}
    else:
        return {} 

    debug_list = []
 
    grp_id_list = get_grp_id_list(record_type, filter_conf)
    tmp_record_list = []
    for record_obj in res_obj["results"]:
        if "_id" in record_obj:
            record_obj.pop("_id")
        flag = compare_filter_codes(record_obj["filter_code"], query_filter_code, query_obj["filters"], code_dict, grp_id_list)
        if type(flag) is dict:
            if "error_list" in flag:
                return flag
        if flag:
            tmp_record_list.append(record_obj)

    #return {"error_list":debug_list}
    res_obj["results"] = tmp_record_list

    return {}




def get_grp_id_list(record_type, filter_conf):
    
    idx2grp = {}
    for grp in filter_conf[record_type]:
        grp_idx = filter_conf[record_type][grp]["grp_idx"]
        idx2grp[grp_idx] = grp
    grp_id_list = []
    for grp_idx in sorted(idx2grp):
        grp_id_list.append(idx2grp[grp_idx])
    
    return grp_id_list

   
def update_filters(record_type, obj_list, filters, step, code_dict, filter_conf):

    #grp_id_list = sorted(code_dict.keys())
    grp_id_list = get_grp_id_list(record_type, filter_conf)
   
 
    n_11 = len(grp_id_list)
    seen_filter_code = {}
    count_dict = {}
    debug_list = []
    for record_obj in obj_list:
        if "filter_code" not in record_obj:
            return {"error_list":[{"error_code": "list_obj_without_filter_code","record":record_obj}]}
        seen_filter_code[record_obj["filter_code"].replace(".", "_")] = True
        record_code_parts = record_obj["filter_code"].split(".")
        debug_list.append(record_code_parts)
        n_12 = len(record_code_parts)
        if n_11 != n_12:
            return {"error_list":[{"error_code": "filter_grp_count mismatch %s!=%s" % (n_11, n_12)}]}
        for grp_idx in range(0, len(grp_id_list)):
            grp = grp_id_list[grp_idx]
            n_21 = len(code_dict[grp])
            n_22 = len(record_code_parts[grp_idx])
            if grp == "by_sequence_details":
                debug_list.append([code_dict[grp], record_code_parts[grp_idx]])
            if n_21 != n_22:
                return {"error_list":[{"grp_id_list":grp_id_list, "grp":grp, "grp_idx":grp_idx, "code_dict":code_dict, "record_code_parts":record_code_parts}]}
                return {"error_list":[{"error_code": "filter_value_count mismatch %s!=%s"%(n_21,n_22)}]}
            for j in range(0, n_22):
                label = code_dict[grp][j]["value"]
                #label = grp + " | " + str(j) 
                if record_code_parts[grp_idx][j] == "1":
                    #s = "%s|%s|%s|%s" % (grp,record_code_parts[grp_idx], label, j)
                    s = "%s|%s|%s" % (grp,record_code_parts[grp_idx], code_dict[grp])
                    debug_list.append(s)
                    if grp not in count_dict:
                        count_dict[grp] = {}
                    if label not in count_dict[grp]:
                        count_dict[grp][label] = 0
                    count_dict[grp][label] += 1
    #return {"error_list":debug_list}
    #return {"a":code_dict, "b":count_dict, "c":seen_filter_code, "d":debug_list}
    #print (count_dict)
    

    tmp_seen = {}
    for grp in filter_conf[record_type]:
        label_dict = filter_conf[record_type][grp]["label_dict"] if "label_dict" in filter_conf[record_type][grp] else {}
        group_label = filter_conf[record_type][grp]["group_label"]
        group_ordr = filter_conf[record_type][grp]["group_order"]
        obj = {"id":grp, "label":group_label, "order":group_ordr, "tooltip":"", "tmp_options":{}}
        for option_id in filter_conf[record_type][grp]["order_dict"]:
            #debug_list.append(grp + "|" + option_id + "|" + str(grp in count_dict))
            label = option_id
            option_ordr = filter_conf[record_type][grp]["order_dict"][option_id]
            if grp not in tmp_seen:
                tmp_seen[grp] = {}
            tmp_seen[grp][label] = True
            count = 0
            if grp in count_dict:
                if label in count_dict[grp]:
                    count = count_dict[grp][label]
           
            label = label_dict[option_id] if option_id in label_dict else label
            obj["tmp_options"][option_id] = {"id":option_id, "label":label, "count":count,"order":option_ordr}
        filters["available"].append(obj)
        #xxxxx

    #return {"error_list":debug_list}


    seen = {}
    non_empty_grp_obj_list = []
    for grp_obj in filters["available"]:
        if "tmp_options" not in grp_obj:
            continue
        filter_group_id = grp_obj["id"]
        grp_obj["options"] = []
        for option_id in grp_obj["tmp_options"]:
            obj = grp_obj["tmp_options"][option_id]
            if step == 1 and obj["count"] == 0:
                continue
            grp_obj["options"].append(obj)
            if filter_group_id not in seen:
                seen[filter_group_id] = {}
            if option_id not in seen[filter_group_id]:
                seen[filter_group_id][option_id] = True
        grp_obj.pop("tmp_options")
        if grp_obj["options"] != []:
            non_empty_grp_obj_list.append(grp_obj)
    
    filters["available"] = non_empty_grp_obj_list

    #print (json.dumps(filters["available"], indent=4))

    return {}







def get_errors_in_superquery(query_obj, config_obj):

    error_list = []
    for obj in query_obj:
        for k in ["concept", "query"]:
            if k not in obj:
                error_list.append({"error_code": "missing-%s" % (k)})
        if "concept" in obj:
            concept = obj["concept"]
            if "query" in obj:
                for k in ["aggregator", "unaggregated_list", "aggregated_list"]:
                    if k not in obj["query"]:
                        error_list.append({"error_code": "missing-%s" %(k),"concept":concept})

    return error_list



def get_errors_in_query(svc_name, query_obj, config_obj):

    if query_obj == None:
        return {"error_list":[{"error_code": "missing query object"}]}

    for key1 in query_obj:
        if type(query_obj[key1]) in [str]:
            query_obj[key1] = query_obj[key1].strip()
        elif type(query_obj[key1]) is dict:
            for key2 in query_obj[key1]:
                if type(query_obj[key1][key2]) in [str]:
                    query_obj[key1][key2] = query_obj[key1][key2].strip()

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    field_info = config_obj[svc_name]["field_info"]
    collection_list = config_obj[svc_name]["collectionlist"]
    max_query_value_len = config_obj["max_query_value_len"]

    error_list = []
    for coll in collection_list:
        if coll not in dbh.list_collection_names():
            error_list.append({"error_code": "missing-collection", "collection":coll})

    for key1 in query_obj:
        if key1 not in field_info:
            error_list.append({"error_code":"unexpected-field-in-query", "field":key1})
        else:
            if type(query_obj[key1]) is dict:
                for key2 in query_obj[key1]:
                    if key2 not in field_info[key1]:
                        error_list.append({"error_code":"unexpected-field-in-query", "field":key2})
                    elif "type" in field_info[key1][key2]:
                        combo_key = "%s.%s" % (key1, key2)
                        val_type = ""
                        val_type = "string" if type(query_obj[key1][key2]) in [str] else val_type
                        val_type = "number" if type(query_obj[key1][key2]) in [int, float] else val_type
                        val_type = "boolean" if type(query_obj[key1][key2]) in [bool] else val_type
                        val_type = "list" if type(query_obj[key1][key2]) in [list] else val_type
                        if key2 not in field_info[key1]:
                            error_list.append({"error_code":"unexpected-field-in-query", "field":combo_key})
                        if val_type != field_info[key1][key2]["type"]:
                            error_list.append({"error_code":"invalid-parameter-value", "field":combo_key})
                        if "maxlen" in field_info[key1][key2]:
                            max_query_value_len = field_info[key1][key2]["maxlen"]
                        if len(str(query_obj[key1][key2])) > max_query_value_len:
                            error_list.append({"error_code":"invalid-parameter-value-length", "field":combo_key})
                    else:
                        if type(query_obj[key1][key2]) is dict:
                            for key3 in query_obj[key1][key2]:
                                if "type" in field_info[key1][key2][key3]:
                                    combo_key = "%s.%s.%s" % (key1, key2,key3)
                                    t = query_obj[key1][key2][key3]
                                    val_type = ""
                                    val_type = "string" if type(t) in [str] else val_type
                                    val_type = "number" if type(t) in [int, float] else val_type
                                    val_type = "boolean" if type(t) in [bool] else val_type
                                    if key3 not in field_info[key1][key2]:
                                        error_list.append({"error_code":"unexpected-field-in-query", 
                                            "field":combo_key})
                                    if val_type != field_info[key1][key2][key3]["type"]:
                                        error_list.append({"error_code":"invalid-parameter-value", "field":combo_key})
                                    if "maxlen" in field_info[key1][key2][key3]:
                                        max_query_value_len = field_info[key1][key2][key3]["maxlen"]
                                    if len(str(query_obj[key1][key2][key3])) > max_query_value_len:
                                        error_list.append({"error_code":"invalid-parameter-value-length", "field":combo_key})
                        elif type(query_obj[key1][key2]) is list:
                            for o in query_obj[key1][key2]:
                                for key3 in o:
                                    if "type" in field_info[key1][key2][key3]:
                                        combo_key = "%s.%s.%s" % (key1, key2,key3)
                                        t = o[key3]
                                        val_type = ""
                                        val_type = "string" if type(t) in [str] else val_type
                                        val_type = "number" if type(t) in [int, float] else val_type
                                        val_type = "boolean" if type(t) in [bool] else val_type
                                        if key3 not in field_info[key1][key2]:
                                            error_list.append({"error_code":"unexpected-field-in-query",
                                                "field":combo_key})
                                        if val_type != field_info[key1][key2][key3]["type"]:
                                            error_list.append({"error_code":"invalid-parameter-value", "field":combo_key})
                                        if "maxlen" in field_info[key1][key2][key3]:
                                            max_query_value_len = field_info[key1][key2][key3]["maxlen"]
                                        if len(str(o[key3])) > max_query_value_len:
                                            error_list.append({"error_code":"invalid-parameter-value-length", "field":combo_key})



            elif type(query_obj[key1]) is list:
                for val in query_obj[key1]:
                    if "maxlen" in field_info[key1]:
                        max_query_value_len = field_info[key1]["maxlen"]
                    if len(str(val)) > max_query_value_len:
                        error_list.append({"error_code":"invalid-parameter-value-length", "field":key1})
            else:
                val_type = "" 
                val_type = "string" if type(query_obj[key1]) in [str] else val_type
                val_type = "number" if type(query_obj[key1]) in [int, float] else val_type
                val_type = "boolean" if type(query_obj[key1]) in [bool] else val_type
                if "maxlen" in field_info[key1]:
                    max_query_value_len = field_info[key1]["maxlen"] 
                if len(str(query_obj[key1])) > max_query_value_len:
                    error_list.append({"error_code":"invalid-parameter-value-length", "field":key1})
                if "type" not in field_info[key1]:
                    error_list.append({"error_code":"invalid-parameter-value", "field":key1})
                elif val_type != field_info[key1]["type"]:
                    error_list.append({"error_code":"invalid-parameter-value", "field":key1})


    for combo_field in config_obj[svc_name]["requiredfields"]:
        field_list = combo_field.split(".")
        if len(field_list)  == 1:
            key1 = field_list[0]
            if key1 not in query_obj:
                error_list.append({"error_code":"missing-parameter", "field":key1})
            elif str(query_obj[key1]).strip() == "":
                error_list.append({"error_code":"invalid-parameter-value-length", "field":key1})
        elif len(field_list) > 1:
            key1, key2 = field_list[0], field_list[1]
            if key1 not in query_obj:
                error_list.append({"error_code":"missing-parameter", "field":key1})
            elif key2 not in query_obj[key1]:
                error_list.append({"error_code":"missing-parameter", "field":combo_field})
            elif str(query_obj[key1][key2]).strip() == "":
                error_list.append({"error_code":"invalid-parameter-value-length", "field":combo_field})

    return error_list



def get_error_obj(error_code, error_log, log_path):

    error_id = get_random_string(6)
    log_file = log_path + "/" + error_id + "-" + error_code + ".log"
    with open(log_file, "w") as FW:
        FW.write("%s" % (error_log))
    return {"error_list":[{"error_code": "exception-error-" + error_id}]}








def get_paginated_sections(obj, query_obj, section_list, limit_flag):

    sec_map = {
        "glycosylation_reported_with_glycan":"glycosylation",
        "glycosylation_reported":"glycosylation",
        "glycosylation_predicted":"glycosylation",
        "glycosylation_automatic_literature_mining":"glycosylation",
        "snv_disease":"snv",
        "snv_non_disease":"snv", 
        "expression_tissue":"expression", 
        "expression_cell_line":"expression"
    }
    site_cat_list_all = ["reported", "reported_with_glycan", "predicted", "automatic_literature_mining"] 
    table_id_list = []
    for o in query_obj["paginated_tables"]:
        table_id_list.append(o["table_id"])
 
    debug_dict = {} 
    sec_tables = {}
    tableid2sec = {}
    seen_obj = {}
    tmp_list = []
    for sec in section_list:
        sec_new = sec_map[sec]  if sec in sec_map else sec
        if sec_new not in obj:
            continue
        for o in obj[sec_new]:
            #table_id = sec
            tmp_table_id_list = [sec]
            if sec.find("glycosylation_") != -1:
                start_pos = o["start_pos"] if "start_pos" in o else "x"
                gtc = o["glytoucan_ac"] if "glytoucan_ac" in o else "x"
                site_cat_list_seen = list(o["site_category_dict"].keys())
                tmp_table_id_list = [] 
                for site_cat in site_cat_list_seen:
                    if site_cat in site_cat_list_all:
                        table_id = "glycosylation_" + site_cat
                        tmp_table_id_list.append(table_id)
                        cmb = "%s|%s|%s" % (table_id,start_pos, gtc)
                        debug_dict[cmb] = True
                 
            #if sec.find("glycosylation_") != -1 and o["site_category"] in site_cat_list_all:
            #    table_id = "glycosylation_" + o["site_category"]
            #    cmb = "%s|%s|%s" % (table_id,start_pos, gtc)
            #    debug_dict[cmb] = True
            if sec in ["expression_tissue", "expression_cell_line"]:
                tmp_table_id_list = ["expression_" + o["category"]]
            if sec in ["snv"]:
                tmp_table_id_list = ["snv_disease"] if "disease" in o["keywords"] else ["snv_non_disease"]
            #Fix to remove redundant svn objects
            if sec == "snv_disease" and "disease" not in o["keywords"]:
                continue
            if sec == "snv_non_disease" and "disease" in o["keywords"]:
                continue
            for table_id in tmp_table_id_list:
                site_cat = table_id.replace("glycosylation_", "")
                if table_id in table_id_list:
                    tableid2sec[table_id] = sec_new
                    if table_id not in sec_tables:
                        sec_tables[table_id] = []
                    oo = {}
                    for k in o:
                        oo[k] = o[k]
                    oo["site_category"] = site_cat
                    s = json.dumps(oo)
                    if table_id not in seen_obj:
                        seen_obj[table_id] = {}
                    if s not in seen_obj[table_id]:
                        sec_tables[table_id].append(oo)
                    seen_obj[table_id][s] = True
                    if site_cat in ["reported", "automatic_literature_mining"]:
                        debug_dict[site_cat] = oo
 
    #return debug_dict 
    #return sec_tables


    for q in query_obj["paginated_tables"]:
        if "table_id" not in q:
            return {"error_list":[{"error_code":"missing-table_id-parameter"}]}
        table_id = q["table_id"]
        if table_id in sec_tables and table_id in tableid2sec:
            sort_order = q["order"] if "order" in q else "asc"
            offset = q["offset"] if "offset" in q else 1
            limit = q["limit"] if "limit" in q else 20
            if type(sec_tables[table_id][0]) is dict:
                if "sort" not in q:
                    key_list = list(sec_tables[table_id][0].keys())
                    q["sort"] = key_list[0]
                sorted_idx_list = sort_objects_new(sec_tables[table_id], q["sort"], sort_order)
                #return sorted_idx_list
            else:
                sorted_idx_list = []
                rev_flag = sort_order == "desc"
                ordered_values = sorted(sec_tables[table_id], reverse=rev_flag)
                for v in ordered_values:
                    sorted_idx_list.append(sec_tables[table_id].index(v))
            start_index = int(offset) - 1
            stop_index = start_index + int(limit)
            start_index = 0 if start_index > len(sorted_idx_list) - 1 else start_index
            stop_index = len(sorted_idx_list) if stop_index > len(sorted_idx_list) else stop_index
            if limit_flag:
                sorted_idx_list = sorted_idx_list[start_index:stop_index]
            tmp_table = []
            for idx in sorted_idx_list:
                tmp_table.append(sec_tables[table_id][idx])
            sec = tableid2sec[table_id]
            if sec == table_id:
                sec_tables[sec] = tmp_table
            else:
                if sec not in sec_tables:
                    sec_tables[sec] = []
                sec_tables[sec] += tmp_table
                if table_id in sec_tables:
                    sec_tables.pop(table_id)


    return sec_tables


def get_partition_ranges(n, batch_size):

    range_list = []
    i = 0
    while True:
        s, e = i*batch_size, (i+1)*batch_size
        e = n if e > n else e
        range_list.append({"s":s, "e":e})
        if e == n:
            break
        i += 1
    return range_list



def cache_list_objects(dbh, api_name, cache_id, listcache_id, res_obj, config_obj):


    #making result objects simple   
    result_obj_list = [] 
    if "results" in res_obj:
        idx = 0
        for obj in res_obj["results"]:
            score_info, hit_score = obj["score_info"], obj["hit_score"]
            o = {"idx":idx, "record_id":obj["record_id"], "hit_score":hit_score, "score_info":score_info,
                "filter_code":obj["filter_code"]
            }
            result_obj_list.append(o)
            idx += 1
    total_count = len(result_obj_list)

    ts_format = "%Y-%m-%d %H:%M:%S %Z%z"
    ts = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format)

    batch_size = 1000
    cache_coll = "c_initlistcache"
    cached_obj = dbh[cache_coll].find_one({"list_id":listcache_id})
    cache_info = {"ts":ts,"search_type":api_name}
    
    # Insert only if listcache_id is not in c_initlistcache
    if cached_obj == None:
        cache_info = res_obj["cache_info"] if "cache_info" in res_obj else {}
        cache_info["cache_id"] = cache_id
        cache_info["listcache_id"] = listcache_id

        glbl_obj = {}
        for k in res_obj:
            if k not in ["results", "cache_id", "listcache_id"]:
                glbl_obj[k] = res_obj[k]

        if total_count > batch_size:
            range_list = get_partition_ranges(total_count, batch_size)           
            for o in range_list:
                s, e = o["s"], o["e"]
                tmp_glbl_obj = glbl_obj if s == 0 else {}
                tmp_obj_list = result_obj_list[s:e] 
                oo = {"list_id":listcache_id,"cache_info":cache_info, "total_count":total_count,
                    "results":tmp_obj_list,"glbl":tmp_glbl_obj,"start":s,"end":e}
                res = dbh[cache_coll].insert_one(oo)
        else:
            s, e = 0, total_count
            oo = {"list_id":listcache_id,"cache_info":cache_info, "results":result_obj_list,
                    "glbl":glbl_obj,"start":s, "end":e, "total_count":total_count}
            res = dbh[cache_coll].insert_one(oo)
 
    return {}






def retrieve_cached_list_objects(cache_id, listcache_id):

    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj
    cache_coll = "c_initlistcache"
    res_obj = {"results":[]}
    oo_list = []
    for doc in dbh[cache_coll].find({"list_id":listcache_id}):
        for k in doc["glbl"]:
            res_obj[k] = doc["glbl"][k]
        res_obj["results"] += doc["results"]
        oo_list.append(doc["start"])
    #return oo_list

    if len(res_obj["results"]) == 0:
        return None

    if "cache_info" not in res_obj:
        res_obj["cache_info"] = {}
    res_obj["cache_info"]["cache_id"] = cache_id
    res_obj["cache_info"]["listcache_id"] = listcache_id
    
    return res_obj



def get_hash_id(api_name , record_type, obj):

    new_obj = {}
    for k in sorted(obj):
        if k not in ["offset", "limit", "sort", "order", "columns"]:
            new_obj[k] = obj[k]
            if k == "filters":
                oo_list = []
                for o in new_obj["filters"]:
                    # default to OR for single selected options
                    if len(o["selected"]) == 1:
                        o["operator"] = "OR" 
                    oo = {}
                    for kk in sorted(o):
                        oo[kk] = o[kk]
                    oo["selected"] = sorted(oo["selected"])
                    oo_list.append(oo)
                new_obj["filters"] = oo_list
    
    
    hash_str = api_name + record_type + json.dumps(new_obj)
    hash_obj = hashlib.md5(hash_str.encode('utf-8'))
    

    return hash_obj.hexdigest()



def filter_glyco_obj_list(table_id, obj_list, query_filters , config_obj):

    filter_init = config_obj["filter_init"]
    filters_obj = {"applied":query_filters, "available":[]}
   
    query_site_category = table_id.replace("glycosylation_", "")
    table_obj_list, other_table_obj_list = [], []
    for gly_obj in obj_list:
        if query_site_category == gly_obj["site_category"]:
            table_obj_list.append(gly_obj)
        else:
            other_table_obj_list.append(gly_obj)
    res = get_query_filter_code(dbh, query_filters, table_id, filter_init)
    query_filter_code, code_dict = res["code"], res["dict"]
    update_res = update_filters(table_id, table_obj_list, filters_obj, 1, code_dict, filter_init)
    if "error_list" in update_res:
        return update_res
 

    
 
    grp_id_list = get_grp_id_list(table_id, filter_init)
    passed_obj_list = []
    for gly_obj in table_obj_list:
        flag = compare_filter_codes(gly_obj["filter_code"], query_filter_code, query_filters, code_dict, grp_id_list)
        if type(flag) is dict:
            if "error_list" in flag:
                return flag
        if flag:
            passed_obj_list.append(gly_obj)
    res = {"a":table_obj_list,"b":passed_obj_list, "c":other_table_obj_list, "d":filters_obj}
    return res







def parse_sent(s,  max_word_count, min_word_count):

    phrase_dict = {}
    if s.strip() == "":
        return
    s = s.lower().replace(",", " ").replace("-", " ").replace(";", " ")
    s = s.replace("(", " ").replace(")", " ").replace("[", " ").replace("]", " ")
    w_list = s.split(" ")
    word_count = len(w_list) + 1
    word_count = max_word_count if word_count > max_word_count else word_count
    for wlen in range(0, word_count):
        if wlen > len(w_list):
            continue
        for i in range(0, len(w_list)):
            l = []
            for ww in w_list[i:i+wlen]:
                ww = ww.strip()
                if ww != "":
                    l.append(ww)
            if len(l) >= min_word_count:
                w = " ".join(l)
                if len(w) == 1:
                    continue
                phrase_dict[w] = True

    return phrase_dict




def get_list_objects(dbh,cache_id, cache_info, cache_collection, final_fields, score_dict, prj_obj, config_obj):
    
    is_empty_query = False
    if "query" in cache_info:
        is_empty_query = True if cache_info["query"] == {} else is_empty_query
        if "concept_query_list" in cache_info["query"]:
            is_empty_query = True if cache_info["query"]["concept_query_list"] == [] else is_empty_query

    tmp_obj_list = []
    id_list = []
    qry_obj = {"list_id":cache_id}
    for doc in dbh[cache_collection].find(qry_obj):
        id_list += doc["results"]

 
    batch_size = 300000
    record_count = len(id_list)
    nparts = int(float(record_count)/float(batch_size)) + 1
    for i in range(0, nparts):
        start = i*batch_size
        end = (i+1)*batch_size
        end = len(id_list) if end > len(id_list) else end
        mongo_query = {"record_id":{"$in": id_list[start:end]}}
        for obj in dbh["c_list"].find(mongo_query, prj_obj):
            if "_id" in obj:
                obj.pop("_id")
            score_info = {"freqdict":{}}
            if True:
            #if is_empty_query == False:
                obj["hit_score"], cond_match_freq = get_hit_score(obj, cache_info, score_dict, final_fields, score_info)
            obj["score_info"] = score_info
            
            tmp_obj_list.append(obj)

    return tmp_obj_list




