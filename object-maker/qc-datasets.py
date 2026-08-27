import os,sys
import json
import glob
import datetime
import csvutil
import subprocess
import psutil
import orjson
from optparse import OptionParser


def get_file_stats(in_file):

    lcount = 0
    seen = {}
    with open(in_file, "r") as FR:
        f_list = []
        for line in FR:
            lcount += 1
            row = line[:-1].split("\t")
            if lcount == 1:
                f_list = row
            else:
                if "biomarker_id" in f_list:
                    biomarker_id = row[f_list.index("biomarker_id")]
                    seen[biomarker_id] = True
    return lcount, seen



def get_qc_report_one(in_file_one, in_file_two):
    
    lcount_one, seen_one = get_file_stats(in_file_one)
    lcount_two, seen_two = get_file_stats(in_file_two)
     
    ret_obj = {
        "lcount_one":lcount_one,
        "lcount_two":lcount_two,
        "record_count_one":len(seen_one.keys()),
        "record_count_two":len(seen_two.keys())
    } 
    return ret_obj
        

def get_qc_report_two(in_file):
    # code to be implemented
    ret_obj = {}
    
    return ret_obj




def main():

    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-r","--rel",action="store",dest="rel",help="")
    parser.add_option("-p","--prev",action="store",dest="prev",help="")
    (options,args) = parser.parse_args()
    for key in ([options.rel, options.prev]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    rel = options.rel
    prev_rel = options.prev


    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)
    file_list = glob.glob(release_dir + "reviewed/biomarkers_*.tsv")
    file_idx = 0
    for in_file_one in file_list:
        file_idx += 1
        file_name = in_file_one.split("/")[-1]
        in_file_two = "/data/shared/biomarkerdb/releases/data/v-%s/reviewed/%s" % (prev_rel, file_name)
        if os.path.isfile(in_file_two):
            qc_obj_one = get_qc_report_one(in_file_one, in_file_two)
            print ("qc_one",file_name, qc_obj_one)
        if False:
            qc_obj_two = get_qc_report_two(in_file_one)
            print ("qc_two",file_name, qc_obj_two)
            
        




    return




if __name__ == '__main__':
    main()

