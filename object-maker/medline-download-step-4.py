import os
import sys
import gzip
import json
from optparse import OptionParser
import glob
import pubmed_parser as pp
import subprocess


def load_pmid_dict(in_file):

    seen = {}
    line_list =  open(in_file, "r").read().split("\n")
    for line in line_list:
        pmid = line.split(" ")[0]
        if pmid.strip() == "":
            continue
        seen[pmid] = True

    return seen


###############################
def main():

    xml_folder = "/data/shared/biomarkerdb/downloads/ncbi/medline_xml/"
    list_folder = "/data/shared/biomarkerdb/downloads/ncbi/medline_list/"
    list_file = "/data/shared/biomarkerdb/logs/medline-download-list.txt"
    pmid_dict = load_pmid_dict(list_file)

    file_list = sorted(glob.glob(list_folder + "pubmed*.txt"))
    xmlfile2pmid = {}
    seen = {}
    for in_file in file_list:
        with open(in_file, "r") as FR:
            n = 0
            for pmid in FR:
                pmid = pmid.strip()
                if pmid not in seen and pmid in pmid_dict:
                    file_name = in_file.split("/")[-1].split(".")[0]
                    xml_file = xml_folder + file_name + ".xml.gz"
                    if xml_file not in xmlfile2pmid:
                        xmlfile2pmid[xml_file] = {}
                    xmlfile2pmid[xml_file][pmid] = True
                    seen[pmid] = True
                    n += 1

    out_file = "/data/shared/biomarkerdb/logs/xml_file_list.json"
    xml_file_list = sorted(list(xmlfile2pmid.keys()))
    with open(out_file, "w") as FW:
        FW.write("%s\n" % (json.dumps(xml_file_list, indent=4)))


if __name__ == '__main__':
    main()


