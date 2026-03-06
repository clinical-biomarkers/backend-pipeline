import os,sys
import json
import glob
import datetime
import csvutil
from optparse import OptionParser
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

    rel = options.rel

    global release_dir
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)

    url_dict = csvutil.load_url_dict(release_dir + "misc/xref_info.csv")

    seen_disease_id = {}
    file_list = glob.glob(release_dir + "unreviewed/biomarkers_*.tsv")
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
                    disease_id = row[f_list.index("condition_id")]
                    if disease_id != "":
                        seen_disease_id[disease_id] = True


    #"xref_id","xref_key","name_type","name","description"
    in_file = "/data/shared/biomarkerdb/downloads/glygen/current/protein_disease_names.csv"
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

    disease_id_list = list(recname_dict.keys())
    
    for disease_id in seen_disease_id:
        if disease_id not in disease_id_list:
            recname_dict[disease_id] = {"name":"", "description":""}
            d = disease_id.replace(":","_")
            cmd = "grep %s /data/shared/biomarkerdb/downloads/do/current/doid.nt" % (d)
            line_list = subprocess.getoutput(cmd).split("\n")
            for line in line_list:
                prd = line.split(" ")[1]
                if prd == "<http://www.w3.org/2000/01/rdf-schema#label>":
                    val = " ".join(line.split(" ")[2:])
                    val = val.replace(".\"@en .", "").replace("\"","")
                    recname_dict[disease_id]["name"] = val
                if prd == "<http://purl.obolibrary.org/obo/IAO_0000115>":
                    val = " ".join(line.split(" ")[2:])
                    val = val.replace(".\"@en .", "").replace("\"","")
                    recname_dict[disease_id]["description"] = val

    disease_id_list = ["DOID:0051065"]
        
    doc_list = []
    batch_idx = 0
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

        doc_list.append(record_obj)
        if len(doc_list) == 100:
            batch_idx += 1
            out_file = release_dir + "jsondb/diseasedb/batch.%s.json" % (batch_idx)
            with open(out_file, "w") as FW:
                FW.write("%s\n" % (json.dumps(doc_list, indent=4))) 
            doc_list = []


    if len(doc_list) > 0:
        batch_idx += 1
        out_file = release_dir + "jsondb/diseasedb/batch.%s.json" % (batch_idx)
        with open(out_file, "w") as FW:
            FW.write("%s\n" % (json.dumps(doc_list, indent=4)))          

    

 
    return 




if __name__ == '__main__':
    main()
 
