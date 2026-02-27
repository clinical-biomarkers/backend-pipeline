import os,sys
import json
import glob
import datetime

import csvutil




def main():

    count_dict = {}
    in_file = "tmp/output.1.txt"
    with open(in_file, "r") as FR:
        for line in FR:
            new = ""
            flag,file_name,orig, v_type,a_type,m_type = "", "", "", "", "", ""
            if line.find("modified") != -1:
                flag,file_name,orig, v_type,a_type,m_type = line.replace("\n", "").split("|")
                new = "%s|%s|%s" % (v_type,a_type,m_type)
            else:
                flag,file_name,orig,new = line.replace("\n", "").split("|")
            if file_name not in count_dict:
                count_dict[file_name] = {"rows_total":0, "rows_not_transformed":0, "rows_transformed":{}}
            count_dict[file_name]["rows_total"] += 1
            if flag == "modified":
                if new not in count_dict[file_name]["rows_transformed"]:
                    count_dict[file_name]["rows_transformed"][new] = 0
                count_dict[file_name]["rows_transformed"][new] += 1
            if flag == "original":
                count_dict[file_name]["rows_not_transformed"] += 1
    
    for file_name in count_dict:
        if "rows_transformed" in count_dict[file_name]:
            o_list = []
            for new in count_dict[file_name]["rows_transformed"]:
                v_type,a_type,m_type = new.split("|")
                n = count_dict[file_name]["rows_transformed"][new]
                o = {"variation_type":v_type, "aspect_type":a_type,"magnitude_type":m_type,"count":n}
                o_list.append(o)
            count_dict[file_name]["rows_transformed"] = o_list

    print (json.dumps(count_dict, indent=4))


            
            


    return 




if __name__ == '__main__':
    main()
 
