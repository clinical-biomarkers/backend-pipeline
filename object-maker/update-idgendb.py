import os,sys
import json
import glob
import requests
from optparse import OptionParser
import orjson
import hashlib
import csvutil

def main():


    legacy_release_list = ["3.1.1","3.2.1","3.2.2","3.3.1","3.4.1","3.4.2"]

    



    for rel in legacy_release_list:

        term_dict = csvutil.load_biomarker_orig(rel)


        

 
        release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)
        out_dir = release_dir + "jsondb/idgendb/"
        file_list = glob.glob("/data/shared/biomarkerdb/releases/data/v-%s/jsondb/idgendb_backup/*.json" % (rel))
        for in_file in file_list:
            doc_list = json.load(open(in_file))
            for doc in doc_list:
                biomarker_id = doc["record_id"]
                biomarker_id_md5 = doc["biomarker_id_md5"]
                canon_id_md5 = doc["canon_id_md5"]
                cmb_list = doc["cmb_list"]
                cmb_list_new = []
                
                for cmb in cmb_list:
                    cmb_parts = cmb.split("|")
                    d_id, ctype = "", ""
                    if cmb_parts[1].split(":")[0] in ["DOID","MONDO","OMIM"]:
                        d_id, ctype = cmb_parts[1],"condition"
                    if cmb_parts[2].split(":")[0] in ["meSHID"]:
                        d_id,ctype =cmb_parts[2], "condition" 
                    if ctype != "condition" and  cmb_parts[0].split(":")[0] in ["PCCID", "CHEBI"]:
                        d_id, ctype = cmb_parts[2], "exposure_agent"
                    if ctype == "" and cmb_parts[2].split(":")[0] in ["PCCID","NCIt"]:
                        d_id, ctype = cmb_parts[2], "exposure_agent"
            
                    cmb_parts = [cmb_parts[0], d_id, ctype, cmb_parts[-1]]

                    c_vocab = cmb_parts[-1]
                    change, aspect, mod = "", "", ""
                    flag = False
                    if c_vocab.find("presence of") != -1 and c_vocab.find("sequence variation") != -1:
                        change, mod = "presence of", "sequence variation"
                        flag = True
                    elif c_vocab.find("increased level of") != -1:
                        change, aspect = "increased", "level"
                        flag = True
                    elif c_vocab.find("decreased level of") != -1:
                        change, aspect = "decreased", "level" 
                        flag = True
                    elif c_vocab.find("increased expression of") != -1:
                        change, aspect = "increased", "expression"
                        flag = True
                    elif c_vocab.find("decreased expression of") != -1:
                        change, aspect = "decreased", "expression"
                        flag = True
                    elif c_vocab.find("differential expression of") != -1:
                        change, aspect = "differential", "expression"
                        flag = True
                    elif c_vocab.find("differential level of") != -1:
                        change, aspect = "differential", "level"
                        flag = True
                    elif c_vocab.find("increased methylation") != -1:
                        change, mod = "increased", "methylation"
                        flag = True 
                    elif c_vocab.find("decreased activity of") != -1:
                        change, aspect = "decreased", "activity"
                        flag = True
                    elif c_vocab.find("presence of expression of gene") != -1:
                        change, aspect = "presence of", "expression"
                        flag = True
                    elif c_vocab.find("presence of methylation of gene") != -1:
                        change, mod = "presence of", "methylation"
                        flag = True
                    elif c_vocab.find("presence of activity of protein") != -1:
                        change, aspect = "presence of", "activity"
                        flag = True
                    elif c_vocab.find("presence of level of metabolite") != -1:
                        change, aspect = "presence of", "level"
                        flag = True
            
                        
                    new_c_vocab = "xxx"
                    if flag:
                        new_c_vocab = "change_type:%s" % (change)
                        new_c_vocab += ",aspect_type:%s" % (aspect) if aspect != "" else ""
                        new_c_vocab += ",mod_type:%s" % (mod) if mod != "" else ""
                    elif c_vocab.find("[biomarker_term_in_review]") != -1:
                        new_c_vocab = c_vocab
                    cmb_parts[-1] = new_c_vocab

                    if c_vocab.find("presence of bmkb_i::") != -1 or c_vocab.find("presence of bmkb_ii::") != -1:
                        mut_id = c_vocab.split(" ")[2].replace("bmkb_ii::","bmkb:").replace("bmkb_i::","bmkb:")
                        cmb_parts[0] += "@%s" % (mut_id)
                        #print (cmb_parts[0])
                    cmb_list_new.append("|".join(cmb_parts))
               
                    
 
                doc["cmb_list"] = cmb_list_new
                doc["biomarker_id"] = doc["record_id"]
                doc.pop("record_id")
                doc["biomarker"] = term_dict[doc["biomarker_id"]] if doc["biomarker_id"] in term_dict else ""


 
                cmb_list_canon = []
                for cmb in doc["cmb_list"]:
                    ent_id, d_id, ctype, vocab = cmb.split("|")
                    cmb_list_canon.append("%s|%s" % (ent_id, vocab.lower()))
                cmb_list_canon = sorted(set(cmb_list_canon))
                cmb_list_str_canon = json.dumps(cmb_list_canon)
                canon_id_md5 = hashlib.md5(cmb_list_str_canon.encode('utf-8')).hexdigest()
                doc["canon_id_md5"] = canon_id_md5

                d_id = doc["cmb_list"][0].split("|")[1]
                s = canon_id_md5 + d_id
                biomarker_id_md5 = hashlib.md5(s.encode('utf-8')).hexdigest()
                doc["biomarker_id_md5"] = biomarker_id_md5



            out_file = in_file.replace("idgendb_backup","idgendb")
            with open(out_file, "wb") as FW:
                FW.write(orjson.dumps(doc_list))
            #print(rel, out_file) 
            
 
    return


if __name__ == '__main__':
    main()



