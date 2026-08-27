import os,sys
import string
from optparse import OptionParser
import glob
import json
import csvutil
import datetime
import pytz
import orjson

__version__="1.0"
__status__ = "Dev"



def main():

    
    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-r","--rel",action="store",dest="rel",help="")
    parser.add_option("-s","--start",action="store",dest="start",help="")
    parser.add_option("-e","--end",action="store",dest="end",help="")
    (options,args) = parser.parse_args()
    for key in ([options.rel, options.start, options.end]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    rel = options.rel
    s = int(options.start)
    e = int(options.end)

    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)
 
    file_list = sorted(glob.glob(release_dir + "jsondb/biomarkerdb/*.json"))
    e = len(file_list) if e > len(file_list) else e
    
    out_file = release_dir + "jsondb/interm/statdb/output.%s-%s.csv" % (s, e)
     
    log_file = "/data/shared/biomarkerdb/logs/make-statdb.%s-%s.log" % (s, e)
    msg = ""
    csvutil.write_log_msg(log_file, msg, "w")


    newrow = ["biomarker_id","condition_id","agent_id","entity_type", "role_list", "source_list","keywords","flag"]
    with open(out_file, "w") as FW:
        FW.write("\"%s\"\n" % ("\",\"".join(newrow)))

    idx = 0
    total = e - s + 1
    row_list = []
    for in_file in file_list[s-1:e]:
        doc_list = orjson.loads(open(in_file, "rb").read())
        for doc in doc_list:
            biomarker_id = doc["biomarker_id"]
            condition_id, agent_id = "", ""
            if "condition" in doc:
                if doc["condition"] != {}:
                    condition_id = doc["condition"]["id"]
            if "exposure_agent" in doc:
                if "id" in doc["exposure_agent"]:
                    agent_id = doc["exposure_agent"]["id"]

            source_list = doc["source_list"]
            kw_list = doc["keywords"]
            role_list = []
            for o in doc["best_biomarker_role"]:
                role_list.append(o["role"])
            flag_list = []
            if len(doc["biomarker_component"]) == 1:
                flag_list.append("biomarker_single")
            if len(doc["biomarker_component"]) > 1:
                flag_list.append("biomarker_multi")
            for obj in doc["biomarker_component"]:
                ent_type = obj["assessed_entity_type"]
                flags, sources, roles = ";".join(flag_list), ";".join(source_list), ";".join(role_list)
                keywords = ";".join(kw_list)
                newrow = [biomarker_id,condition_id,agent_id,ent_type, roles, sources, keywords,flags]
                row_list.append(newrow)
        if len(row_list) == 1000:
            with open(out_file, "a") as FW:
                for newrow in row_list:
                    FW.write("\"%s\"\n" % ("\",\"".join(newrow)))
                    idx += 1
            msg = "created %s rows" % (idx)
            csvutil.write_log_msg(log_file, msg, "a")
            row_list = []

 
    if len(row_list) > 0:
        with open(out_file, "a") as FW:
            for newrow in row_list:
                FW.write("\"%s\"\n" % ("\",\"".join(newrow)))
                idx += 1
        msg = "created %s rows" % (idx)
        csvutil.write_log_msg(log_file, msg, "a")

    return





            

if __name__ == '__main__':
	main()



