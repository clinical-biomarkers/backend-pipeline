import os,sys
import json
import glob
import datetime
import csvutil
import subprocess
import psutil
import orjson
from optparse import OptionParser


def get_cmb_list_str_list():

    seen_cmb_list_str = {}
    file_list = glob.glob(release_dir + "unreviewed/biomarkers_*.tsv")
    for in_file in file_list:
        source = in_file.split("/")[-1].replace("biomarkers_","").replace(".tsv","")
        with open(in_file, "r") as FR:
            f_list, lcount = [], 0
            for line in FR:
                lcount += 1
                row = line[0:-1].split("\t")
                if lcount == 1:
                    f_list = row
                else:
                    condition_id = row[f_list.index("condition_id")]
                    grp_idx = row[f_list.index("component_group")]
                    if condition_id == "":
                        continue
                    grp = "%s|%s" % (source, grp_idx)
                    cmb_list = grp2cmblist[grp]
                    cmb_list_str = json.dumps(cmb_list)
                    seen_cmb_list_str[cmb_list_str] = True
    cmb_list_str_list = sorted(list(seen_cmb_list_str.keys()))
    
    return cmb_list_str_list


def main():

    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog " )
    parser.add_option("-r","--rel",action="store",dest="rel",help="")

    (options,args) = parser.parse_args()
    for file in ([options.rel]):
        if not (file):
            parser.print_help()
            sys.exit(0)

    rel = options.rel

    global cmb2biomarkerid
    global cmblist2src
    global grp2cmblist
    global release_dir

    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)

    cmb2biomarkerid = csvutil.load_cmb2biomarkerid(release_dir)
    cmblist2src, grp2cmblist = csvutil.load_cmblist2src(release_dir)
    
    cmb_list_str_list = get_cmb_list_str_list()

    id_dict = {}
    for cmb_list_str in cmb_list_str_list:
        cmb_list = json.loads(cmb_list_str)
        cmb_list_new = []
        for cmb in cmb_list:
            ent_id, d_id, vocab = cmb.split("|")
            cmb_list_new.append("%s|%s|%s" % (ent_id, d_id, vocab.lower()))
        cmb_list_str_new = json.dumps(cmb_list_new)
        biomarker_id_list = []
        if cmb_list_str_new in cmb2biomarkerid:
            biomarker_id_list = sorted(list(cmb2biomarkerid[cmb_list_str_new].keys()))
        id_dict[cmb_list_str] = biomarker_id_list[0]


    #first copy all files to reviewed
    cmd = "cp %s/unreviewed/* %s/reviewed/" % (release_dir, release_dir)
    x = subprocess.getoutput(cmd)


    FW1 = open(release_dir + "reviewed/masterlist.tsv", "w")
       
    #update biomarkers_*.tsv to insert biomarker_id
    file_list = glob.glob(release_dir + "unreviewed/biomarkers_*.tsv")
    file_idx = 0
    for in_file in file_list:
        file_idx += 1
        out_file = in_file.replace("unreviewed", "reviewed")
        FW2 = open(out_file, "w")
        source = in_file.split("/")[-1].replace("biomarkers_","").replace(".tsv","")
        with open(in_file, "r") as FR:
            f_list, lcount = [], 0
            for line in FR:
                lcount += 1
                row = line[0:-1].split("\t")
                if lcount == 1:
                    f_list = row
                    newrow = ["biomarker_id"] + row
                    FW2.write("%s\n" % ("\t".join(newrow)))
                    if file_idx == 1:
                        FW1.write("%s\n" % ("\t".join(newrow)))
                else:
                    condition_id = row[f_list.index("condition_id")]
                    grp_idx = row[f_list.index("component_group")]
                    if condition_id == "":
                        continue
                    grp = "%s|%s" % (source, grp_idx)
                    cmb_list = grp2cmblist[grp]
                    cmb_list_str = json.dumps(cmb_list)
                    biomarker_id = id_dict[cmb_list_str] if cmb_list_str in id_dict else "NO_BIOMARKER_ID"
                    newrow = [biomarker_id] + row
                    FW1.write("%s\n" % ("\t".join(newrow)))
                    FW2.write("%s\n" % ("\t".join(newrow)))
        FW2.close()
    FW1.close()


    return




if __name__ == '__main__':
    main()

