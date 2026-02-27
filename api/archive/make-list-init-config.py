import os,sys
import string
import glob
import json
from optparse import OptionParser


__version__="1.0"
__status__ = "Dev"



###############################
def main():


    
    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-r","--rel",action="store",dest="rel",help="2.6.1, 2.7.1")
    (options,args) = parser.parse_args()
    for key in ([options.rel]):
        if not (key):
            parser.print_help()
            sys.exit(0)
    
    rel = options.rel
    rel_dir = "/data/shared/glygen/releases/data/v-%s/" % (rel)

    in_file = rel_dir + "misc/list_init_categories.csv"
    line_list = open(in_file, "r").read().split("\n")
    cat_dict = {}
    for line in line_list[1:-1]:
        row = line.split(",")
        if list(set(row)) == ['']:
            continue
        record_type,cat_id,cat_label,cat_order = row[0], row[1], row[2], row[-1]
        #print (row)
        cat_order = int(cat_order)
        if record_type not in cat_dict:
            cat_dict[record_type] = {}
        cat_dict[record_type][cat_id] = {"label":cat_label, "order":cat_order, "tooltip": ""}

    #record_type,field_id,field_label,field_order,is_default,is_immutable,category_id_list,global_order,description

    in_file = rel_dir + "misc/list_init_fields.csv"
    line_list = open(in_file, "r").read().split("\n")
    tmp_dict = {}
    for line in line_list[1:-1]:
        row = line.split(",")
        if list(set(row)) == ['']:
            continue
        record_type,field_id,field_label,local_order_list = row[0], row[1], row[2], row[3]
        is_default,is_immutable,category_id_list, global_order, field_desc = row[4], row[5], row[6], row[7], row[8]
        global_order = int(global_order) if global_order.strip() != "" else 1000
        if record_type not in tmp_dict:
            tmp_dict[record_type] = {"columns":[], "categories":[]}
        obj = {
            "id":field_id,
            "property_name":field_id, 
            "label":field_label, 
            "order":int(global_order), 
            "tooltip": "",
            "immutable":is_immutable.strip() == "true",
            "default":is_default.strip() == "true", 
            "categories": []
        }
        category_id_list = category_id_list.replace("\"", "").split("|")
        local_order_list = local_order_list.replace("\"", "").split("|")
        #print (category_id_list, local_order_list)
        for i in range(0, len(category_id_list)):
            cat_id = category_id_list[i].strip()
            local_order = local_order_list[i].strip()
            if cat_id in cat_dict[record_type]:
                o = {"id":cat_id, "order":int(local_order)}
                obj["categories"].append(o)
        tmp_dict[record_type]["columns"].append(obj)
        #print (field_id, len(obj["categories"]))  
 
    for record_type in tmp_dict:
        seen = {}
        for obj in tmp_dict[record_type]["columns"]:
            for o in obj["categories"]:
                cat_id = o["id"] 
                if cat_id not in seen:
                    oo = cat_dict[record_type][cat_id]
                    lbl, ordr, tooltip = oo["label"], oo["order"], oo["tooltip"]
                    tmp_dict[record_type]["categories"].append({"id":cat_id, "label":lbl, "order":ordr, "tooltip": tooltip})
                    seen[cat_id] = True
    
    out_file = "glygen/conf/list_init.json"
    with open(out_file, "w") as FW:
        FW.write("%s\n" % (json.dumps(tmp_dict, indent=4)))
    print ("Created %s" % (out_file))



if __name__ == '__main__':
    main()
