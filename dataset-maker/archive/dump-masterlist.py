#!/usr/bin/python
import os,sys
import string
import csv
import json
import glob
import requests
import subprocess
from Bio import SeqIO
import csvutil


def main():
    
    conditionid2loincid = {}

    misc_dir = "/data/shared/biomarkerdb/releases/data/current/misc/"
    if os.path.isdir(misc_dir) == False:
        cmd = "mkdir -p " + misc_dir
        x = subprocess.getoutput(cmd)

    out_file = misc_dir + "MASTERLIST.csv"
    FW = open(out_file, "w")
    newrow = ["biomarker_id","entity_id","condition_id","loinc_id","biomarker"]
    FW.write("\"%s\"\n" % ("\",\"".join(newrow)))
    current_dir = "/data/shared/biomarkerdb/generated/datamodel/merged/current/"
    file_list = glob.glob(current_dir + "merged_json_old/*.json")
    for in_file in file_list:
        file_name = in_file.split("/")[-1]
        doc = json.load(open(in_file))
        biomarker_id = doc["biomarker_id"]
        if "biomarker_component" not in doc:
            continue
        if "condition" not in doc:
            continue
        if doc["condition"] == None:
            continue
        condition_id = doc["condition"]["id"]
        loinc_id = conditionid2loincid[condition_id] if condition_id in conditionid2loincid else ""
        for obj in doc["biomarker_component"]:
            biomarker = obj["biomarker"] if "biomarker" in obj else ""
            ent_id = obj["assessed_biomarker_entity_id"]
            newrow = [biomarker_id,ent_id,condition_id,loinc_id,biomarker]
            FW.write("\"%s\"\n" % ("\",\"".join(newrow)))
   
    FW.close()

    cmd = "chmod 775 " + out_file
    x = subprocess.getoutput(cmd)

    print ("created:", out_file)


 


    return

if __name__ == '__main__':
    main()



