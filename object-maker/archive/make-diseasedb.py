import os,sys
import json
import glob
import datetime
import csvutil
from optparse import OptionParser



def main():



    in_file = "downloads/do/current/doid.nt"
    recname_dict = {}
    desc_dict = {}
    syn_dict = {}
    with open(in_file, "r") as FR:
        for line in FR:
            parts = line.strip().split(" ")
            if parts[1] == "<http://www.w3.org/2000/01/rdf-schema#label>":
                do_id = parts[0].split("/")[-1].replace(">","")
                val = " ".join(parts[2:-1])[1:-1].replace("@e", "").replace("\"","")
                val = val[:-1] if val[-1] == "." else val
                if do_id[0:5] == "DOID_":
                    recname_dict[do_id] = val
            if parts[1] == "<http://purl.obolibrary.org/obo/IAO_0000115>":
                do_id = parts[0].split("/")[-1].replace(">","")
                val = " ".join(parts[2:-1])[1:-1].replace("@e", "").replace("\"","")
                val = val[:-1] if val[-1] == "." else val
                if do_id[0:5] == "DOID_":
                    desc_dict[do_id] = val
            if parts[1] == "<http://www.geneontology.org/formats/oboInOwl#hasExactSynonym>":
                do_id = parts[0].split("/")[-1].replace(">","")
                val = " ".join(parts[2:-1])[1:-1].replace("@e", "").replace("\"","")
                val = val[:-1] if val[-1] == "." else val
                if do_id not in syn_dict:
                    syn_dict[do_id] = {}
                syn_dict[do_id][val] = True
               

    do_id_list = list(recname_dict.keys())
    #do_id_list = ["DOID_0080600"]
    for do_id in do_id_list:
        record_id = do_id.replace("_",":")
        desc = desc_dict[do_id] if do_id in desc_dict else ""
        url = "http://purl.obolibrary.org/obo/%s" % (do_id)
        record_obj = {
            "id": record_id,
            "recommended_name": {
                "id":record_id,
                "name": recname_dict[do_id],
                "description": desc,
                "resource": "Disease Ontology",
                "url": url
            },
            "synonyms": []
        }
        if do_id in syn_dict:
            for name in syn_dict[do_id]:
                url = "http://purl.obolibrary.org/obo/%s" % (do_id)
                o = {"id":record_id, "name":name, "resource":"Disease Ontology", "url":url}
                record_obj["synonyms"].append(o)

        file_name = do_id.replace("_",".").lower()
        out_file = "jsondb/diseasedb/%s.json" % (file_name)
        with open(out_file, "w") as FW:
            FW.write("%s\n" % (json.dumps(record_obj, indent=4))) 

 
    return 




if __name__ == '__main__':
    main()
 
