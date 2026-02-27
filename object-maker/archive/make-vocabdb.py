import os,sys
import json
import glob
import datetime

import csvutil



def main():

    config_obj = json.load(open("conf/config.json"))
    out_dict = {}
    file_list = glob.glob("reviewed/biomarkers_*.tsv")
    for in_file in file_list:
        df = {}
        csvutil.load_sheet(df, in_file, [], "\t")
        f_list = df["fields"]
        for row in df["data"]:
            entity_id = row[f_list.index("assessed_biomarker_entity_id")]
            entity = row[f_list.index("assessed_biomarker_entity")]
            entity_type = row[f_list.index("assessed_entity_type")]
            condition_id = row[f_list.index("condition_id")]
            biomarker = row[f_list.index("biomarker")]
            biomarker_lc = biomarker.lower()
            c_vocab = row[f_list.index("biomarker_controlled_vocab")]
            if entity_id not in out_dict: 
                out_dict[entity_id] = {}
            if condition_id not in out_dict[entity_id]:
                out_dict[entity_id][condition_id] = {}
            out_dict[entity_id][condition_id][biomarker_lc] = c_vocab

    for entity_id  in out_dict:
        ent_key = entity_id.replace(":",".").lower()
        out_file = "jsondb/vocabdb/%s.json" % (ent_key)
        doc = {"entity_id":entity_id, "mapdict":out_dict[entity_id]}
        with open(out_file, "w") as FW:
            FW.write("%s\n" % (json.dumps(doc, indent=4)))

    return 




if __name__ == '__main__':
    main()
 
