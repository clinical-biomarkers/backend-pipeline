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


    crossref_dict = csvutil.load_entity_crossref_dict(release_dir)
    refid2hgncid, hgnc2upkb = csvutil.load_refid2hgncid()
    prt_name_dict, gene_name_dict, glycan_name_dict = csvutil.load_entity_names()
    upkb2geneid = csvutil.load_upkb2geneid()
     

    annotation_dict = csvutil.load_annotation_dict(release_dir)
   
    normal_ranges_dict = {}
    file_list = glob.glob(release_dir + "jsondb/normalrangesdb/*.json")
    for in_file in file_list:
        doc = json.load(open(in_file))
        ent_id = doc["entity_id"]
        normal_ranges_dict[ent_id] = doc

    #for ent_id in normal_ranges_dict:
    #    print (ent_id)
    #exit()


    legacy_ent_id = {}
    origid2entid = csvutil.load_origid2entid(rel)
    for orig_id in origid2entid:
        legacy_ent_id[origid2entid[orig_id]] = True

    # clean out_dir
    out_dir = release_dir + "jsondb/interm/entdb/"
    if os.path.isdir(out_dir):
        cmd = "rm -rf %s/*" % (out_dir)
        x = subprocess.getoutput(cmd)


    rsid2geneid = {}
    file_list = glob.glob("/data/shared/biomarkerdb/downloads/rsidmap/current/*.json")
    for in_file in file_list:
        doc_list = json.load(open(in_file))
        for doc in doc_list:
            entity_id = doc["entity_id"]
            for obj in doc["map"]:
                gene_id = obj["geneid"]
                if entity_id not in rsid2geneid:
                    rsid2geneid[entity_id] = {}
                rsid2geneid[entity_id][gene_id] = True

    tmp_map = {
        "dbSNP:rs12129037": "100874054",
        "dbSNP:rs71580314": "100874054",
        "dbSNP:rs367563576": "100874054",
        "dbSNP:rs11582423": "100874054",
        "dbSNP:rs42775": "121232377"
    }
    for entity_id in rsid2geneid:
        if entity_id in tmp_map:
            rsid2geneid[entity_id][tmp_map[entity_id]] = True 

    
     
    file_list = glob.glob(release_dir + "unreviewed/biomarkers_*.tsv")
    ref_dict_one, ref_dict_two, ref_dict_three, ref_dict_four = {}, {}, {}, {}
   
    entid2entity = {} 
    for in_file in file_list:
        file_name = in_file.split("/")[-1]
        source = in_file.split("/")[-1].replace("biomarkers_","").replace(".tsv","")
        with open(in_file, "r") as FR:
            f_list, lcount = [], 0
            for line in FR:
                lcount += 1
                row = line[0:-1].split("\t")
                if lcount == 1:
                    f_list = row
                else:
                    ent_id = row[f_list.index("assessed_biomarker_entity_id")]
                    ent_type = row[f_list.index("assessed_entity_type")]
                    ent = row[f_list.index("assessed_biomarker_entity")]
                    entid2entity[ent_id] = ent
                    cmb = "%s|%s" % (ent_type, ent_id)
                    c_vocab = row[f_list.index("biomarker_controlled_vocab")]
                    biomarker = row[f_list.index("biomarker")]
                    ref_id_list = []
                    ref_id_list = [ent_id] if ent_type == "gene" else ref_id_list
                    ref_id_list = [ent_id] if ent_type == "protein" else ref_id_list

                    if ent_type == "protein" and ent_id.find("HGNC:") != -1:
                        if ent_id in hgnc2upkb:
                            ref_id_list = list(hgnc2upkb[ent_id].keys())
 
                    et_list = ["metabolite","glycan","cell","amino acid","mRNA","other", "RNA", "miRNA","image"]
                    et_list += ["protein complex","lipoprotein", "chemical element", "peptide", "lipid", "DNA"]
                    ref_id_list = [ent_id] if ent_type in et_list else ref_id_list
                    if ent_type == "gene" and ent_id.find("dbSNP:") != -1:
                        c_vocab_id = c_vocab.split("/")[-1]
                        ref_id_list = [] if c_vocab_id.split(":")[1] == "" else [c_vocab_id]
                        if ref_id_list == [] and c_vocab.find("sequence variation in gene") != -1:
                            if ent_id in rsid2geneid:
                                for gene_id in rsid2geneid[ent_id]:
                                    ref_id_list.append("NCBI:"+str(gene_id))
                    flag_list = []
                    for ref_id in ref_id_list:
                        flag = False
                        flag = True if ref_id in prt_name_dict else flag
                        flag = True if ref_id in glycan_name_dict else flag
                        flag = True if ref_id in gene_name_dict else flag
                        if flag:
                            if ref_id not in ref_dict_one:
                                ref_dict_one[ref_id] = {}
                            ref_dict_one[ref_id][cmb] = True
                        else:
                            if ref_id not in ref_dict_two:
                                ref_dict_two[ref_id] = {}
                            ref_dict_two[ref_id][cmb] = True                    
                    if ref_id_list == []:
                        if ent_id.find("dbSNP:") != -1:
                            ref_id = "NCBI:CLASS4"
                            ref_dict_four[ref_id] = {cmb:True}
                        else:
                            ref_id = ent_id
                            ref_dict_three[ref_id] = {cmb:True}



    c_ref_dict = {}
    for ref_id in ref_dict_one:
        c_ref_dict[ref_id] = ref_dict_one[ref_id]
    for ref_id in ref_dict_two:
        if ref_id not in c_ref_dict:
            c_ref_dict[ref_id] = ref_dict_two[ref_id]
        else:
            for cmb in ref_dict_two[ref_id]:
                c_ref_dict[ref_id][cmb] = True
    for ref_id in ref_dict_three:
        if ref_id not in c_ref_dict:
            c_ref_dict[ref_id] = ref_dict_three[ref_id]
        else:
            for cmb in ref_dict_three[ref_id]:
                c_ref_dict[ref_id][cmb] = True    

    for ref_id in ref_dict_four:
        if ref_id not in c_ref_dict:
            c_ref_dict[ref_id] = ref_dict_four[ref_id]
        else:
            for cmb in ref_dict_four[ref_id]:
                c_ref_dict[ref_id][cmb] = True


    

    record_obj_dict = {}
    #these are with references and name info
    for ref_id in c_ref_dict:
        cls = 0
        cls = 4 if ref_id in ref_dict_four else cls
        cls = 3 if ref_id in ref_dict_three else cls
        cls = 2 if ref_id in ref_dict_two else cls
        cls = 1 if ref_id in ref_dict_one else cls

        record_obj = {
            "ref_id":ref_id, "entities":[], "class":cls 
        }
        for cmb in c_ref_dict[ref_id]:
            ent_type, ent_id = cmb.split("|")
            entity = entid2entity[ent_id] if ent_id in entid2entity else ""
            orig_id = ent_id 
            if ent_id in origid2entid:
                ent_id = origid2entid[ent_id]
            if ent_id.find("bGSL:") != -1:
                if ent_id not in origid2entid:
                    tmp_id = ""
                    zeros = "000000"
                    while True:
                        rand_int = random.randint(1, 999999)
                        padding = zeros[:6-len(str(rand_int))]
                        tmp_id = "BGSL:%s%s" % (padding, rand_int)
                        if tmp_id not in legacy_ent_id:
                            break
                    ent_id = tmp_id
            oo = {
                "entity_type":ent_type, "entity_id":ent_id, "orig_entity_id":orig_id,
                "entity_normal_ranges":[],"annotations":[], "crossref":[], "citation":[], "biomarkers":[]
            } 
            if ent_id in normal_ranges_dict:
                oo["entity_normal_ranges"] = normal_ranges_dict[ent_id]
            if ent_id in annotation_dict:
                oo["annotations"] =  annotation_dict[ent_id]
            if ent_id in crossref_dict:
                oo["crossref"] =  crossref_dict[ent_id]
            
            record_obj["entities"].append(oo)
            if ent_type == "glycan":
                record_obj["ref_id"] = ent_id

        ent_name_dict = prt_name_dict if ent_type == "protein" else {}
        ent_name_dict = gene_name_dict if ent_type == "gene" else ent_name_dict
        ent_name_dict = glycan_name_dict if ent_type == "glycan" else ent_name_dict
        record_obj["recommended_name"] = entity
        record_obj["synonyms"] = []
        if ref_id in ent_name_dict:
            for name_obj in ent_name_dict[ref_id]:
                if name_obj["type"] == "synonym":
                    record_obj["synonyms"].append({"synonym":name_obj["name"]})
                elif name_obj["type"] == "recommended":
                    record_obj["recommended_name"] = name_obj["name"]


        if ref_id in refid2hgncid:
            for hgnc_id in refid2hgncid[ref_id]:
                new_record_obj = {"hgnc_id":"HGNC:" + hgnc_id}
                for k in record_obj:
                    new_record_obj[k] = record_obj[k] 
                record_obj_dict[ref_id] = new_record_obj
        else:
            record_obj["hgnc_id"] = "HGNC:000000"
            record_obj_dict[ref_id] = record_obj



    #here we merge UPKB records to corresponding NCBI records
    #this way we have common reference record for both gene and protein
    ref_id_list = list(record_obj_dict.keys())
    rcount = 0
    for src_ref_id in ref_id_list:
        if src_ref_id.find("UPKB:") != -1:
            if src_ref_id in upkb2geneid:
                src_record = record_obj_dict[src_ref_id]
                dst_count = 0
                for dst_ref_id in upkb2geneid[src_ref_id]:
                    if dst_ref_id in record_obj_dict:
                        dst_count += 1
                        dst_record = record_obj_dict[dst_ref_id]
                        for obj in src_record["entities"]:
                            if obj["entity_id"] == src_ref_id:
                                dst_record["entities"].append(obj)
                if dst_count > 0:
                    #now we remove src_record
                    record_obj_dict.pop(src_ref_id)
                    rcount += 1


    

    record_obj_list = []
    batch_idx = 0
    for ref_id in record_obj_dict:
        doc = record_obj_dict[ref_id]
        record_obj_list.append(doc)
        if len(record_obj_list) == 100:
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
 
