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
    parser.add_option("-p","--prev",action="store",dest="prev",help="")
    (options,args) = parser.parse_args()
    for key in ([options.rel, options.prev]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    rel = options.rel
    prev_rel = options.prev

    global release_dir
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)


    cmb2biomarkerid = csvutil.load_cmb2biomarkerid(release_dir)
    cmblist2src, grp2cmblist = csvutil.load_cmblist2src(release_dir)
    canon2disease_dict = csvutil.load_canon2disease_dict(grp2cmblist, release_dir)
    canon_id_md5_list = sorted(list(canon2disease_dict.keys()))
    canon_id_dict = csvutil.load_canon_id_dict(rel,canon_id_md5_list)
  
    
    prev_rel_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (prev_rel)
    file_list = glob.glob(prev_rel_dir + "jsondb/idtrackdb/*.json")
    hist_dict = {}
    for in_file in file_list:
        doc_list = json.load(open(in_file))
        for doc in doc_list:
            biomarker_id = doc["record_id"] 
            hist_dict[biomarker_id] = doc
 

    replacement_dict = {}
    track_status = {}
    record_obj_list = []
    out_dir = release_dir + "jsondb/idtrackdb/"
    bmkb_idx = 0
    batch_idx = 0
    for canon_id_md5 in canon_id_md5_list:
        canon_id_new = canon_id_dict[canon_id_md5]
        idx = 0
        for d_id in canon2disease_dict[canon_id_md5]:
            idx += 1
            bmkb_idx += 1
            s = canon_id_md5 + d_id
            biomarker_id_md5 = hashlib.md5(s.encode('utf-8')).hexdigest()         
            biomarker_id_new = "%s-%s" % (canon_id_new, idx)
            cmb_list = canon2disease_dict[canon_id_md5][d_id]["cmblist"]
            grp = canon2disease_dict[canon_id_md5][d_id]["grp"]
            cmb_list_new = []
            for cmb in cmb_list:
                ent_id, d_id, vocab = cmb.split("|")
                cmb_list_new.append("%s|%s|%s" % (ent_id, d_id, vocab.lower()))
            cmb_list_str = json.dumps(cmb_list)
            cmb_list_str_new = json.dumps(cmb_list_new)       
            
            src_list = list(cmblist2src[cmb_list_str].keys())
            biomarker_id_list = []
            if cmb_list_str_new in cmb2biomarkerid:
                biomarker_id_list = sorted(list(cmb2biomarkerid[cmb_list_str_new].keys()))
            if biomarker_id_list == []:
                continue
            biomarker_id = biomarker_id_list[0]
            record_obj = {
                "record_id":biomarker_id,
                "recordtype":"biomarker",
                "grp":grp,
                "cmb_list":cmb_list,
                "canon_id_md5":canon_id_md5,
                "biomarker_id_md5":biomarker_id_md5,
                "canon_id_new":canon_id_new,
                "biomarker_id_new":biomarker_id_new,
                "biomarker_id_list":biomarker_id_list,
                "source_list":src_list,
                "history":[]
            }
            track_status[biomarker_id] = True
            if biomarker_id in hist_dict:
                record_obj["history"] = hist_dict[biomarker_id]["history"]
            if len(biomarker_id_list) > 1:
                id_list = biomarker_id_list[1:]
                desc = "Inherits %s as of release %s" % (";".join(id_list), rel)
                o = {"type":"inherits", "inherited_id_list":id_list, "description": desc}
                record_obj["history"].append(o)
                for tmp_id in id_list:
                    if tmp_id not in replacement_dict:
                        replacement_dict[tmp_id] = {}
                    replacement_dict[tmp_id][biomarker_id] = True
                     
            record_obj_list.append(record_obj)
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
    for biomarker_id in hist_dict:
        if biomarker_id not in track_status:
            if biomarker_id in replacement_dict:
                id_list = list(replacement_dict[biomarker_id].keys())
                desc = "Replaced by %s as of release %s" % (";".join(id_list), rel)
                o = {"type":"replaced", "replacement_id_list":id_list, "description": desc}
                hist_dict[biomarker_id]["history"].append(o)
            else:
                o = {"type": "discontinued", "description": "Discontinued in release %s" % (rel)}
                hist_dict[biomarker_id]["history"].append(o)
            record_obj_list.append(hist_dict[biomarker_id])

    if len(record_obj_list) > 0:
        batch_idx += 1
        out_file = out_dir + "batch.%s.json" % (batch_idx)
        with open(out_file, "wb") as FW:
            FW.write(orjson.dumps(record_obj_list))




    return 




if __name__ == '__main__':
    main()
 
