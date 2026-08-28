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


def main():

    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-r","--rel",action="store",dest="rel",help="")
    (options,args) = parser.parse_args()
    for key in ([options.rel]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    rel = options.rel

    global release_dir
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)

    # clean out_dir
    out_dir = "%s/jsondb/idgendb/*" % (release_dir)
    if os.path.isdir(out_dir):
        cmd = "rm -rf %s/*" % (out_dir)
        x = subprocess.getoutput(cmd)

    # this gets old IDs from datasets with non-empty values in column=legacy_biomarker_id
    legacy_biomarkerid_dict, orig_dict = csvutil.load_legacy_biomarkerid_dict(release_dir)




    term_dict = csvutil.load_biomarker_orig(rel)

    # these are only for current release 
    cmblist2src, grp2cmblist = csvutil.load_cmblist2src(release_dir)
    canon2conagent_dict = csvutil.load_canon2conagent_dict(grp2cmblist, release_dir)
    canon_id_md5_list = sorted(list(canon2conagent_dict.keys()))
   
    # this loads canonmd52id dictionary -- uses idgendb from old releases 
    canon_id_dict, canonid2maxindex, cmblist2biomarkerid = csvutil.load_canon_id_dict(rel,canon_id_md5_list)
 
    
    disease_dict = {}
    file_list = glob.glob(release_dir + "jsondb/diseasedb/*.json")
    for in_file in file_list:
        doc_list = json.load(open(in_file))
        for doc in doc_list:
            disease_id = doc["id"].lower().replace(":",".")
            disease_dict[disease_id] = doc


    record_obj_list = []
    out_dir = release_dir + "jsondb/idgendb/"
    batch_idx = 0
   

 
    for canon_id_md5 in canon_id_md5_list:
        canon_id = canon_id_dict[canon_id_md5]
        bmkb_idx = canonid2maxindex[canon_id] if canon_id in canonid2maxindex else 0
        for d_id in canon2conagent_dict[canon_id_md5]:
            bmkb_idx += 1
            s = canon_id_md5 + d_id
            biomarker_id_md5 = hashlib.md5(s.encode('utf-8')).hexdigest()         
            biomarker_id_new = "%s-%s" % (canon_id, bmkb_idx)
            cmb_list = canon2conagent_dict[canon_id_md5][d_id]["cmblist"]
            grp = canon2conagent_dict[canon_id_md5][d_id]["grp"]
            cmb_list_new = []
            missing_disease_flag = False
            for cmb in cmb_list:
                ent_id, d_id, ctype, vocab = cmb.split("|")
                cmb_list_new.append("%s|%s|%s|%s" % (ent_id, d_id, ctype, vocab.lower()))
                if ctype == "condition" and d_id != "":
                    if d_id.lower().replace(":",".") not in disease_dict:
                        missing_disease_flag = True
            cmb_list_str = json.dumps(cmb_list)
            cmb_list_str_new = json.dumps(cmb_list_new)       
            src_list = list(cmblist2src[cmb_list_str].keys())
            biomarker_id_list = []
            if cmb_list_str_new in legacy_biomarkerid_dict:
                biomarker_id_list = sorted(list(legacy_biomarkerid_dict[cmb_list_str_new].keys()))
           
            if biomarker_id_list == [] and cmb_list_str_new in cmblist2biomarkerid:
                biomarker_id_list = [cmblist2biomarkerid[cmb_list_str_new]]

            if biomarker_id_list == []:
                biomarker_id_list = [biomarker_id_new]
            biomarker_id = biomarker_id_list[0]

            #print (biomarker_id_list, biomarker_id_new)

            #print (biomarker_id_md5, biomarker_id, cmb_list, missing_disease_flag)
            if missing_disease_flag:
                continue

            record_obj = {
                "canon_id":canon_id,
                "canon_id_md5":canon_id_md5,
                "biomarker_id":biomarker_id,
                "biomarker_id_md5":biomarker_id_md5,
                "recordtype":"biomarker",
                "grp":grp,
                "cmb_list":cmb_list,
                "biomarker_id_list":biomarker_id_list,
                "source_list":src_list
            }
            record_obj["biomarker"] = term_dict[biomarker_id] if biomarker_id in term_dict else ""
            record_obj_list.append(record_obj)
            
            #if biomarker_id == "WY3480-1":
            #    print (json.dumps(record_obj, indent=4))
            #    exit()

            if len(record_obj_list) == 1000:
                batch_idx += 1
                out_file = out_dir + "batch.%s.json" % (batch_idx)
                with open(out_file, "wb") as FW:
                    FW.write(orjson.dumps(record_obj_list))
                record_obj_list = []

    if len(record_obj_list) > 0:
        batch_idx += 1
        out_file = out_dir + "batch.%s.json" % (batch_idx)
        with open(out_file, "wb") as FW:
            FW.write(orjson.dumps(record_obj_list))

        
    record_obj_list = []
    if len(record_obj_list) > 0:
        batch_idx += 1
        out_file = out_dir + "batch.%s.json" % (batch_idx)
        with open(out_file, "wb") as FW:
            FW.write(orjson.dumps(record_obj_list))


    return 




if __name__ == '__main__':
    main()
 
