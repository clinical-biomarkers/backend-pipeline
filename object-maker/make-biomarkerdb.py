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







        

def load_crossref_dict():

    in_file = "unreviewed/xrefs.tsv"
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


    crossref_dict = load_crossref_dict()

    # this means, jsondb/idtrackdb/ objects need to be created
    # before jsondb/biomarkerdb objects
    biomarker_id_dict = {}
    file_list = glob.glob("jsondb/idtrackdb/biomarker.*.json")
    for in_file in file_list:
        doc = json.load(open(in_file))
        biomarker_id_dict[doc["biomarker_id_md5"]] = doc["biomarker_id_new"]
        

    prt_name_dict, gene_name_dict = csvutil.load_entity_names()
    url_dict = csvutil.load_url_dict("misc/xref_info.csv")
    cite_dict = csvutil.load_cite_dict()
    cmb2biomarkerid = csvutil.load_cmb2biomarkerid()
    cmblist2src, grp2cmblist = csvutil.load_cmblist2src()

     
    norma_ranges_dict = {}
    file_list = glob.glob("jsondb/normalrangesdb/*.json")
    for in_file in file_list:
        doc = json.load(open(in_file))
        ent_id = doc["entity_id"]
        norma_ranges_dict[ent_id] = doc


    disease_dict = {}
    file_list = glob.glob("jsondb/diseasedb/*.json")
    for in_file in file_list:
        doc_list = json.load(open(in_file))
        for doc in doc_list:
            disease_id = doc["id"].lower().replace(":",".")
            disease_dict[disease_id] = doc
        
    

    id_counter = 0
    row_dict = {}
    grp_dict = {}
    file_list = glob.glob("unreviewed/biomarkers_*.tsv")
    for in_file in file_list:
        source = in_file.split("/")[-1].replace("biomarkers_","").replace(".tsv","")
        #grp_dict = {}
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
                    grp_idx = row[f_list.index("component_group")]
                    if condition_id == "":
                        continue
                    grp = "%s|%s" % (source, grp_idx)
                    cmb_list = grp2cmblist[grp]
                    cmb_list_str = json.dumps(cmb_list)
                    if cmb_list_str not in row_dict:
                        row_dict[cmb_list_str] = {}
                    
                    cmb = "%s|%s|%s" % (entity_id,condition_id,biomarker_controlled_vocab)
                    if cmb not in row_dict[cmb_list_str]:
                        row_dict[cmb_list_str][cmb] = []
                    row_obj = {}
                    for f in f_list:
                        row_obj[f] = row[f_list.index(f)]
                    row_dict[cmb_list_str][cmb].append(row_obj)

    DEBUG = False
    #DEBUG = True
    cmb_list_str_list = list(row_dict.keys())
    cmb_list_str_list = sorted(cmb_list_str_list)

    log_file = "logs/make-biomarker.json"
    with open(log_file, "w") as FL:
        FL.write("") 

    missing_id_list = []
    for cmb_list_str in cmb_list_str_list:
        biomarker_id_md5 = hashlib.md5(cmb_list_str.encode('utf-8')).hexdigest()
        if biomarker_id_md5 not in biomarker_id_dict:
            missing_id_list.append(cmb_list_str)

    #if missing_id_list != []:
    #    with open(log_file, "a") as FL:
    #        for cmb_list_str in missing_id_list:
    #            FL.write("ID missing for %s\n" % (cmb_list_str))
    #    #exit()


    out_dir = "jsondb/biomarkerdb/"

    final_id_list = [] 
    total_created = 0
    missed = 0 
    total = len(cmb_list_str_list)
    record_obj_list =  []
    bmkb_idx, batch_idx = 0, 0 
    for cmb_list_str in cmb_list_str_list:
        biomarker_id_md5 = hashlib.md5(cmb_list_str.encode('utf-8')).hexdigest()
        #biomarker_id_new = biomarker_id_dict[biomarker_id_md5]
        biomarker_id_new = "xxx"
        bmkb_idx += 1
        cmb_list = json.loads(cmb_list_str)
        src_list = list(cmblist2src[cmb_list_str].keys())

        cmb_list_new = []
        for cmb in cmb_list:
            ent_id, d_id, vocab = cmb.split("|")
            cmb_list_new.append("%s|%s|%s" % (ent_id, d_id, vocab.lower()))
        cmb_list_str_new = json.dumps(cmb_list_new)
        biomarker_id_list = list(cmb2biomarkerid[cmb_list_str_new].keys()) if cmb_list_str_new in cmb2biomarkerid else []
        biomarker_id_list = sorted(biomarker_id_list)
        if DEBUG:
            print (biomarker_id_list,src_list, cmb_list_str)
        
        role_dict, evdn_dict = {}, {}
        comp_dict = {}
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
                        "name_space":specimen_ns, "url":xref_url
                    }
                if entity_id not in comp_dict:
                    rec_name, syn_obj_list = entity, []
                    if entity_type == "protein" and entity_id in prt_name_dict:
                        for name_obj in prt_name_dict[entity_id]:
                            if name_obj["type"] == "synonym":
                                syn_obj_list.append({"synonym":name_obj["name"]})

                    comp_dict[entity_id] = {
                        "assessed_biomarker_entity_id":entity_id,
                        "assessed_biomarker_entity":{ "recommended_name":rec_name, "synonyms": syn_obj_list},
                        "assessed_entity_type":entity_type,
                        "biomarker_orig":biomarker_orig,
                        "biomarker":biomarker
                    }
                if evdn_id != "":
                    if "evidence_dict" not in comp_dict[entity_id]:
                        comp_dict[entity_id]["evidence_dict"] = {}
                    comp_dict[entity_id]["evidence_dict"][evdn_id] = evdn_dict[evdn_id]
 
                if specimen_id != "":
                    if "specimen_dict" not in comp_dict[entity_id]:
                        comp_dict[entity_id]["specimen_dict"] = {}
                    comp_dict[entity_id]["specimen_dict"][specimen_id] = specimen_obj

                
        if biomarker_id_list == []:
            id_counter += 1
            biomarker_id_list = [biomarker_id_new]
        biomarker_id = biomarker_id_list[0]
        
        data_src_list = []
        for s in src_list:
            src, biomarker_idx = s.split("|")
            #data_src_list.append("source":src, "biomarker_idx":biomarker_idx})
            data_src_list.append(src)
         
        record_obj = {
            "biomarker_id":biomarker_id,
            "biomarker_canonical_id":biomarker_id.split("-")[0],
            "biomarker_id_md5":biomarker_id_md5,
            "biomarker_id_new":biomarker_id_new,
            "condition":{},
            "best_biomarker_role":[],
            "biomarker_component":[],
            "evidence_source":[],
            "citation_dict":{},
            "citation_evdn_dict":{},
            "crossref":[],
            "entity_normal_ranges":[],
            "source_list":data_src_list
        }
        final_id_list.append(";".join(biomarker_id_list))
        #--> best_biomarker_role
        for role in role_dict:
            record_obj["best_biomarker_role"].append({"role":role})

        #-->evidence_source and citation
        for evdn_id in evdn_dict:
            xref_key, xref_id = evdn_id.lower().split(":")[0], evdn_id.split(":")[1]
            #print (evdn_id, xref_key, xref_id)
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

        #-->condition
        disease_id = cmb_list[0].split("|")[1].replace(":",".").lower()
        if disease_id in disease_dict:
            record_obj["condition"] = disease_dict[disease_id]
        else:
            with open(log_file, "a") as FL:
                FL.write("ERROR|disease_file_not_found|%s|%s\n" % (disease_id,cmb_list_str))
            missed += 1
            continue

        #-->crossref
        for src in src_list:
            if src in crossref_dict:
                for pair in crossref_dict[src]:
                    xref_key, xref_id = pair.split("|")
                    #print (xref_key, xref_id, xref_key in url_dict)
                    if xref_key in url_dict:
                        xref_lbl, xref_url = url_dict[xref_key]["lbl"], url_dict[xref_key]["url"] % (xref_id)
                        o = {"id":xref_id, "url":xref_url, "database":xref_lbl, "categories":[]}
                        record_obj["crossref"].append(o)


        #-->biomarker_component
        for entity_id in comp_dict:
            comp_obj = comp_dict[entity_id]
            comp_obj["evidence_source"] = []
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
        
        record_obj_list.append(record_obj)
        if len(record_obj_list) == 100:
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

    if len(record_obj_list) > 0:
        batch_idx +=1
        total_created += len(record_obj_list)
        out_file = out_dir + "batch.%s.json" % (batch_idx)
        with open(out_file, "wb") as FW:
            FW.write(orjson.dumps(record_obj_list))
        ts = datetime.datetime.now()
        with open(log_file, "a") as FL:
            FL.write("%s created %s/%s records (%s missed)\n" % (ts, total_created, total, missed)) 

    if final_id_list != []:
        out_file = "logs/make-biomarker.idlist.json"
        with open(out_file, "w") as FW:
            FW.write("%s\n" % (json.dumps(final_id_list, indent=4)))




 
    return 




if __name__ == '__main__':
    main()
 
