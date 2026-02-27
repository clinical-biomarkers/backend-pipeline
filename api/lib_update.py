import os
import string
import random
import hashlib
import json
import datetime,time
import pytz
from collections import OrderedDict
from bson import json_util, ObjectId
import collections
import pymongo
from copied_util import get_hash_id





def cache_hitlist(dbh,list_id, record_list, cache_info, cache_coll, config_obj):
    
    res = dbh[cache_coll].delete_many({"list_id":list_id})
    total_count = len(record_list)
    partition_count = total_count/config_obj["cache_batch_size"]
    for i in range(0,int(partition_count)+1):
        start = i*config_obj["cache_batch_size"]
        end = start + config_obj["cache_batch_size"]
        end = total_count if end > total_count else end
        cache_info["start"] = start
        if start < total_count:
            cache_obj = {
                "list_id":list_id, 
                "cache_info":cache_info,
                "total_count":total_count,
                "results":record_list[start:end]
            }
            res = dbh[cache_coll].insert_one(cache_obj)
        
    return





def get_mongodb (db_info):

    db_name = db_info["db_name"]
    user, password = db_info["user"], db_info["password"]
    host_ip = db_info["host_ip"]
    port = db_info["port"]
    conn_str = "mongodb://%s:%s@%s:%s/?authSource=%s" % (user, password, host_ip, port,db_name)
 
    ret_obj, error_obj = {}, {}
    try: 
        client = pymongo.MongoClient(conn_str)
        client.server_info()
        ret_obj = client[db_name]
    except pymongo.errors.ServerSelectionTimeoutError as err:
        error_obj = {"status":0, "error":"Connection to MongoDB failed", "details":err.details}
    except pymongo.errors.OperationFailure as err:
        error_obj = {"status":0, "error":"Connection to MongoDB failed", "details":err.details}
    return ret_obj, error_obj



