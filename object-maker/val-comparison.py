import os,sys
import json
import glob
import datetime
import csvutil
from optparse import OptionParser
import random
import orjson


def get_cmb_list(doc_two):

    condition_id = doc_two["condition"]["id"]
    cmb_list = []
    for obj in doc_two["biomarker_component"]:
        entity_id = obj["assessed_biomarker_entity_id"]
        biomarker = obj["biomarker"]
        cmb = "%s|%s|%s" % (entity_id, condition_id, biomarker)
        cmb_list.append(cmb)

    src_list = []
    for src in doc_two["source_list"]:
        src_list.append(src)

    return cmb_list, src_list


def compare_section_values(doc_one, doc_two, sec):

#best_biomarker_role <class 'list'>
#biomarker_component <class 'list'>
#evidence_source <class 'list'>
#entity_normal_ranges <class 'list'>

    set_one, set_two = set(["xxx"]), set(["yyy"])
    if sec in ["biomarker_id", "biomarker_canonical_id"]:
        set_one = set([doc_one[sec]])
        set_two = set([doc_two[sec]]) 
    elif sec in ["condition"]:
        set_one = set([doc_one[sec]["id"]] + [obj["id"] for obj in doc_one[sec]["synonyms"]])
        set_two = set([doc_two[sec]["id"]] + [obj["id"] for obj in doc_two[sec]["synonyms"]])
    elif sec in ["source_list"]:
        set_one = set([val for val in doc_one[sec]])
        set_two = set([val for val in doc_two[sec]])
    elif sec in ["citation"]:
        set_one = set([obj["reference"][0]["id"] for obj in doc_one[sec]])
        set_two = set([obj["reference"][0]["id"] for obj in doc_two[sec]])
    elif sec in ["crossref"]:
        set_one = set([obj["database"] for obj in doc_one[sec]])
        set_two = set([obj["database"] for obj in doc_two[sec]])
    elif sec in ["entity_normal_ranges"]:
        l_one, l_two = [], []
        for obj in doc_one[sec]:
            l_one.append(obj["entity_id"])
            l_one += [o["lab_term"] for o in obj["source"]]
        for obj in doc_two[sec]: 
            l_two.append(obj["entity_id"]) 
            l_two += [o["lab_term"] for o in obj["source"]]
        set_one = set(l_one)
        set_two = set(l_two)
    elif sec in ["best_biomarker_role"]:
        set_one = set([obj["role"] for obj in doc_one[sec]])
        set_two = set([obj["role"] for obj in doc_two[sec]])
    elif sec in ["evidence_source"]:
        l_one, l_two = [], []
        for obj in doc_one[sec]:
            l_one.append("evdn_id=" + obj["id"])
            l_one += ["evdn_txt=" + o["evidence"] for o in obj["evidence_list"]]
            l_one += ["evdn_tag=" +o["tag"] for o in obj["tags"]]
        for obj in doc_two[sec]:
            l_two.append("evdn_id=" + obj["id"])
            l_two += ["evdn_txt=" + o["evidence"] for o in obj["evidence_list"]]
            l_two += ["evdn_tag=" + o["tag"] for o in obj["tags"]]
        set_one = set(l_one)
        set_two = set(l_two)
    elif sec in ["biomarker_component"]:
        l_one, l_two = [], []
        for obj in doc_one[sec]:
            #for f in ["assessed_biomarker_entity_id","assessed_entity_type","biomarker"]:
            for f in ["assessed_biomarker_entity_id","assessed_entity_type"]:
                l_one.append(f+"="+obj[f] if f in obj else "")
            l_one += ["recname=" + obj["assessed_biomarker_entity"]["recommended_name"]]
            #l_one += ["synonym=" + o["synonym"] for o in obj["assessed_biomarker_entity"]["synonyms"]] 
            for o in obj["evidence_source"]:
                l_one.append("biomarker_component.evdn_id=" + o["id"])
                l_one += ["biomarker_component.evdn_txt=" + oo["evidence"] for oo in o["evidence_list"]]
                #l_one += ["evdn_tag=" + oo["tag"] for oo in o["tags"]]
        for obj in doc_two[sec]:
            #for f in ["assessed_biomarker_entity_id","assessed_entity_type","biomarker"]:
            for f in ["assessed_biomarker_entity_id","assessed_entity_type"]:
                l_two.append(f+"="+obj[f] if f in obj else "")
            l_two += ["recname=" + obj["assessed_biomarker_entity"]["recommended_name"]]
            #l_two += ["synonym=" + o["synonym"] for o in obj["assessed_biomarker_entity"]["synonyms"]]
            for o in obj["evidence_source"]:
                l_two.append("biomarker_component.evdn_id="+o["id"])
                l_two += ["biomarker_component.evdn_txt=" + oo["evidence"] for oo in o["evidence_list"]]
                #l_two += ["evdn_tag=" + oo["tag"] for oo in o["tags"]]
        #print (json.dumps(l_one, indent=4))
        #print (json.dumps(l_two, indent=4))
        #exit()
        set_one = set(l_one)
        set_two = set(l_two)
 
    diff = list(set_one - set_two)

    return diff


###############################
def main():


    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-r","--rel",action="store",dest="rel",help="")
    parser.add_option("-s","--start",action="store",dest="start",help="")
    parser.add_option("-e","--end",action="store",dest="end",help="")
    (options,args) = parser.parse_args()
    for key in ([options.rel, options.start, options.end]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    rel = options.rel
    s = int(options.start)
    e = int(options.end)

    global release_dir
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)


    #ver = "2025_12_22"
    ver = "current"
    #db_dir_one = "/data/shared/biomarkerdb/generated/datamodel/merged/%s/merged_json/" %(ver)
    db_dir_one = "/data/shared/biomarkerdb/generated/datamodel/merged/%s/merged_json_updated/" %(ver)
    db_dir_two = release_dir + "jsondb/biomarkerdb/"

    sec_list = [ 
        "biomarker_id", "biomarker_component", "condition", "evidence_source", "best_biomarker_role", 
        "biomarker_canonical_id", "citation", "crossref", "source_list", "entity_normal_ranges"
    ]
    sec_list.remove("source_list")


    file_list = glob.glob(release_dir + "jsondb/biomarkerdb/*.json")
    e = len(file_list) if e > len(file_list) else e

    out_file = "/data/shared/biomarkerdb/logs/val_comparison.%s-%s.txt" % (s, e)
    with open(out_file, "w") as FW:
        FW.write("")
                

    idx = 0
    total = len(file_list)
    for f_two in file_list[s-1:e]:
        fail_count = 0
        doc_list_two = orjson.loads(open(f_two, "rb").read())
        for doc_two in doc_list_two:
            biomarker_id = doc_two["biomarker_id"]
            f_one = db_dir_one + "%s.json" % (biomarker_id) 
            if os.path.isfile(f_one) == False:
                continue
            doc_one = orjson.loads(open(f_one, "rb").read())
            if doc_two["condition"] == {}:
                continue
            cmb_list, src_list = get_cmb_list(doc_two)
            #print (cmb_list, src_list)
            for sec in sec_list:
                diff = compare_section_values(doc_one, doc_two, sec)
                flag = diff == []
                if flag == False:
                    fail_count += 1
                    with open(out_file, "a") as FW:
                        FW.write("%s|%s|%s|%s\n" % (biomarker_id, sec, diff, src_list))
        with open(out_file, "a") as FW:
            FW.write("finished %s, fail_count=%s\n" % (f_two, fail_count))        
        
    return 




if __name__ == '__main__':
    main()
 
