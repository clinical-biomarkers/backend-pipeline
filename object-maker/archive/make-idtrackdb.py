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
    parser.add_option("-r","--r",action="store",dest="rel",help="")
    (options,args) = parser.parse_args()
    for key in ([ options.rel]):
        if not (key):
            parser.print_help()
            sys.exit(0)



    canon_id_dict = {}
    rel = options.rel
    d_list = glob.glob("/data/shared/biomarkerdb/releases/data/v-*/jsondb/idtrackdb")
    for d in d_list:
        r = d.split("/")[-3].split("-")[1]
        if r not in [rel, "y.y.y"]:
            file_list = glob.glob(d + "/*.json")
            for in_file in file_list:
                doc = json.load(open(in_file))
                canon_id_dict[doc["canon_id_md5"]] = doc["canon_id_new"]

    canon_id_counter = len(canon_id_dict.keys())

    cmb2biomarkerid = csvutil.load_cmb2biomarkerid()
    cmblist2src, grp2cmblist = csvutil.load_cmblist2src()

    seen_grp = {}
    row_dict = {}
    file_list = glob.glob("reviewed/biomarkers_*.tsv")
    for in_file in file_list:
        source = in_file.split("/")[-1].replace("biomarkers_","").replace(".tsv","")
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
                    seen_grp[grp] = True


    
    canon2disease_dict = {}    
    grp_list = sorted(seen_grp.keys())
    for grp in grp_list:
        cmb_list = grp2cmblist[grp]
        cmb_list_canon = []
        seen_d_id = {}
        for cmb in cmb_list:
            ent_id, d_id, vocab = cmb.split("|")
            seen_d_id[d_id] = True
            cmb_list_canon.append("%s|%s" % (ent_id, vocab.lower()))
        cmb_list_canon = sorted(set(cmb_list_canon))
        cmb_list_str_canon = json.dumps(cmb_list_canon)
        canon_id_md5 = hashlib.md5(cmb_list_str_canon.encode('utf-8')).hexdigest()
        if canon_id_md5 not in canon2disease_dict:
            canon2disease_dict[canon_id_md5] = {}
        for d_id in seen_d_id:
            canon2disease_dict[canon_id_md5][d_id] = {"cmblist":cmb_list, "grp":grp}


    out_dir = "jsondb/idtrackdb/"

    bmkb_idx = 0
    for canon_id_md5 in canon2disease_dict:
        canon_id_new, biomarker_id_new = "", ""
        if canon_id_md5 in canon_id_dict:
            canon_id_new = canon_id_dict[canon_id_md5]
        else:
            canon_id_counter += 1
            canon_id_new = csvutil.generate_new_id(canon_id_counter)

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
            record_obj = {
                "grp":grp,
                "cmb_list":cmb_list,
                "canon_id_md5":canon_id_md5,
                "biomarker_id_md5":biomarker_id_md5,
                "canon_id_new":canon_id_new,
                "biomarker_id_new":biomarker_id_new,
                "biomarker_id_list":biomarker_id_list,
                "source_list":src_list
            }
            out_file = out_dir + "%s.json" % (biomarker_id_new)
            with open(out_file, "wb") as FW:
                FW.write(orjson.dumps(record_obj))
                #FW.write(json.dumps(record_obj, indent=4))

    return 




if __name__ == '__main__':
    main()
 
