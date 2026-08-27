#!/usr/bin/python
import os,sys
import string
import csv
import json
import glob
from csvutil import parse_sent, write_log_msg
from optparse import OptionParser
import datetime
import pytz
import orjson



def get_disease_obj_list(sec_obj_list, record_id, record_type):

    obj_list = []
    phrase_dict_one, phrase_dict_two = {}, {}

    for obj in sec_obj_list:
        if "recommended_name" in obj:
            parse_sent(obj["recommended_name"]["id"], phrase_dict_one, 1)
            parse_sent(obj["recommended_name"]["name"], phrase_dict_two, 1)
        if "synonyms" in obj:
            for o in obj["synonyms"]:
                parse_sent(o["id"], phrase_dict_one, 1)
    if phrase_dict_one != {}:
        p_list = list(phrase_dict_one.keys())
        obj_list.append({"record_id":record_id, "record_type":record_type,
            "section":"condition_id", "phraselist":p_list})
    if phrase_dict_two != {}:
        p_list = list(phrase_dict_two.keys())
        obj_list.append({"record_id":record_id, "record_type":record_type,
            "section":"condition_name","phraselist":p_list})


    return obj_list



def get_crossref_obj_list(sec_obj_list, record_id, record_type):

    obj_list = []
    phrase_dict_one = {}
    for obj in sec_obj_list:
        parse_sent(obj["id"], phrase_dict_one, 1)
    if phrase_dict_one != {}:
        p_list = list(phrase_dict_one.keys())
        obj_list.append({"record_id":record_id, "record_type":record_type,
            "section":"crossref", "phraselist":p_list})

    return obj_list


def get_publication_obj_list(sec_obj_list, record_id, record_type):

    obj_list = []
    phrase_dict_one = {}
    for obj in sec_obj_list:
        for o in obj["reference"]:
            parse_sent(o["id"], phrase_dict_one, 1)
    if phrase_dict_one != {}:
        p_list = list(phrase_dict_one.keys())
        obj_list.append({"record_id":record_id, "record_type":record_type,
            "section":"publication", "phraselist":p_list})

    return obj_list



def get_biomarker_record(in_file, doc):

    obj_list = []
    file_name = in_file.split("/")[-1]
    record_id = doc["biomarker_id"]
    record_type = "biomarker"

    #-- biomarker_id
    sec = "biomarker_id"
    phrase_dict = {}
    for f in ["biomarker_id"]:
        parse_sent(doc[f], phrase_dict, 1)
    if phrase_dict != {}:
        p_list = list(phrase_dict.keys())
        obj_list.append({"record_id":record_id, "record_type":record_type,
            "section":sec, "phraselist":p_list})

    #-- biomarker_canonical_id
    sec = "biomarker_canonical_id"
    phrase_dict = {}
    for f in ["biomarker_canonical_id"]:
        parse_sent(doc[f], phrase_dict, 1)
    if phrase_dict != {}:
        p_list = list(phrase_dict.keys())
        obj_list.append({"record_id":record_id, "record_type":record_type,
            "section":sec, "phraselist":p_list})


    # -- source_list
    sec = "source_list"
    phrase_dict = {}
    for source in doc[sec]:
        parse_sent(source, phrase_dict, 1)
    if phrase_dict != {}:
        p_list = list(phrase_dict.keys())
        obj_list.append({"record_id":record_id, "record_type":record_type,
            "section":sec, "phraselist":p_list})

    # -- keywords
    sec = "keywords"
    phrase_dict = {}
    for kw in doc[sec]:
        parse_sent(kw, phrase_dict, 1)
    if phrase_dict != {}:
        p_list = list(phrase_dict.keys())
        obj_list.append({"record_id":record_id, "record_type":record_type,
            "section":sec, "phraselist":p_list})


    #-- publication
    for sec in ["citation"]:
        if sec not in  doc:
            continue
        obj_list += get_publication_obj_list(doc[sec], record_id, record_type)

    #--> crossref
    for sec in ["crossref"]:
        if sec not in doc:
            continue
        obj_list += get_crossref_obj_list(doc[sec], record_id, record_type)

    #-->condition
    for sec in ["condition"]:
        if sec not in doc:
            continue
        obj_list += get_disease_obj_list([doc[sec]], record_id, record_type)


     
    # -- best_biomarker_role
    sec = "best_biomarker_role"
    phrase_dict = {}
    if sec in doc:
        for o in doc[sec]:
            parse_sent(o["role"], phrase_dict, 1)
    if phrase_dict != {}:
        p_list = list(phrase_dict.keys())
        obj_list.append({"record_id":record_id, "record_type":record_type,
            "section":"best_biomarker_role", "phraselist":p_list})


    #-->biomarker_component
    for sec in ["biomarker_component"]:
        if sec not in doc:
            continue
        
        phrase_dict_specimen_id, phrase_dict_loinc_code, phrase_dict_specimen_name = {}, {}, {}
        phrase_dict_entity_id, phrase_dict_entity_name, phrase_dict_biomarker_vocab = {}, {}, {}
        phrase_dict_entity_type = {}
        for obj in doc[sec]:
            for k in ["assessed_biomarker_entity_id"]:
                if k not in obj:
                    continue
                val = str(obj[k])
                parse_sent(val, phrase_dict_entity_id, 1)
                if val.find(":") != -1:
                    parse_sent(val.split(":")[1], phrase_dict_entity_id, 1)
            for k in ["assessed_entity_type"]:
                if k not in obj:
                    continue
                parse_sent(str(obj[k]), phrase_dict_entity_type, 1)
            for k in ["biomarker"]:
                if k not in obj:
                    continue
                parse_sent(str(obj[k]), phrase_dict_biomarker_vocab, 1)
            if "assessed_biomarker_entity" in obj:
                o = obj["assessed_biomarker_entity"]
                if "recommended_name" in o:
                    parse_sent(o["recommended_name"], phrase_dict_entity_name, 1)
                if "synonyms" in o:
                    for oo in o["synonyms"]:
                        parse_sent(oo["synonym"], phrase_dict_entity_name, 1)
            if "specimen" in obj:
                for o in obj["specimen"]:
                    if "name_space" in o and "id" in o:
                        parse_sent(o["id"], phrase_dict_specimen_id, 1) 
                    if "loinc_code" in o:
                        parse_sent(o["loinc_code"], phrase_dict_loinc_code, 1)
                    if "name" in o:
                        parse_sent(o["name"], phrase_dict_specimen_name, 1)
                    
        if phrase_dict_entity_id != {}:
            p_list = list(phrase_dict_entity_id.keys())
            obj_list.append({"record_id":record_id, "record_type":record_type,
                "section":"entity_id", "phraselist":p_list})
        if phrase_dict_entity_type != {}:
            p_list = list(phrase_dict_entity_type.keys())
            obj_list.append({"record_id":record_id, "record_type":record_type,
                "section":"entity_type", "phraselist":p_list})
        if phrase_dict_entity_name != {}:
            p_list = list(phrase_dict_entity_name.keys())
            obj_list.append({"record_id":record_id, "record_type":record_type,
                "section":"entity_name","phraselist":p_list})
        if phrase_dict_biomarker_vocab != {}:
            p_list = list(phrase_dict_biomarker_vocab.keys())
            obj_list.append({"record_id":record_id, "record_type":record_type,
                "section":"biomarker_vocab","phraselist":p_list})        

        if phrase_dict_loinc_code != {}:
            p_list = list(phrase_dict_loinc_code.keys())
            obj_list.append({"record_id":record_id, "record_type":record_type,
                "section":"loinc_code", "phraselist":p_list})
        if phrase_dict_specimen_id != {}:
            p_list = list(phrase_dict_specimen_id.keys())
            obj_list.append({"record_id":record_id, "record_type":record_type,
                "section":"specimen_id", "phraselist":p_list})
        if phrase_dict_specimen_name != {}:
            p_list = list(phrase_dict_specimen_name.keys())
            obj_list.append({"record_id":record_id, "record_type":record_type,
                "section":"specimen_name", "phraselist":p_list})




    return obj_list





