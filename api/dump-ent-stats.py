import json
import glob

file_list = glob.glob("/data/shared/biomarkerdb/releases/data/v-3.6.0/jsondb/entdb/*.json")

ent_stat = {}
n2ref = {}
for in_file in file_list:
    doc_list = json.load(open(in_file))
    for doc in doc_list:
        n = len(doc["entities"])
        ref_id = doc["ref_id"]
        if n not in ent_stat:
            ent_stat[n] = 0
        ent_stat[n] += 1
        if n not in n2ref:
            n2ref[n] = {}
        n2ref[n][ref_id] = True
    
for n in ent_stat:
    ref_id_list = list(n2ref[n].keys())
    print (n, ent_stat[n], ref_id_list)

exit()

