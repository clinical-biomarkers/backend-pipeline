import os,sys
import json
import glob
import datetime
import csvutil
import subprocess
from optparse import OptionParser
import psutil
import orjson
import hashlib





def load_dsfilename2bcoid_remote(TOKEN):


    filename2bcoid = {}
    headers = {
        "Authorization":"Token " + TOKEN,
        "Content-Type":"application/json"
    }
    req_obj = {
        "POST_api_objects_search":[
            {"type":"bco_id","search":"BMK_"}
        ]
    }

    cmd =  'curl --request GET https://biocomputeobject.org/api/objects/search/'
    cmd += ' -H ' + '"Content-type:application/json"'
    cmd += ' -H ' + '"Authorization:Token %s" ' % (TOKEN)
    cmd += ' -d ' + '\'{"POST_api_objects_search":[{"type":"bco_id","search":"BMK_"}]}\''
    cmd += ' -o logs/bco.txt'
    x = subprocess.getoutput(cmd)
    x = subprocess.getoutput("cat logs/bco.txt")
    bco_obj_list = json.loads(x)
    for bco_doc in bco_obj_list:
        bco_id = bco_doc["object_id"].split("/")[-2]
        if bco_id.find("BMK_") == -1:
            continue
        bco_ver = bco_doc["object_id"].split("/")[-1]
        if bco_ver == "DRAFT" and "contents" in bco_doc:
            status_list = []
            if "extension_domain" in bco_doc["contents"]:
                for obj in bco_doc["contents"]["extension_domain"]:
                    if "dataset_extension" in obj:
                        o = obj["dataset_extension"]
                        if "dataset_categories" in o:
                            for oo in o["dataset_categories"]:
                                cat_name = oo["category_name"].lower() if "category_name" in oo else ""
                                cat_value = oo["category_value"].lower() if "category_value" in oo else ""
                                if cat_name == "status":
                                    status_list.append(cat_value)
            if "retired" in status_list:
                continue
            if "io_domain" in bco_doc["contents"]:
                for obj in bco_doc["contents"]["io_domain"]["output_subdomain"]:
                    if "uri" in obj:
                        if "filename" in obj["uri"]:
                            file_name = obj["uri"]["filename"]
                            if file_name.strip() != "" and file_name.find(".stat.csv") == -1:
                                filename2bcoid[file_name] = bco_id

    return filename2bcoid




     




def load_annotation_dict():

    in_file = release_dir + "unreviewed/annotations.tsv"

    tmp_dict_one = {}
    with open(in_file, "r") as FR:
        f_list, lcount = [], 0
        for line in FR:
            lcount += 1
            row = line[0:-1].split("\t")
            if lcount == 1:
                f_list = row
            else:
                ent_id = row[f_list.index("assessed_biomarker_entity_id")]
                xref_key = row[f_list.index("xref_key")]
                xref_id = row[f_list.index("xref_id")]
                annotation_category = row[f_list.index("annotation_category")]
                annotation_term = row[f_list.index("annotation_term")]
                if xref_key == "protein_xref_uniprotkb_fun" and ent_id.find(xref_id) == -1:
                    continue
                cmb_one = "%s|%s|%s" % (ent_id,annotation_category, annotation_term)
                cmb_two = "%s|%s" % (xref_key, xref_id)
                if cmb_one not in tmp_dict_one:
                    tmp_dict_one[cmb_one] = {}
                tmp_dict_one[cmb_one][cmb_two] = True
                

    
    tmp_dict_two = {}
    for cmb_one in tmp_dict_one:
        ent_id = cmb_one.split("|")[0]
        annotation_category = cmb_one.split("|")[1]
        annotation_term = "|".join(cmb_one.split("|")[2:])
        if ent_id not in tmp_dict_two:
            tmp_dict_two[ent_id] = []
        ann_obj = {"annotation_category":annotation_category, "annotation_term":annotation_term, "evidence":[]}
        for cmb_two in tmp_dict_one[cmb_one]:
            xref_key, xref_id = cmb_two.split("|")
            xref_lbl, xref_url = "", ""
            if xref_key in url_dict:
                xref_lbl, xref_url = url_dict[xref_key]["lbl"], url_dict[xref_key]["url"] % (xref_id)
            evdn_obj = {"id":xref_id, "database":xref_lbl, "url":xref_url}
            ann_obj["evidence"].append(evdn_obj)
        tmp_dict_two[ent_id].append(ann_obj)
            
    return tmp_dict_two


 

        