def main():

    
    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog " )
    parser.add_option("-r","--rel",action="store",dest="rel",help="")
    parser.add_option("-s","--start",action="store",dest="start",help="")
    parser.add_option("-e","--end",action="store",dest="end",help="")
    (options,args) = parser.parse_args()
    for file in ([options.rel, options.start, options.end]):
        if not (file):
            parser.print_help()
            sys.exit(0)

    rel = options.rel
    start = int(options.start)
    end = int(options.end)

    global release_dir
    global MAX_WORD_COUNT
    MAX_WORD_COUNT = 6
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)
    
    DEBUG = False
    #DEBUG = True
    pattern_dict = {"biomarker":["*"]}
    if DEBUG:
        pattern_dict = {"biomarker":["*"]}


    file_obj_list = []
    for record_type in sorted(list(pattern_dict.keys())):
        file_list = []
        for ptrn in pattern_dict[record_type]:
            glob_str = release_dir + "jsondb/%sdb/%s.json" % (record_type, ptrn)
            file_list += glob.glob(glob_str)
        file_list = sorted(list(set(file_list)))
        for json_file in file_list:
            file_obj_list.append({"file":json_file, "record_type":record_type})


    end = end if end < len(file_obj_list) else len(file_obj_list)
    log_file = "/data/shared/biomarkerdb/logs/make-indexdb.%s-%s.log" % (start, end)
   
    
    msg = "make-indexdb: started logging"
    write_log_msg(log_file, msg, "w")

    
    record_count = 0
    for obj in file_obj_list[start-1:end]:
        record_type = obj["record_type"]
        json_file = obj["file"]
        file_name = json_file.split("/")[-1]
        doc_list = orjson.loads(open(json_file,"r").read())
        record_obj_list = []
        for doc in doc_list:
            record_obj = get_biomarker_record(json_file, doc)
            #print (json.dumps(record_obj, indent=4))
            if record_obj != []:
                record_obj_list.append(record_obj)
        out_file = release_dir + "jsondb/indexdb/%s" % (file_name)
        with open(out_file, "w") as FW:
            FW.write("%s\n" % (json.dumps(record_obj_list, indent=4)))
        record_count += 1
        if record_count > 0 and record_count%1000 == 0:
            msg = "make-indexdb: created %s %s indexdb records" % (record_type, record_count)
            write_log_msg(log_file, msg, "a")

    msg = "make-indexdb: FINAL %s files" % (record_count)
    write_log_msg(log_file, msg, "a")


 

    return



if __name__ == '__main__':
    main()



