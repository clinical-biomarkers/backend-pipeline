import os
import csv
import sys
import json
import glob
import gzip
import xml.etree.ElementTree as ET
from Bio import SeqIO
import time
import requests
from optparse import OptionParser







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





    file_list = glob.glob("/data/shared/biomarkerdb/downloads/ncbi/medline_json/pmid.*.json")
    is_downloaded = {}
    for in_file in file_list:
        pmid = in_file.split(".")[-2]
        is_downloaded[pmid] = True

    seen = {}
    file_list = glob.glob(release_dir + "unreviewed/biomarkers_*.tsv")
    for in_file in file_list:
        file_name = in_file.split("/")[-1]
        with open(in_file, "r") as FR:
            f_list, lcount = [], 0
            for line in FR:
                lcount += 1
                row = line[0:-1].strip().split("\t")
                if lcount == 1:
                    f_list = row
                else:
                    evidence_source = row[f_list.index("evidence_source")]
                    prefix = evidence_source.split(":")[0]
                    if prefix not in ["PubMed"]:
                        continue
                    xref_id = evidence_source.split(":")[1]
                    if xref_id == "" or xref_id.isdigit() == False:
                        continue
                    if xref_id in is_downloaded:
                        continue
                    if xref_id not in seen:
                        seen[xref_id] = {}
                    seen[xref_id][file_name] = True
   
    FW = open("/data/shared/biomarkerdb/logs/medline-download-list.txt", "w") 
    for xref_id in seen:
        file_list = list(seen[xref_id].keys())
        FW.write("%s %s\n" % (xref_id, ";".join(file_list)))
    FW.close()  


            
    return


                


if __name__ == '__main__':
    main()

