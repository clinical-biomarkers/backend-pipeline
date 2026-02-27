import json
import glob
import orjson

rel = "2.4.1"
rel_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)
out_dir = rel_dir +  "jsondb/idtrackdb/"
file_list = glob.glob(rel_dir + "datamodeldb/*.json")

record_obj_list = []
batch_idx = 0
for in_file in file_list:
    doc_list = json.load(open(in_file))
    for doc in doc_list:
        biomarker_id = doc["biomarker_id"]
        print (biomarker_id)
        record_obj = {
            "record_id":biomarker_id,
            "recordtype":"biomarker",
            "history":[{"type":"added", "description":"Introduced in release %s" % (rel)}]
        }
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
 

