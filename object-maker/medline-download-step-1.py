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







def main():


    file_list = glob.glob("downloads/ncbi/medline_json/pmid.*.json")
    is_downloaded = {}
    for in_file in file_list:
        pmid = in_file.split(".")[-2]
        is_downloaded[pmid] = True

    seen = {}
    file_list = glob.glob("unreviewed/biomarkers_*.tsv")
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
   
    FW = open("logs/medline-download-list.txt", "w") 
    for xref_id in seen:
        file_list = list(seen[xref_id].keys())
        FW.write("%s %s\n" % (xref_id, ";".join(file_list)))
    FW.close()  


            
    return


                


if __name__ == '__main__':
    main()

