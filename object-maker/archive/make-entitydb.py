import os,sys
import json
import glob
import datetime
import csvutil
from optparse import OptionParser



def main():


    prt_name_dict, gene_name_dict = csvutil.load_entity_names()
    for enetity_id in gene_name_dict:
        for name_obj in gene_name_dict[enetity_id]:
            print (enetity_id, name_obj)
        
    exit()
 

    file_list = glob.glob("reviewed/biomarkers_*.csv")
    for in_file in file_list:
        source = in_file.split("/")[-1].replace("biomarkers_","").replace(".csv","")
        with open(in_file, "r") as FR:
            f_list, lcount = [], 0
            for line in FR:
                lcount += 1
                row = line[1:-2].strip().split("\",\"")
                if lcount == 1:
                    f_list = row
                else:
                    entity_id = row[f_list.index("assessed_biomarker_entity_id")]
                    entity_id = row[f_list.index("assessed_entity_type")]
                    
    exit()


    url_dict = csvutil.load_url_dict("misc/xref_info.csv")
    

    seen_disease_id = {}
    file_list = glob.glob("reviewed/biomarkers_*.csv")
    for in_file in file_list:
        source = in_file.split("/")[-1].replace("biomarkers_","").replace(".csv","")
        with open(in_file, "r") as FR:
            f_list, lcount = [], 0
            for line in FR:
                lcount += 1
                row = line[1:-2].strip().split("\",\"")
                if lcount == 1:
                    f_list = row
                else:
                    disease_id = row[f_list.index("condition_id")]
                    if disease_id != "":
                        seen_disease_id[disease_id] = True


    #"xref_id","xref_key","name_type","name","description"
    in_file = "downloads/glygen/current/protein_disease_names.csv"
    recname_dict = {}
    syn_dict = {}
    with open(in_file, "r") as FR:
        f_list, lcount = [], 0
        for line in FR:
            lcount += 1
            row = line[1:-2].strip().split("\",\"")
            if lcount == 1:
                f_list = row
            else:
                xref_id = row[f_list.index("xref_id")]
                xref_key = row[f_list.index("xref_key")]
                xref_key = "DOID" if xref_key.lower() == "do" else xref_key
                name = row[f_list.index("name")]
                name_type = row[f_list.index("name_type")]
                description = row[f_list.index("description")]
                disease_id = "%s:%s" % (xref_key.upper(), xref_id)
                if disease_id in seen_disease_id:
                    if name_type == "recommended_name":
                        recname_dict[disease_id] = {"name":name, "description":description}
                    elif name_type == "synonym":
                        if disease_id not in syn_dict:
                            syn_dict[disease_id] = {}
                        syn_dict[disease_id][name] = {"name":name, "description":description}


    #disease_id_list = list(recname_dict.keys())
    disease_id_list = ["DOID:0080600", "MONDO:0004967", "OMIM:251000"]
    for disease_id in disease_id_list:
        xref_key, xref_id = disease_id.lower().split(":")
        xref_url, xref_lbl = "", ""
        if xref_key in url_dict:
            xref_url, xref_lbl = url_dict[xref_key]["url"] % (xref_id), url_dict[xref_key]["lbl"]
                
        record_obj = {
            "id": disease_id,
            "recommended_name": {
                "id":disease_id,
                "name": recname_dict[disease_id]["name"],
                "description": recname_dict[disease_id]["description"],
                "resource": xref_lbl,
                "url": xref_url
            },
            "synonyms": []
        }
        if disease_id in syn_dict:
            for name in syn_dict[disease_id]:
                syn_name = syn_dict[disease_id][name]["name"]
                syn_description = syn_dict[disease_id][name]["description"]
                o = {"id":disease_id, "name":syn_name, "resource":xref_lbl, "url":xref_url}
                record_obj["synonyms"].append(o)

        file_name = disease_id.replace(":",".").lower()
        out_file = "jsondb/diseasedb/%s.json" % (file_name)
        with open(out_file, "w") as FW:
            FW.write("%s\n" % (json.dumps(record_obj, indent=4))) 

 
    return 




if __name__ == '__main__':
    main()
 
