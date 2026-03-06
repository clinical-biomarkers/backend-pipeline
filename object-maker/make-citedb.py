import os,sys
import json
import glob
import datetime
import csvutil
from optparse import OptionParser
import random
import orjson


###############################
def main():


    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-r","--rel",action="store",dest="rel",help="")
    parser.add_option("-s","--start",action="store",dest="start",help="")
    parser.add_option("-e","--end",action="store",dest="end",help="")
    (options,args) = parser.parse_args()
    for key in ([ options.start, options.end]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    start = int(options.start)
    end = int(options.end)
    rel = options.rel

    global release_dir
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)



    file_list = glob.glob("/data/shared/biomarkerdb/downloads/ncbi/medline_json/pmid.*.json")
    file_list = sorted(file_list)
    end = len(file_list) if end > len(file_list) else end

    log_file = "/data/shared/biomarkerdb/logs/make-citedb.%s-%s.txt" % (start, end)
    with open(log_file, "w") as FL:
        FL.write("")
                
    idx = 0
    total = len(file_list[start-1:end])
    record_obj_list = []
    batch_idx = 0
    for in_file in file_list[start-1:end]:
        idx += 1
        pmid = in_file.split(".")[-2]
        url = "https://pubmed.ncbi.nlm.nih.gov/" + pmid
        ref_obj = {"id": pmid, "type": "PubMed", "url":url}
        doc = {"pmid":pmid,"title": "","journal":"","date":"","authors":"","reference": [ref_obj], "evidence": []}
        if os.path.isfile(in_file) == False:
            continue
        obj = orjson.loads(open(in_file, "rb").read())
        if "AU" not in obj and "IR" in obj:
            obj["AU"] = obj["IR"]
        if "AU" not in obj:
            obj["AU"] = ["author information missing"]
        for tag in ["TI", "DP", "JT", "BTI"]:
            if tag not in obj:
                obj[tag] = ["missing tag=%s" % (tag)]
        row, flag_list = [], []
        if flag_list == []:
            if type(obj["TI"]) is list:
                title = " ".join(obj["TI"]).replace("\"", "`")
                journal = " ".join(obj["JT"]) if "JT" in obj else " ".join(obj["BTI"])
                pubdate = " ".join(obj["DP"])
                authors = ", ".join(obj["AU"])
                row = [title, journal, pubdate, authors]
            else:
                title = obj["TI"].replace("\"", "`")
                journal = obj["JT"] if "JT" in obj else obj["BTI"]
                pubdate = obj["DP"]
                authors = obj["AU"]
                row = [title, journal, pubdate, authors]
        if len(row) == 4:
            doc["title"] = row[0]
            doc["journal"] = row[1]
            doc["date"] = row[2]
            doc["authors"] = row[3]

        if idx%100 == 0:
            with open(log_file, "a") as FL:
                FL.write("make-citedb: finished %s/%s\n" % (idx, total))
        record_obj_list.append(doc)
        if len(record_obj_list) == 100:
            batch_idx += 1
            out_file = release_dir + "jsondb/citedb/batch.%s-%s.%s.json" % (start, end, batch_idx)
            with open(out_file, "wb") as FW:
                FW.write(orjson.dumps(record_obj_list))
            record_obj_list = []
             

    if len(record_obj_list) > 0:
        batch_idx += 1
        out_file = release_dir + "jsondb/citedb/batch.%s-%s.%s.json" % (start, end, batch_idx)
        with open(out_file, "wb") as FW:
            FW.write(orjson.dumps(record_obj_list))


    return 




if __name__ == '__main__':
    main()
 
