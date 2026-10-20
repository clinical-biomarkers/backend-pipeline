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
import random

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
    out_dir = release_dir + "jsondb/entdb/"
    if os.path.isdir(out_dir):
        cmd = "rm -rf %s/*" % (out_dir)
        x = subprocess.getoutput(cmd)

    k_list_one = ["biomarker_id", "condition","best_biomarker_role", "source_list"]
    k_list_two = ["biomarker_orig", "biomarker", "evidence_source", "specimen"]
    entid2biomarker = {}
    entid2citation = {}
    file_list = glob.glob(release_dir + "jsondb/biomarkerdb/*.json")
    for in_file in file_list:
        doc_list = json.load(open(in_file))
        for doc in doc_list:
            oo = {}
            for k in k_list_one:
                oo[k] = doc[k]
            biomarker_id = doc["biomarker_id"]
            seen_cite = {}
            for obj in doc["citation"]:
                for o in obj["reference"]:
                    cmb = "%s|%s" % (o["type"], o["id"])
                    seen_cite[cmb] = obj

            for obj in doc["biomarker_component"]:
                ent_id = obj["assessed_biomarker_entity_id"]
                if ent_id not in entid2biomarker:
                    entid2biomarker[ent_id] = {}
                for k in k_list_two:
                    oo[k] = obj[k]
                entid2biomarker[ent_id][biomarker_id] = oo
                for o in obj["evidence_source"]:
                    if o["database"] in ["PubMed","DOI"]:
                        cmb = "%s|%s" % (o["database"], o["id"])
                        if cmb in seen_cite:
                            if ent_id not in entid2citation:
                                entid2citation[ent_id] = {}
                            entid2citation[ent_id][cmb] = seen_cite[cmb]  

 
    file_list = sorted(glob.glob(release_dir + "jsondb/interm/entdb/*.json")) 
    for in_file in file_list:
        doc_list = json.load(open(in_file))
        for doc in doc_list:
            ref_id = doc["ref_id"]
            for obj in doc["entities"]:
                ent_id = obj["entity_id"]
                if ent_id in entid2biomarker:
                    for biomarker_id in entid2biomarker[ent_id]:
                        obj["biomarkers"].append(entid2biomarker[ent_id][biomarker_id])
                if ent_id in entid2citation:
                    for cmb in entid2citation[ent_id]:
                        obj["citation"].append(entid2citation[ent_id][cmb])
            out_str = json.dumps(doc, indent=4)
            if len(out_str) > 16000000:
                out_dir_jumbo = release_dir + "jsondb/jumbodb/entdb/"
                out_file = out_dir_jumbo + "%s.json" % (ref_id)
                if os.path.isdir(out_dir_jumbo) == False:
                    cmd = "mkdir -p " + out_dir_jumbo
                    x = subprocess.getoutput(cmd)
                with open(out_file, "w") as FW:
                    FW.write("%s\n" % (json.dumps(doc, indent=4)))
                doc["entities"] = []
            out_file = "tmp/%s.json" % (ref_id)
            with open(out_file, "w") as FW:
                FW.write(json.dumps(doc))

        file_name = in_file.split("/")[-1] 
        out_file = out_dir + file_name
        with open(out_file, "wb") as FW:
            FW.write(orjson.dumps(doc_list))

    return 




if __name__ == '__main__':
    main()
 
