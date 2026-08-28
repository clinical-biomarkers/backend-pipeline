import os,sys
import json
import glob
import requests
from optparse import OptionParser
import orjson
import subprocess

def main():

    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-r","--rel",action="store",dest="rel",help="")
    (options,args) = parser.parse_args()
    for key in ([options.rel]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    current_rel = options.rel


    global release_dir
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (current_rel)
    out_dir = release_dir + "jsondb/idtrackdb/"

    # clean out_dir
    if os.path.isdir(out_dir):
        cmd = "rm -rf %s/*" % (out_dir)
        x = subprocess.getoutput(cmd)
 


    legacy_release_list = ["3.1.1","3.2.1","3.2.2","3.3.1","3.4.1","3.4.2"]

    url = "https://api.biomarkerkb.org//misc/verlist/"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    tmp_list = response.json()
    release_list = legacy_release_list + sorted(tmp_list) + [current_rel]
    release_list = sorted(list(set(release_list)))

    

    live_dict = {}
    src_dict = {}    
    hist_dict = {}
    for rel in release_list:
        file_list = glob.glob("/data/shared/biomarkerdb/releases/data/v-%s/jsondb/idgendb/*.json" % (rel))
        for in_file in file_list:
            doc_list = json.load(open(in_file))
            for doc in doc_list:
                biomarker_id_md5 = doc["biomarker_id_md5"]
                canon_id_md5 = doc["canon_id_md5"]
                cmb_list = doc["cmb_list"]
                if biomarker_id_md5 not in hist_dict:
                    hist_dict[biomarker_id_md5] = {"rel":{}, "id_list":[], "cmb_list":doc["cmb_list"], "canon_id_md5":doc["canon_id_md5"]}
                    src_dict[biomarker_id_md5] = []
                hist_dict[biomarker_id_md5]["rel"][rel] = True
                hist_dict[biomarker_id_md5]["id_list"] += doc["biomarker_id_list"]
                src_dict[biomarker_id_md5] += doc["source_list"]
                if rel == current_rel:
                    live_dict[biomarker_id_md5] = doc["biomarker_id_list"][0]

    debug_list = []
    record_dict = {}
    grp_dict = {} 
    for biomarker_id_md5 in hist_dict:
        doc = hist_dict[biomarker_id_md5]
        rel_list = sorted(list(doc["rel"].keys()))
        id_list = list(set(doc["id_list"]))
        src_list = sorted(list(set(src_dict[biomarker_id_md5])))
        msg = "%s|%s|%s" % (len(rel_list), rel_list, src_list)
        tmp_record_obj = {
            "biomarker_id_md5":biomarker_id_md5,
            "canon_id_md5":doc["canon_id_md5"],
            "cmb_list":doc["cmb_list"],
            "source_list":src_list, 
            "biomarker_id_list":id_list
        }
        live_id = live_dict[biomarker_id_md5] if biomarker_id_md5 in live_dict else ""
        if current_rel in rel_list and live_id != "":
            if len(rel_list) == len(release_list):
                for bmkb_id in id_list:
                    grp, text = "group_1", "Introduced in release %s" % (rel_list[0])
                    grp_dict[bmkb_id] = {"grp":grp, "text":text}
                    record_dict[bmkb_id] = tmp_record_obj.copy()
                    if bmkb_id != live_id:
                        grp, text = "group_2", "Introduced in release %s, replaced by %s" % (rel_list[0], live_id)
                        grp_dict[bmkb_id] = {"grp":grp, "text":text}
                        record_dict[bmkb_id]["replacement_id"] = live_id
            elif len(rel_list) == 1:
                for bmkb_id in id_list:
                    grp, text = "group_3", "Introduced in release %s" % (rel_list[0])
                    grp_dict[bmkb_id] = {"grp":grp, "text":text}
                    record_dict[bmkb_id] = tmp_record_obj.copy()
                    if bmkb_id != live_id:
                        grp, text = "group_4", "Introduced in release %s, replaced by %s" % (rel_list[0], live_id)
                        grp_dict[bmkb_id] = {"grp":grp, "text":text}
                        record_dict[bmkb_id]["replacement_id"] = live_id
            else:
                for bmkb_id in id_list:
                    grp, text = "group_5", "Introduced in release %s" % (rel_list[0])
                    grp_dict[bmkb_id] = {"grp":grp, "text":text}
                    record_dict[bmkb_id] = tmp_record_obj.copy()
                    if bmkb_id != live_id:
                        grp, text = "group_6", "Introduced in release %s, replaced by %s" % (rel_list[0], live_id)
                        grp_dict[bmkb_id] = {"grp":grp, "text":text}
                        record_dict[bmkb_id]["replacement_id"] = live_id                
        else:
            last_rel = rel_list[-1]
            xrel = release_list[release_list.index(last_rel) + 1]
            for bmkb_id in id_list:
                grp, text = "group_7", "Introduced in release %s, discontinued in release %s" % (rel_list[0], xrel)
                grp_dict[bmkb_id] = {"grp":grp, "text":text}
                record_dict[bmkb_id] = tmp_record_obj.copy()

    record_obj_list = []    
    batch_idx = 0 
    for bmkb_id in grp_dict:
        record_obj = record_dict[bmkb_id]
        record_obj["biomarker_id"] = bmkb_id
        record_obj["history"] = grp_dict[bmkb_id]
        #if batch_idx == 132 and len(record_obj_list) in [415, 416]:
        #    print (bmkb_id)
        #    print (json.dumps(record_obj, indent=4))
            
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

   

 
    return


if __name__ == '__main__':
    main()



