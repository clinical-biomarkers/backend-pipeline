import os,sys
import json
import glob
import datetime
from optparse import OptionParser
import csvutil




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



    config_obj = json.load(open("conf/config.json"))

    field_info = {
        "age_group":{"type":"str"},
        "sex":{"type":"str"},
        "mean_val":{"type":"float","round":4},
        "median_val":{"type":"float","round":4},
        "sd_val":{"type":"float","round":4},
        "min_val":{"type":"float","round":4},
        "max_val":{"type":"float","round":4},
        "q1":{"type":"float","round":4},
        "q3":{"type":"float","round":4},
        "iqr":{"type":"float","round":4},
        "lower_whisker":{"type":"float","round":4},
        "upper_whisker":{"type":"float","round":4},
        "n_val":{"type":"int"},
        "units":{"type":"str"}
    }

    f_map = {"age_group":"age_grp", "min_val":"min", "max_val":"max"}

    entid2name = {}
    out_dict = {}
    file_list = glob.glob(release_dir + "unreviewed/entity_normalranges_*.tsv")
    for in_file in file_list:
        src = in_file.split("/")[-1].split(".")[0].replace("entity_normalranges_","")
        if src in config_obj["sourceinfo"]:
            src = config_obj["sourceinfo"][src]
        df = {}
        csvutil.load_sheet(df, in_file, [], "\t")
        f_list = df["fields"]
        f_list[0] = "entity_id"
        for row in df["data"]:
            lab_term = row[f_list.index("entity_name_src")]
            entity_id = "%s:%s" % (row[f_list.index("entity_id_src")], row[f_list.index("entity_id")])
            entity_name = row[f_list.index("entity_name")]
            if entity_id not in out_dict:
                out_dict[entity_id] = {}
                entid2name[entity_id] = entity_name
            if src not in out_dict[entity_id]:
                out_dict[entity_id][src] = {}
            if lab_term not in out_dict[entity_id][src]:
                out_dict[entity_id][src][lab_term] = {"lab_term":lab_term, "ranges":[]} 

            o = {}
            skip_flag = False
            for f in field_info:
                ff = f_map[f] if f in f_map else f
                o[ff] = row[f_list.index(f)]
                if o[ff].isnumeric() and field_info[f]["type"] == "int":
                    o[ff] = int(o[ff])
                elif o[ff].replace(".","").replace("-","").isdigit() and field_info[f]["type"] == "float":
                    o[ff] = round(float(o[ff]), field_info[f]["round"]) 
                if field_info[f]["type"] == "float" and type(o[ff]) is not float:
                    skip_flag = True
                if field_info[f]["type"] == "int" and type(o[ff]) is not int:
                    skip_flag = True
            if skip_flag == False:
                out_dict[entity_id][src][lab_term]["ranges"].append(o)
    
    for entity_id in out_dict:
        entity_name = entid2name[entity_id]
        doc = {"entity_name":entity_name, "entity_id":entity_id, "source":[]}
        for src in out_dict[entity_id]:
            for lab_term in out_dict[entity_id][src]:
                if out_dict[entity_id][src][lab_term]["ranges"] == []:
                    continue
                obj = {"source_name":src, "lab_term":lab_term, "ranges":[]}
                t_dict = {}
                for o in out_dict[entity_id][src][lab_term]["ranges"]:
                    s = int(o["age_grp"].split("-")[0].replace("+",""))
                    if s not in t_dict:
                        t_dict[s] = []
                    t_dict[s].append(o)
                for s in sorted(t_dict):
                    obj["ranges"] += t_dict[s]
                doc["source"].append(obj)
        if doc["source"] == []:
            continue 
        out_file = release_dir + "jsondb/normalrangesdb/%s.json" % (entity_id.replace(":", "."))
        with open(out_file, "w") as FW:
            FW.write("%s\n" % (json.dumps(doc, indent=4)))

    return 




if __name__ == '__main__':
    main()
 
