import os,sys
import json
import glob
import datetime
import csvutil
import subprocess
from optparse import OptionParser
import psutil
import orjson
import hashlib
import random
import myvariant

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

     # clean out_dir
    out_dir = release_dir + "jsondb/rsdb/"
    if os.path.isdir(out_dir):
        cmd = "rm -rf %s/*" % (out_dir)
        x = subprocess.getoutput(cmd)


    seen_rsid = csvutil.get_unmapped_rsid_list(release_dir)
    rsid_list = sorted(list(seen_rsid.keys()))
 
 
    mv = myvariant.MyVariantInfo()
    record_obj_list = []
    batch_idx = 0
    for r in rsid_list:
        rsid = r.replace("dbSNP:", "")
        res = mv.getvariant(rsid, fields='dbsnp.gene')
        if type(res) is not list:
            continue
        o_list = []
        for obj in res:
            if "dbsnp" not in obj:
                continue
            gene_obj_list = [obj["dbsnp"]["gene"]] if type(obj["dbsnp"]["gene"]) is dict else obj["dbsnp"]["gene"]
            for o in gene_obj_list:
                o_list.append({"geneid":o["geneid"], "name":o["name"]})
        if o_list != []:
            doc = {"entity_id":r, "map":o_list }
            record_obj_list.append(doc)
            if len(record_obj_list) == 100:
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



    return 




if __name__ == '__main__':
    main()
 