def load_crossref_dict():

    in_file = release_dir + "unreviewed/xrefs.tsv"
    tmp_dict = {}
    with open(in_file, "r") as FR:
        f_list, lcount = [], 0
        for line in FR:
            lcount += 1
            row = line[0:-1].split("\t")
            if lcount == 1:
                f_list = row
            else:
                source_file = row[f_list.index("source_file")]
                biomarker_idx = row[f_list.index("biomarker_idx")]
                xref_key = row[f_list.index("xref_key")]
                xref_id = row[f_list.index("xref_id")]
                cmb_one = "%s|%s" % (source_file,biomarker_idx)
                cmb_two = "%s|%s" % (xref_key,xref_id)
                if cmb_one not in tmp_dict:
                    tmp_dict[cmb_one] = {}
                tmp_dict[cmb_one][cmb_two] = True

    return tmp_dict    





def main():

    
    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog " )
    parser.add_option("-r","--rel",action="store",dest="rel",help="")

    (options,args) = parser.parse_args()
    for file in ([options.rel]):
        if not (file):
            parser.print_help()
            sys.exit(0)

    rel = options.rel
    global release_dir
    global log_dir
    global url_dict

    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)
    log_dir = "/data/shared/biomarkerdb/logs/"
    #release_dir = "/local/v-%s/" % (rel)
    #log_dir = "/local/v-%s/logs/" % (rel)


    #dsfilename2bcoid = load_dsfilename2bcoid_remote(TOKEN)
    in_file = release_dir + "misc/ds2bco.json"
    dsfilename2bcoid = json.load(open(in_file))


    url_dict = csvutil.load_url_dict(release_dir + "misc/xref_info.csv")
    ds_dict = json.load(open(release_dir + "misc/datasets.json"))
    crossref_dict = load_crossref_dict()
    annotation_dict = load_annotation_dict()

    llm_src_list = ds_dict["llm_dataset_sources"]

    prt_name_dict, gene_name_dict = csvutil.load_entity_names()
    cite_dict = csvutil.load_cite_dict(release_dir)
    cmblist2src, grp2cmblist = csvutil.load_cmblist2src(release_dir)

    canon2conagent_dict = csvutil.load_canon2conagent_dict(grp2cmblist, release_dir)
    canon_id_md5_list = sorted(list(canon2conagent_dict.keys()))
    canon_id_dict, canonid2maxindex, cmblist2biomarkerid = csvutil.load_canon_id_dict(rel,canon_id_md5_list)


    # this means, jsondb/idgendb/ objects need to be created
    # before jsondb/biomarkerdb objects
    biomarker_id_dict = {}
    file_list = glob.glob(release_dir + "jsondb/idgendb/batch.*.json")
    for in_file in file_list:
        doc_list = json.load(open(in_file))
        for doc in doc_list:
            biomarker_id_dict[doc["biomarker_id_md5"]] = doc
        

    
    norma_ranges_dict = {}
    file_list = glob.glob(release_dir + "jsondb/normalrangesdb/*.json")
    for in_file in file_list:
        doc = json.load(open(in_file))
        ent_id = doc["entity_id"]
        norma_ranges_dict[ent_id] = doc




    disease_dict = {}
    file_list = glob.glob(release_dir + "jsondb/diseasedb/*.json")
    for in_file in file_list:
        doc_list = json.load(open(in_file))
        for doc in doc_list:
            disease_id = doc["id"].lower().replace(":",".")
            disease_dict[disease_id] = doc
       


 

    DEBUG = False
    #DEBUG = True
    file_list = glob.glob(release_dir + "unreviewed/biomarkers_*.tsv")
    #file_list = glob.glob(release_dir + "unreviewed/biomarkers_llm_glycan*.tsv")


    id_counter = 0
    row_dict = {}
    grp_dict = {}
    dsfilename_dict = {}
    for in_file in file_list:
        file_name = in_file.split("/")[-1]
        source = in_file.split("/")[-1].replace("biomarkers_","").replace(".tsv","")
        log_file = log_dir + "make-biomarkers-%s.log" % (source)
        with open(log_file, "w") as FL:
            FL.write("")
        with open(in_file, "r") as FR:
            f_list, lcount = [], 0
            for line in FR:
                lcount += 1
                row = line[0:-1].split("\t")
                if lcount == 1:
                    f_list = row
                else:
                    biomarker = row[f_list.index("biomarker")]
                    biomarker_controlled_vocab = row[f_list.index("biomarker_controlled_vocab")]
                    entity_id = row[f_list.index("assessed_biomarker_entity_id")]
                    condition_id = row[f_list.index("condition_id")]
                    agent_id = row[f_list.index("exposure_agent_id")]
                    grp_idx = ""
                    for k in ["biomarker_index", "component_group"]:
                        grp_idx = row[f_list.index(k)] if k in f_list else grp_idx
                    if grp_idx == "":
                        continue
                                        
                    if condition_id == "" and agent_id == "":
                        with open(log_file, "a") as FL:
                            FL.write("%s\n" % ("\t".join(["missing_condition_id and exposure_agent_id"]+ row)))
                        continue
                    grp = "%s|%s" % (source, grp_idx)
                    cmb_list = grp2cmblist[grp]
                    cmb_list_str = json.dumps(cmb_list)
                    if cmb_list_str not in row_dict:
                        row_dict[cmb_list_str] = {}
                    cmb = "%s|%s|%s|%s" % (entity_id,condition_id,agent_id,biomarker_controlled_vocab)
                    if cmb not in row_dict[cmb_list_str]:
                        row_dict[cmb_list_str][cmb] = []
                    row_obj = {}
                    for f in f_list:
                        row_obj[f] = row[f_list.index(f)]
                    row_dict[cmb_list_str][cmb].append(row_obj)
                    dsfilename_dict[cmb_list_str] = file_name

    
    log_file = log_dir + "make-biomarker-progress.log"
    with open(log_file, "w") as FL:
        FL.write("")

    cmb_list_str_list = list(row_dict.keys())
    cmb_list_str_list = sorted(cmb_list_str_list)


    missing_obj_list = []
    for canon_id_md5 in canon_id_md5_list:
        canon_id_new = canon_id_dict[canon_id_md5]
        idx = 0
        for d_id in canon2conagent_dict[canon_id_md5]:
            idx += 1
            s = canon_id_md5 + d_id
            biomarker_id_md5 = hashlib.md5(s.encode('utf-8')).hexdigest()
            biomarker_id_new = "%s-%s" % (canon_id_new, idx)
            if biomarker_id_md5 not in biomarker_id_dict:
                info_obj = canon2conagent_dict[canon_id_md5][d_id]
                oo = {"biomarker_id_new":biomarker_id_new, "info":info_obj}
                missing_obj_list.append(oo)
    
    if missing_obj_list != []:
        with open(log_file, "a") as FL:
            for oo in missing_obj_list:
                FL.write("ID missing:%s\n" % (json.dumps(oo)))


    out_dir = release_dir + "jsondb/biomarkerdb/"
    final_id_list = [] 
    total_created = 0
    missed = 0 
    total = len(cmb_list_str_list)
    record_obj_list =  []
    bmkb_idx, batch_idx = 0, 0


    for canon_id_md5 in canon2conagent_dict:
        canon_id_new = canon_id_dict[canon_id_md5]
        idx = 0
        for d_id in canon2conagent_dict[canon_id_md5]:
            cmb_list = canon2conagent_dict[canon_id_md5][d_id]["cmblist"]
            cmb_list_str = json.dumps(cmb_list)
            if cmb_list_str not in row_dict:
                continue
            bco_id = ""
            if cmb_list_str in dsfilename_dict:
                dsfilename = dsfilename_dict[cmb_list_str]
                if dsfilename in dsfilename2bcoid:
                    bco_id = dsfilename2bcoid[dsfilename]               
                         
         
            src_list = list(cmblist2src[cmb_list_str].keys())
            idx += 1
            bmkb_idx += 1
            s = canon_id_md5 + d_id
            biomarker_id_md5 = hashlib.md5(s.encode('utf-8')).hexdigest()
            biomarker_id_new = "%s-%s" % (canon_id_new, idx)
            grp = canon2conagent_dict[canon_id_md5][d_id]["grp"]
            
            if biomarker_id_md5 not in biomarker_id_dict:
                missed += 1
                continue
            biomarker_id_list = biomarker_id_dict[biomarker_id_md5]["biomarker_id_list"]
            role_dict, evdn_dict = {}, {}
            
            comp_dict = {}
            agent_id2name = {}
            for cmb in row_dict[cmb_list_str]:
                for row_obj in row_dict[cmb_list_str][cmb]:
                    if row_obj["best_biomarker_role"] != "":
                        for role in row_obj["best_biomarker_role"].split(";"):
                            role_dict[role] = True
                    evdn_id = row_obj["evidence_source"]
                    if evdn_id not in evdn_dict:
                        evdn_dict[evdn_id] = {"text":{}, "tags":[]}
                    evdn_dict[evdn_id]["text"][row_obj["evidence"]] = True
                    evdn_dict[evdn_id]["tags"] += row_obj["tag"].split(";") 
                    exposure_agent = row_obj["exposure_agent"]
                    agent_id = row_obj["exposure_agent_id"]
                    agent_id2name[agent_id] = exposure_agent
                    entity_id, entity_type = row_obj["assessed_biomarker_entity_id"], row_obj["assessed_entity_type"]
                    entity, biomarker_orig = row_obj["assessed_biomarker_entity"], row_obj["biomarker"]
                    biomarker = row_obj["biomarker_controlled_vocab"]
                    specimen_id, specimen,loinc_code = row_obj["specimen_id"], row_obj["specimen"], row_obj["loinc_code"]
                    specimen_obj = {}
                    if specimen_id != "":
                        specimen_ns = specimen_id.split(":")[0]       
                        xref_key, xref_id = specimen_ns.lower(), specimen_id.split(":")[1]
                        xref_url = url_dict[xref_key]["url"] % (xref_id) if xref_key in url_dict else ""
                        specimen_obj = { "id":specimen_id, "name":specimen, "loinc_code":loinc_code, 
                            "name_space":specimen_ns, 
                            "url":xref_url,
                            "loince_code_url":""
                        }
                        if loinc_code != "" and "loinc" in url_dict:
                            specimen_obj["loince_code_url"] = url_dict["loinc"]["url"] % (loinc_code)
                    if entity_id not in comp_dict:
                        rec_name, syn_obj_list = entity, []
                        if entity_type == "protein" and entity_id in prt_name_dict:
                            for name_obj in prt_name_dict[entity_id]:
                                if name_obj["type"] == "synonym":
                                    syn_obj_list.append({"synonym":name_obj["name"]})
                        ann_obj_list = annotation_dict[entity_id] if entity_id in annotation_dict else []
                        comp_dict[entity_id] = {
                            "assessed_biomarker_entity_id":entity_id,
                            "assessed_biomarker_entity_url":"",
                            "assessed_biomarker_entity":{ "recommended_name":rec_name, "synonyms": syn_obj_list},
                            "assessed_entity_type":entity_type,
                            "biomarker_orig":biomarker_orig,
                            "biomarker":biomarker,
                            "annotations":ann_obj_list
                        }
                        entity_ns = entity_id.split(":")[0].lower()
                        if entity_ns in url_dict:
                            entity_url =  url_dict[entity_ns]["url"] % (entity_id.split(":")[1])
                            comp_dict[entity_id]["assessed_biomarker_entity_url"] = entity_url

                    if evdn_id != "":
                        if "evidence_dict" not in comp_dict[entity_id]:
                            comp_dict[entity_id]["evidence_dict"] = {}
                        comp_dict[entity_id]["evidence_dict"][evdn_id] = evdn_dict[evdn_id]
 
                    if specimen_id != "":
                        if "specimen_dict" not in comp_dict[entity_id]:
                            comp_dict[entity_id]["specimen_dict"] = {}
                        comp_dict[entity_id]["specimen_dict"][specimen_id] = specimen_obj

            biomarker_id = biomarker_id_list[0]
            data_src_list = []
            for s in src_list:
                src, biomarker_idx = s.split("|")
                data_src_list.append(src)
            
 
            record_obj = {
                "biomarker_id":biomarker_id,
                "biomarker_canonical_id":biomarker_id.split("-")[0],
                "biomarker_id_md5":biomarker_id_md5,
                "canon_id_md5":canon_id_md5,
                "biomarker_id_new":biomarker_id_new,
                "condition":{},
                "best_biomarker_role":[],
                "biomarker_component":[],
                "evidence_source":[],
                "citation_dict":{},
                "citation_evdn_dict":{},
                "crossref":[],
                "entity_normal_ranges":[],
                "keywords":[],
                "source_list":data_src_list
            }
            print ("Robel-1", canon_id_md5, biomarker_id_md5, biomarker_id, data_src_list)
            
            final_id_list.append(";".join(biomarker_id_list))
            #--> best_biomarker_role
            for role in role_dict:
                record_obj["best_biomarker_role"].append({"role":role})

            #-->evidence_source and citation
            for evdn_id in evdn_dict:
                xref_key, xref_id = evdn_id.lower().split(":")[0], evdn_id.split(":")[1]
                xref_lbl, xref_url = "", ""
                if xref_key in url_dict:
                    xref_lbl, xref_url = url_dict[xref_key]["lbl"], url_dict[xref_key]["url"] % (xref_id)
                evdn_obj = {"id":xref_id, "database":xref_lbl, "url":xref_url, "evidence_list":[], "tags":[]}
                for text in evdn_dict[evdn_id]["text"]:
                    for txt in text.split("|"):
                        if txt.strip() != "":
                            txt = txt[:-1] if txt[-1] == ";" else txt
                            evdn_obj["evidence_list"].append({"evidence":txt})
                for tag in evdn_dict[evdn_id]["tags"]:
                    evdn_obj["tags"].append({"tag":tag})
                record_obj["evidence_source"].append(evdn_obj)

            #-->condition/exposure
            disease_id = cmb_list[0].split("|")[1].replace(":",".").lower()
            agent_id = cmb_list[0].split("|")[2]
            if disease_id != "":
                if disease_id in disease_dict:
                    record_obj["condition"] = disease_dict[disease_id]
                else:
                    with open(log_file, "a") as FL:
                        FL.write("ERROR|disease_file_not_found|%s|%s\n" % (disease_id,cmb_list_str))
                    missed += 1
                    print ("Robel-2", canon_id_md5, biomarker_id_md5, biomarker_id, data_src_list)
                    continue
            elif agent_id != "":
                agent_name = agent_id2name[agent_id] if agent_id in agent_id2name else ""
                record_obj["exposure_agent"] = {
                    "id": agent_id,
                    "recommended_name": {
                        "id": agent_id,
                        "name": agent_name,
                        "description": "",
                        "resource": "",
                        "url": ""
                    },
                    "synonyms": []
                }

            #-->crossref
            for src in src_list:
                if src in crossref_dict:
                    for pair in crossref_dict[src]:
                        xref_key, xref_id = pair.split("|")
                        if xref_key in url_dict:
                            xref_lbl, xref_url = url_dict[xref_key]["lbl"], url_dict[xref_key]["url"] % (xref_id)
                            o = {"id":xref_id, "url":xref_url, "database":xref_lbl, "categories":[]}
                            record_obj["crossref"].append(o)


            #-->biomarker_component
            for entity_id in comp_dict:
                comp_obj = comp_dict[entity_id]
                comp_obj["evidence_source"] = []
                # add LLM evidence for sources in llm_src_list
                if len(list(set(llm_src_list).intersection(set(data_src_list)))) > 0:
                    oo = {"id":"","database":"LLM-Extracted","url":"","evidence_list":[],"tags":[]}
                    comp_obj["evidence_source"].append(oo)
                if bco_id != "":
                    xref_key, xref_id, xref_lbl, xref_url = "biomarkerkb", bco_id, "", ""
                    if xref_key in url_dict:
                        xref_lbl,xref_url = url_dict[xref_key]["lbl"],url_dict[xref_key]["url"] % (xref_id)
                        oo = {"id":xref_id,"database":xref_lbl,"url":xref_url,"evidence_list":[],"tags":[]}
                        comp_obj["evidence_source"].append(oo)
                    

                if "evidence_dict" in comp_obj:
                    # order evidences so that publications are on top
                    # so that other evidences can be under "evidence" subfield of citations objects
                    ordr_list_one,ordr_list_two = [], []
                    for evdn_id in comp_obj["evidence_dict"]:
                        xref_key, xref_id = evdn_id.lower().split(":")
                        if xref_key in ["pubmed", "doi"]:
                            ordr_list_one.append(evdn_id)
                        else:
                            ordr_list_two.append(evdn_id)
                    ordr_list = ordr_list_one + ordr_list_two
                    cmp_evdn_dict = comp_obj["evidence_dict"] 
                    sorted_cmp_evdn_dict = {key: cmp_evdn_dict[key] for key in ordr_list if key in cmp_evdn_dict}
                    pub_id = ""
                    for evdn_id in sorted_cmp_evdn_dict:
                        xref_key, xref_id = evdn_id.lower().split(":")[0], evdn_id.split(":")[1]
                        xref_lbl, xref_url = "", ""
                        if xref_key in url_dict:
                            xref_lbl, xref_url = url_dict[xref_key]["lbl"], url_dict[xref_key]["url"] % (xref_id)
                        evdn_obj = {"id":xref_id, "database":xref_lbl, "url":xref_url, "evidence_list":[], "tags":[]}
                        for text in sorted_cmp_evdn_dict[evdn_id]["text"]:
                            for txt in text.split("|"):
                                if txt.strip() != "":
                                    txt = txt[:-1] if txt[-1] == ";" else txt
                                    evdn_obj["evidence_list"].append({"evidence":txt})
                        for tag in sorted_cmp_evdn_dict[evdn_id]["tags"]:
                            evdn_obj["tags"].append({"tag":tag})
                        comp_obj["evidence_source"].append(evdn_obj)
                        if xref_key in ["pubmed", "doi"]:
                            pub_id = xref_id.lower().replace("pubmed:","").replace("doi:","")
                            cite_obj = cite_dict[pub_id] if pub_id in cite_dict else {}
                            if cite_obj != {} and pub_id not in record_obj["citation_dict"]:
                                record_obj["citation_dict"][pub_id] = cite_obj
                        else:
                            oo = {"id":xref_id, "database":xref_lbl, "url":xref_url}
                            xref_cmb = "%s|%s" % (xref_lbl,xref_id)
                            record_obj["citation_evdn_dict"][xref_cmb] = oo
                    comp_obj.pop("evidence_dict")
            
                comp_obj["specimen"] = []
                if "specimen_dict" in comp_obj:
                    for specimen_id in comp_obj["specimen_dict"]:
                        comp_obj["specimen"].append(comp_obj["specimen_dict"][specimen_id])            
                    comp_obj.pop("specimen_dict")
                record_obj["biomarker_component"].append(comp_obj)
        
 
            if len(record_obj["biomarker_component"]) > 1:
                kw = "panel_biomarker"
                record_obj["keywords"].append(kw)
                
            #-->entity_normal_ranges
            for entity_id in comp_dict:
                if entity_id in norma_ranges_dict:
                    record_obj["entity_normal_ranges"].append(norma_ranges_dict[entity_id])

            cite_evdn_obj_list = []
            for ref_cmb in record_obj["citation_evdn_dict"]:
                cite_evdn_obj_list.append(record_obj["citation_evdn_dict"][ref_cmb])
            record_obj.pop("citation_evdn_dict")

            cite_obj_list = []
            for pub_id in record_obj["citation_dict"]:
                obj = record_obj["citation_dict"][pub_id]
                obj["evidence"] = cite_evdn_obj_list
                cite_obj_list.append(obj)
            record_obj["citation"] = cite_obj_list
            record_obj.pop("citation_dict")
            if DEBUG:
                print (json.dumps(record_obj, indent=4))
            
            record_obj_list.append(record_obj)
                        
    
            if DEBUG == False and len(record_obj_list) == 100:
                batch_idx +=1
                total_created += len(record_obj_list)
                out_file = out_dir + "batch.%s.json" % (batch_idx)
                with open(out_file, "wb") as FW:
                    FW.write(orjson.dumps(record_obj_list))
                ts = datetime.datetime.now()
                with open(log_file, "a") as FL:
                    FL.write("%s created %s/%s records (%s missed)\n" % (ts, total_created, total, missed))
                record_obj_list = []
            

    ts = datetime.datetime.now()
    with open(log_file, "a") as FL:
        FL.write("%s finished loop\n" % (ts))

    if DEBUG == False and len(record_obj_list) > 0:
        batch_idx +=1
        total_created += len(record_obj_list)
        out_file = out_dir + "batch.%s.json" % (batch_idx)
        with open(out_file, "wb") as FW:
            FW.write(orjson.dumps(record_obj_list))
        ts = datetime.datetime.now()
        with open(log_file, "a") as FL:
            FL.write("%s created %s/%s records (%s missed)\n" % (ts, total_created, total, missed)) 

    if final_id_list != []:
        out_file = log_dir + "make-biomarker.idlist.json"
        with open(out_file, "w") as FW:
            FW.write("%s\n" % (json.dumps(final_id_list, indent=4)))




 
    return 




if __name__ == '__main__':
    main()
 
