import os,sys
import json
import glob
import datetime
import time
from optparse import OptionParser
import csvutil
import subprocess

def main():

    
    
    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-r","--rel",action="store",dest="rel",help="")
    parser.add_option("-p","--prevrel",action="store",dest="prevrel",help="")
    
    (options,args) = parser.parse_args()
    for key in ([ options.rel, options.prevrel]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    rel = options.rel
    prev_rel = options.prevrel

    global release_dir
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s" % (rel)

    cmd_dict = {}
    db_list = ["biomarkerdb","idtrackdb","listdb","indexdb","sortdb","searchinitdb","statdb"]
    #db_list = ["statdb"]
    for idx in range(0, len(db_list)):
        db = db_list[idx]
        cmd_dict[idx] = {"db":db, "cmdlist":[]}
        if db in ["idtrackdb"]:
            cmd_dict[idx]["cmdlist"].append("rm -f %s/jsondb/%s/*" % (release_dir, db))
            cmd_dict[idx]["cmdlist"].append("python3 make-%s.py -r %s -p %s" % (db,rel, prev_rel))
        elif db in ["indexdb"]:
            cmd_dict[idx]["cmdlist"].append("rm -f %s/jsondb/%s/*" % (release_dir, db))
            cmd_dict[idx]["cmdlist"].append("python3 wrap-make-%s.py -r %s" % (db,rel))
        elif db in ["statdb"]:
            cmd_dict[idx]["cmdlist"].append("rm -f %s/jsondb/interm/%s/*" % (release_dir, db)) 
            cmd_dict[idx]["cmdlist"].append("rm -f %s/jsondb/%s/*" % (release_dir, db))
            cmd_dict[idx]["cmdlist"].append("python3 wrap-make-%s.py -r %s" % (db,rel))
            cmd_dict[idx]["cmdlist"].append("python3 update-%s.py -r %s" % (db,rel))
        elif db in ["listdb"]:
            cmd_dict[idx]["cmdlist"].append("rm -f %s/jsondb/interm/%s/*" % (release_dir, db)) 
            cmd_dict[idx]["cmdlist"].append("rm -f %s/jsondb/%s/*" % (release_dir, db))
            cmd_dict[idx]["cmdlist"].append("python3 make-%s.py -r %s" % (db,rel))
            cmd_dict[idx]["cmdlist"].append("python3 update-%s.py -r %s" % (db,rel))
        else:
            cmd_dict[idx]["cmdlist"].append("rm -f %s/jsondb/%s/*" % (release_dir, db))
            cmd_dict[idx]["cmdlist"].append("python3 make-%s.py -r %s" % (db,rel))

    log_file = "/data/shared/biomarkerdb/logs/run-pipeline.log"
    with open(log_file, "w") as FL:
        FL.write("Started logging ...\n")

    for idx in sorted(cmd_dict):
        db = cmd_dict[idx]["db"]
        for cmd in cmd_dict[idx]["cmdlist"]:
            if cmd.find("update-statdb.py") != -1:
                time.sleep(300)
                #print (cmd)
                x = subprocess.getoutput(cmd)
            else:
                #print (cmd)
                x = subprocess.getoutput(cmd)
        out_dir = "%s/jsondb/%s/*" % (release_dir,db)
        file_list = glob.glob("%s/jsondb/%s/*" % (release_dir,db))
        n = 0
        for in_file in file_list:
            n += len(json.load(open(in_file)))
        with open(log_file, "a") as FL:
            FL.write("created %s %s records under %s\n" % (n,db[:-2], out_dir))

    cmd = "rm -f %s/reviewed/*" % (release_dir)
    x = subprocess.getoutput(cmd)
    cmd = "python3 update-dataset-files.py -r %s" % (rel)
    x = subprocess.getoutput(cmd)
    out_dir = "%s/reviewed/*" % (release_dir)
    file_list = glob.glob("%s/reviewed/*" % (release_dir))
    with open(log_file, "a") as FL:
        FL.write("updated %s dataset files under %s\n" % (len(file_list), out_dir))

    return 




if __name__ == '__main__':
    main()
 