def supersearch_search(query_obj, config_obj, reason_flag, empty_search_flag, cache_name):

    dbh, error_obj = get_mongodb(config_obj["db_info"])
    if error_obj != {}:
        return error_obj


    record_type = "supersearch"
    api_name = "superearch_search"
    initial_list_id = get_hash_id(api_name, record_type, query_obj)


    #Collect errors 
    if query_obj == {}:
        query_obj["concept_query_list"] = []

    ts_format = "%Y-%m-%d %H:%M:%S %Z%z"
    ts_list = []
    ts_list.append("0-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))

    seen_path = {}
    for doc in dbh["c_path"].find({}):
        record_type = doc["record_type"]
        if record_type not in seen_path:
            seen_path[record_type] = {}
        path = doc["path"].split(" ")[0]
        seen_path[record_type][path] = True
        path_parts = path.split(".")
        if len(path_parts) > 1:
            for i in range(1, len(path_parts)):
                p = ".".join(path_parts[:i])
                seen_path[record_type][p] = True


    mongo_query = [] 
    error_list = []
    edge_rules = []
    ignore_dict = {}
    if empty_search_flag == False:
        if "ignored_edges" in query_obj:
            edge_rules = query_obj["ignored_edges"]
        else:
            for i in range(0, len(query_obj["concept_query_list"])):
                concept = query_obj["concept_query_list"][i]["concept"]
                edge_rules += config_obj["ignored_edges"][concept]

        for o in edge_rules:
            if "source" not in o or "target" not in o:
                return {"error_list":[{"error_code":"invalid-ignore-edge-object"}]}
            if o["source"] not in ignore_dict:
                ignore_dict[o["source"]] = {}
            ignore_dict[o["source"]][o["target"]] = True
            if "direction" in o:
                if o["direction"] == "both":
                    if o["target"] not in ignore_dict:
                        ignore_dict[o["target"]] = {}
                    ignore_dict[o["target"]][o["source"]] = True


    for i in range(0, len(query_obj["concept_query_list"])):
        q_obj = query_obj["concept_query_list"][i]["query"]
        concept = query_obj["concept_query_list"][i]["concept"]
                
        path_map = {}
        if concept in config_obj["path_map"]:
            path_map = config_obj["path_map"][concept]
        t_query,e_list = transform_query(q_obj, concept, seen_path, path_map)
        mongo_query.append({"query": t_query,"concept":concept})
        error_list += e_list
   
    if error_list != []:
        return {"error_list":error_list}

    DEBUG_FLAG = False

    dump_debug_timer("flag-1 running concept queries", DEBUG_FLAG)
    #return mongo_query

         

    initial_hit_count = 0
    reason_dict = {}
    initial_hit_dict = {}
    for q_obj in mongo_query:
        record_type = q_obj["concept"]
        coll = "c_" + record_type
        if record_type == "gene":
            coll = "c_protein"
            q_obj["query"] = {"$and":[q_obj["query"], {"gene": {'$gt':[]}}]}
        if record_type == "enzyme":
            coll = "c_protein"
            q_obj["query"] = {"$and":[q_obj["query"], {"keywords":"enzyme"}]}
        if record_type not in initial_hit_dict:
            initial_hit_dict[record_type] = {}
        if coll not in config_obj["projectedfields"]:
            continue
        record_id_field = config_obj["record_type_info"][record_type]["field"]
        #prj_obj = {record_id_field:1}
        prj_obj = {record_id_field:1, "down_seq":1, "up_seq":1, "site_seq":1,}
        doc_list = list(dbh[coll].find(q_obj["query"],prj_obj))

        #agg_query = [{"$project":{record_id_field:1, "result":{ "$not": [ q_obj["query"] ] }}}]
        #doc_list = list(dbh[coll].aggregate(agg_query))
        #print  (record_type, len(doc_list))
        #print q_obj["query"]
        initial_hit_count += len(doc_list)
        for doc in doc_list:
            if record_id_field not in doc:
                continue
            record_id = doc[record_id_field]
            #print "Robel", doc["up_seq"], doc["site_seq"], doc["down_seq"], record_id
            #print "Robel", record_id
            #print "Robel", record_id,doc["site_seq"]
            if record_type in ["enzyme", "gene"]:
                record_id = "%s.%s" % (record_type, record_id)
            initial_hit_dict[record_type][record_id] = True
            reason = "hit-in-initial-%s-query" % (record_type)
            add_reason(reason_dict, record_type, record_id, "self", record_id)  

    #return initial_hit_dict



    dump_debug_timer("flag-2 loading network", DEBUG_FLAG)

    record_type_list = list(config_obj["record_type_info"].keys())

    ts = "1-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format)
    ts_list.append(ts)
    #Load network
    #doc_list = list(dbh["c_network"].find({}))
    doc_list = list(dbh["c_network"].find({}))

    ts = "2-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format)
    ts_list.append(ts)
    ts_list.append(len(doc_list))


    final_hit_dict,final_hit_dict_split, conn_dict = {}, {}, {}
    if initial_hit_count > 0:
        final_hit_dict,final_hit_dict_split, conn_dict = load_network(doc_list, 
                initial_hit_dict, empty_search_flag, ignore_dict, reason_dict, config_obj)
    else:
        conn_dict = load_conn_dict(doc_list)

    #return ignore_dict

    ts_list.append("3-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))


    #After imposing edge constraints, some hits cannot be traced
    #these untraceable hits should be removed from final_hit_dict
    impose_edge_constraints_type_I(initial_hit_dict, final_hit_dict, final_hit_dict_split, reason_dict, ignore_dict)


    #Now, set concept_query_list to be empty list
    if empty_search_flag == True:
        query_obj["concept_query_list"] = []


    ts_list.append("6-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))

    res_obj = {"query":query_obj, "results_summary":{}}
    ts_format = "%Y-%m-%d %H:%M:%S %Z%z"
    ts = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format)
    cache_coll = "c_initcache"
    cachable_list = ["protein","glycan","site","disease"]
    for dst_record_type in record_type_list:
        n = len(list(final_hit_dict[dst_record_type].keys())) if dst_record_type in final_hit_dict else 0
        list_id = ""
        if dst_record_type in final_hit_dict and dst_record_type in cachable_list:
            record_list = list(final_hit_dict[dst_record_type].keys())
            if len(record_list) != 0:
                hash_str = dst_record_type + "_" + json.dumps(query_obj)
                hash_obj = hashlib.md5(hash_str.encode('utf-8'))
                list_id = hash_obj.hexdigest()
                cache_info = {
                    "cache_name":cache_name,
                    "query":query_obj,
                    "ts":ts,
                    "record_type":dst_record_type,
                    "empty_search_flag":empty_search_flag,
                    "search_type":"supersearch"
                }
                cache_hitlist(dbh,list_id,record_list,cache_info,cache_coll,config_obj)
                #print ("A-%s %s %s records" % (list_id, len(record_list), dst_record_type))
        res_obj["results_summary"][dst_record_type] = {"list_id":list_id, "result_count":n}
        stat_obj = {}
        bylinkage_obj = {}
        if dst_record_type in final_hit_dict_split:
            stat_obj = get_network_stat(final_hit_dict_split[dst_record_type])
        
        #for src_record_type not in stat_obj
        if dst_record_type in conn_dict:
            for src_record_type in conn_dict[dst_record_type]:
                if src_record_type not in stat_obj:
                    if src_record_type in ignore_dict:
                        if dst_record_type in ignore_dict[src_record_type]:
                            continue
                    bylinkage_obj[src_record_type] = {"list_id":"", "result_count":0}
            
        #for src_record_type in stat_obj
        for src_record_type in stat_obj:
            if src_record_type in ignore_dict:
                if dst_record_type in ignore_dict[src_record_type]:
                    continue
            list_id = ""
            if stat_obj[src_record_type] > 0 and dst_record_type in cachable_list:
                record_list = list(final_hit_dict_split[dst_record_type][src_record_type].keys())
                
                hash_str = dst_record_type + "_" + src_record_type + "_"+json.dumps(query_obj)
                hash_obj = hashlib.md5(hash_str.encode('utf-8'))
                list_id = hash_obj.hexdigest()
                cache_info = {
                    "cache_name":cache_name,
                    "query":query_obj,
                    "ts":ts,
                    "record_type":dst_record_type,
                    "linked_to":src_record_type,
                    "empty_search_flag":empty_search_flag,
                    "search_type":"supersearch"
                }
                cache_hitlist(dbh,list_id,record_list,cache_info,cache_coll,config_obj)
                #print ("B-%s %s %s records" % (list_id, len(record_list), src_record_type))
            n_from_src = stat_obj[src_record_type]
            bylinkage_obj[src_record_type] = {"list_id":list_id, "result_count":n_from_src}
        res_obj["results_summary"][dst_record_type]["bylinkage"] = bylinkage_obj

    

    ts_list.append("7-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))

    id_list = []
    for dst_record_type in res_obj["results_summary"]:
        list_id = res_obj["results_summary"][dst_record_type]["list_id"]
        if list_id != "":
            id_list.append(list_id)
        if "bylinkage" in res_obj["results_summary"][dst_record_type]:
            bylinkage_obj = res_obj["results_summary"][dst_record_type]["bylinkage"]
            for src_record_type in bylinkage_obj:
                list_id = bylinkage_obj[src_record_type]["list_id"]
                if list_id != "":
                    id_list.append(list_id)

    ts_list.append("8-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))

    for list_id in id_list:
        q_obj = {"list_id":list_id}
        update_obj = {"cache_info.result_summary":res_obj["results_summary"]}
        res = dbh["c_initcache"].update_one(q_obj, {'$set':update_obj}, upsert=True)

    cache_info = {"search_type":"supersearch", "empty_search_flag":empty_search_flag, "record_type":"supersearch", "ts":ts}
    cache_obj = {"list_id":initial_list_id, "res":res_obj, "cache_info":cache_info}
    res = dbh["c_initcache"].insert_one(cache_obj)

    ts_list.append("9-"+datetime.datetime.now(pytz.timezone('US/Eastern')).strftime(ts_format))
    #return ts_list

    return res_obj



def impose_edge_constraints_type_I(initial_hit_dict, final_hit_dict, final_hit_dict_split, reason_dict, ignore_dict):
    traceble_dict = {}
    for dst_record_type in final_hit_dict_split:
        for src_record_type in final_hit_dict_split[dst_record_type]:
            if src_record_type in ignore_dict:
                if dst_record_type in ignore_dict[src_record_type]:
                    continue
            for dst_record_id in final_hit_dict_split[dst_record_type][src_record_type]:
                if dst_record_type not in traceble_dict:
                    traceble_dict[dst_record_type] = {}
                traceble_dict[dst_record_type][dst_record_id] = True


    emptied_concepts = []
    dst_record_type_list = list(final_hit_dict.keys())
    for dst_record_type in dst_record_type_list:
        if dst_record_type in initial_hit_dict:
            continue
        dst_record_id_list = list(final_hit_dict[dst_record_type].keys())
        for dst_record_id in dst_record_id_list:
            if dst_record_type not in traceble_dict:
                final_hit_dict[dst_record_type].pop(dst_record_id)
            elif dst_record_id not in traceble_dict[dst_record_type]:
                final_hit_dict[dst_record_type].pop(dst_record_id)
        if final_hit_dict[dst_record_type] == {}:
            final_hit_dict.pop(dst_record_type)
            emptied_concepts.append(dst_record_type)

        
    #clean reason_dict by considering ignored edges
    for dst_record_type in reason_dict:
        dst_record_id_list = list(reason_dict[dst_record_type].keys())
        for dst_record_id in dst_record_id_list:
            src_record_type_list = list(reason_dict[dst_record_type][dst_record_id].keys())
            for src_record_type in src_record_type_list:
                if src_record_type in ignore_dict:
                    if dst_record_type in ignore_dict[src_record_type]:
                        reason_dict[dst_record_type][dst_record_id].pop(src_record_type)
            if reason_dict[dst_record_type][dst_record_id] == {}:
                reason_dict[dst_record_type].pop(dst_record_id)
            else:
                #Remove dst_record_id if comes from emptied_concept only
                src_type_list = sorted(list(reason_dict[dst_record_type][dst_record_id].keys()))
                if src_type_list == sorted(emptied_concepts):
                    final_hit_dict[dst_record_type].pop(dst_record_id)
                    for emptied_concept in emptied_concepts:
                        if emptied_concept in final_hit_dict_split[dst_record_type]:
                            final_hit_dict_split[dst_record_type].pop(emptied_concept)
                    #print "flag", final_hit_dict_split["gene"]["protein"].keys()

    return






def load_conn_dict(doc_list):

    conn_dict = {}
    for doc in doc_list:
        for obj in doc["recordlist"]:
            src_record_type, src_record_id = obj["record_type"], obj["record_id"]
            src_node = "%s %s" % (src_record_type, src_record_id)
            for dst_record_type in obj["linkeage"]:
                if src_record_type not in conn_dict:
                    conn_dict[src_record_type] = {}
                if dst_record_type not in conn_dict[src_record_type]:
                    conn_dict[src_record_type][dst_record_type] = True

    return conn_dict




def load_network(doc_list, initial_hit_dict, empty_search_flag, ignore_dict,reason_dict, config_obj):


    #log_file = "/data/shared/glygen/tmp/supersearch.log"
    #FL = open(log_file, "w")

    conn_dict = {}
    edge_dict = {}
    orphan_dict = {}
    for doc in doc_list:
        for obj in doc["recordlist"]:
            src_record_type, src_record_id = obj["record_type"], obj["record_id"]
            src_node = "%s %s" % (src_record_type, src_record_id)
            if obj["linkeage"] == {}:
                if src_record_type not in orphan_dict:
                    orphan_dict[src_record_type] = {}
                orphan_dict[src_record_type][src_record_id] = True
            else:
                for dst_record_type in obj["linkeage"]:
                    if src_record_type not in conn_dict:
                        conn_dict[src_record_type] = {}
                    if dst_record_type not in conn_dict[src_record_type]:
                        conn_dict[src_record_type][dst_record_type] = True
                    
                    #If edge is ignored, continue
                    if src_record_type in ignore_dict:
                        if dst_record_type in ignore_dict[src_record_type]:
                            continue

                    for dst_record_id in obj["linkeage"][dst_record_type]:
                        dst_node = "%s %s" % (dst_record_type, dst_record_id)
                        if src_record_type not in edge_dict:
                            edge_dict[src_record_type] = {}
                        if src_record_id not in edge_dict[src_record_type]:
                            edge_dict[src_record_type][src_record_id] = {}
                        if dst_record_type not in edge_dict[src_record_type][src_record_id]:
                            edge_dict[src_record_type][src_record_id][dst_record_type] = {}
                        edge_dict[src_record_type][src_record_id][dst_record_type][dst_record_id] = True
   
    initial_record_list = list(initial_hit_dict.keys()) 
    record_type_list = initial_record_list
    for record_type in edge_dict:
        if record_type not in record_type_list:
            record_type_list.append(record_type)


    #node_hit_dict = initial_hit_dict
    node_hit_dict = {}
    edge_hit_dict = {}
 
    #add nodes in initial_hit_dict to node_hit_dict
    for src_record_type in initial_hit_dict:
        for src_record_id in initial_hit_dict[src_record_type]:
            if src_record_type not in node_hit_dict:
                node_hit_dict[src_record_type] = {}
            node_hit_dict[src_record_type][src_record_id] = True
            #print ("flag-1", src_record_type, src_record_id)

    #for src_record_type in record_type_list:
    for src_record_type in config_obj["node_order"][initial_record_list[0]]:
        if src_record_type not in record_type_list:
            continue
        if src_record_type not in edge_dict:
            continue
        for src_record_id in edge_dict[src_record_type]:
            src_node = "%s:%s" % (src_record_type,src_record_id)
            # if empty query search, add all src nodes including unlinked ones
            if empty_search_flag == True and src_record_type in orphan_dict:
                if src_record_type not in node_hit_dict:
                    node_hit_dict[src_record_type] = {}
                node_hit_dict[src_record_type][src_record_id] = True
                #print ("flag-2",src_record_type, src_record_id)
 
            if empty_search_flag == False:
                # any outgoing link/edge passes this step if src node has not been filtered out
                # or the src node has already made it to the node_hit_dict
                
                if filtered_out_flag_type_I(initial_hit_dict,src_record_type,src_record_id):
                    continue
                else:
                    src_node_status = False
                    if src_record_type in node_hit_dict:
                        if src_record_id in node_hit_dict[src_record_type]:
                            src_node_status = True
                    if src_node_status == False:
                        #FL.write("skip_1:%s\n" % (src_node))
                        continue
            for dst_record_type in edge_dict[src_record_type][src_record_id]:
                # ignore edges in the ignore dict
                if empty_search_flag == False:
                    if src_record_type in ignore_dict:
                        if dst_record_type in ignore_dict[src_record_type]:
                            continue
                for dst_record_id in edge_dict[src_record_type][src_record_id][dst_record_type]:
                    dst_node = "%s:%s" % (dst_record_type,dst_record_id)
                    quad_id = "%s -> %s" % (src_node, dst_node)
                    #FL.write("flag_3:%s\n" % (quad_id))
                    if empty_search_flag == False:
                        # link/edge passes this step only if dst node has not been filtered out
                        # or the src node has already made it to the node_hit_dict
                        if filtered_out_flag_type_I(initial_hit_dict,dst_record_type,dst_record_id):
                            continue
                        else:
                            src_node_status = False
                            if src_record_type in node_hit_dict:
                                if src_record_id in node_hit_dict[src_record_type]:
                                    src_node_status = True
                            if src_node_status == False:
                                #FL.write("skip_2:%s\n" % (quad_id))
                                continue
                    #FL.write("flag_4:%s\n" % (quad_id))
                    init_flag = False
                    if dst_record_type in initial_hit_dict:
                        if dst_record_id in initial_hit_dict[dst_record_type]:
                            init_flag = True

                    #skip if src-to-dst edge is ignored
                    if src_record_type in ignore_dict:
                        if dst_record_type in ignore_dict[src_record_type]:
                            continue

                    # at this point both src node (src_record_type, src_record_id) and 
                    # dst node (dst_record_type,dst_record_id) are not filtered out
                    
                    # adding src_node to node_hit_dict
                    if src_record_type not in node_hit_dict:
                        node_hit_dict[src_record_type] = {}
                    node_hit_dict[src_record_type][src_record_id] = True
                    #FL.write("src_added:%s\n" % (quad_id))
                    #print ("flag-3",src_record_type, src_record_id)
                    # adding src_node to edge_hit_dict
                    if src_record_type not in edge_hit_dict:
                        edge_hit_dict[src_record_type] = {}
                    if dst_record_type not in edge_hit_dict[src_record_type]:
                        edge_hit_dict[src_record_type][dst_record_type] = {}
                    edge_hit_dict[src_record_type][dst_record_type][src_record_id] = True
                    # adding src_node to reason_dict
                    if init_flag == False:
                        add_reason(reason_dict, src_record_type, src_record_id, dst_record_type, dst_record_id)
                        #print "flag", quad_id, reason                                                                                        
                    # adding dst_node to node_hit_dict
                    if dst_record_type not in node_hit_dict:
                        node_hit_dict[dst_record_type] = {}
                    node_hit_dict[dst_record_type][dst_record_id] = True
                    #print ("flag-4",dst_record_type, dst_record_id)
                    #FL.write("dst_added:%s\n" % (quad_id))
                    # adding dst_node to edge_hit_dict
                    if dst_record_type not in edge_hit_dict:
                        edge_hit_dict[dst_record_type] = {}
                    if src_record_type not in edge_hit_dict[dst_record_type]:
                        edge_hit_dict[dst_record_type][src_record_type] = {}
                    edge_hit_dict[dst_record_type][src_record_type][dst_record_id] = True
                    # adding dst_node to reason_dict
                    if init_flag == False:
                        add_reason(reason_dict, dst_record_type, dst_record_id, src_record_type, src_record_id)

    #FL.close()


    return node_hit_dict, edge_hit_dict, conn_dict





def filtered_out_flag_type_I(initial_hit_dict, record_type, record_id):


    if record_type in initial_hit_dict:
        if record_id not in initial_hit_dict[record_type]:
            return True

    return False


def filtered_out_flag_type_II(initial_hit_dict, node_hit_dict, record_type, record_id):
    
    #flag_one = filtered_out_flag_type_I(initial_hit_dict, record_type, record_id)
    flag_one = True
    if record_type in initial_hit_dict:
        if record_id in initial_hit_dict[record_type]:
            flag_one = False
    flag_two = True
    if record_type in node_hit_dict: 
        if record_id in node_hit_dict[record_type]:
            flag_two = False
    
    if flag_one == True and flag_two == True:
        return True

    return False


















def get_network_stat(network_dict):
   
    o = {}
    for record_type in network_dict:
        o[record_type] = len(list(network_dict[record_type].keys()))
    return o


def get_hit_stat(hit_dict):

    seen = {}
    for record_type in hit_dict:
        for record_id in hit_dict[record_type]:
            if record_type not in seen:
                seen[record_type] = {}
            seen[record_type][record_id] = True
    o = {}
    for record_type in seen:
        o[record_type] = len(list(seen[record_type].keys()))
    return o




def load_properity_lineage(in_obj, in_key, seen):

    if type(in_obj) in [dict, collections.OrderedDict]:
        for k in in_obj:
            new_key = in_key + "." + k if in_key != "" else k
            load_properity_lineage(in_obj[k], new_key, seen)
    elif type(in_obj) is list:
        for o in in_obj:
            load_properity_lineage(o, in_key, seen)
    elif type(in_obj) in [unicode, int, float]:
        value_type = str(type(in_obj)).replace("<type ", "").replace("'", "").replace(">", "")
        in_key += " %s" % (value_type)
        if in_key not in seen:
            seen[in_key] = True

    return 








def transform_query(in_obj, concept, seen_path, path_map):
    q_list = []
    em_match_obj = {}
    error_list = []
    if "unaggregated_list" in in_obj:
        for obj in in_obj["unaggregated_list"]:
            if concept not in seen_path:
                error_obj = {"error_code": "unknown-concept", "concept":concept}
                error_list.append(error_obj)
            elif obj["path"] not in path_map and obj["path"] not in seen_path[concept]:
                error_obj = {"error_code": "unknown-path", 
                        "concept":concept, "path":obj["path"]}
                error_list.append(error_obj)
            else:
                if "string_value" in obj:
                    if obj["string_value"] in [True, False]:
                        obj["string_value"] = str(obj["string_value"]).lower()

                val = ""
                val = obj["string_value"] if "string_value" in obj else val
                val = obj["numeric_value"] if "numeric_value" in obj else val
                
                if concept == "site" and "string_value" in obj:
                    if type(obj["string_value"]) is str:
                        if obj["string_value"].find("|") != -1:
                            d, s = obj["string_value"].split("|")
                            if obj["path"] == "up_seq":
                                l = int(d) - len(s)  
                                if l < 0:
                                    error_obj = {"error_code": "bad-regex-pattern"}
                                    error_list.append(error_obj)
                                s = s.upper().replace("X", "{1}[A-Z]")
                                val = "%s{%s}[A-Z]$" % (s,l)
                                if l == 0:
                                    val = "%s$" % (s)
                            elif obj["path"] == "down_seq":
                                l = int(d) - 1
                                if l < 1:
                                    error_obj = {"error_code": "bad-regex-pattern"}
                                    error_list.append(error_obj)
                                s = s.upper().replace("X", "{1}[A-Z]")
                                val = "^[A-Z]{%s}%s" % (l,s)
                                #"^[A-Z]{8}C"
                val_obj = {obj["operator"]:val}
                if obj["operator"] == "$eq" and "string_value" in obj:
                    if obj["path"] in ["start_aa", "site_seq"]:
                        val_obj = {"$eq":val}
                    else:
                        val = "^%s$" % (val)
                        val_obj = {"$regex":val, "$options":"i"}
                elif obj["operator"] == "$ne" and "string_value" in obj:
                    val = "^%s$" % (val)
                    val_obj = {"$not": {"$regex":val, "$options":"i"}}
                elif obj["operator"] == "$regex":
                    val_obj = {"$regex":val, "$options":"i"}

                o = {obj["path"]:val_obj}
                if obj["path"] in path_map:
                    local_agg = "$and" if obj["operator"] in ["$ne"] else "$or"
                    o = {local_agg:[]}
                    for new_path in path_map[obj["path"]]["targetlist"]:
                        new_o = {new_path:val_obj}
                        o[local_agg].append(new_o)
                    if "list_fields" in path_map:
                        if new_path in path_map["list_fields"]:
                            val_obj = {"$gt":[]} if obj["string_value"] == "true" else {"$eq":[]} 
                            o = {new_path:val_obj}
                path_parts = obj["path"].split(".")
                if path_parts[0] in ["neighbors"]:
                    if path_parts[0] not in em_match_obj:
                        em_match_obj[path_parts[0]] = {"$elemMatch":{}}
                    em_match_obj[path_parts[0]]["$elemMatch"][path_parts[1]] = val_obj
                else:
                    q_list.append(o)
        
    if "aggregated_list" in in_obj:
        for i in range(0, len(in_obj["aggregated_list"])):
            child_obj = in_obj["aggregated_list"][i]
            o, err_list = transform_query(child_obj, concept, seen_path, path_map)
            q_list.append(o)


    if em_match_obj != {}:
        q_list.append(em_match_obj)

    in_obj = {in_obj["aggregator"]:q_list} if q_list != [] else {}


    return in_obj, error_list



def add_reason(reason_dict, dst_record_type, dst_record_id, src_record_type, src_record_id):

    if dst_record_type not in reason_dict:
        reason_dict[dst_record_type] = {}
    if dst_record_id not in reason_dict[dst_record_type]:
        reason_dict[dst_record_type][dst_record_id] = {}
    if src_record_type not in reason_dict[dst_record_type][dst_record_id]:
        reason_dict[dst_record_type][dst_record_id][src_record_type] = {}
    reason_dict[dst_record_type][dst_record_id][src_record_type][src_record_id] = True

    return

def dump_debug_timer(flag,debug_flag):

    if debug_flag == True:
        print (datetime.datetime.now(), flag)
    return





