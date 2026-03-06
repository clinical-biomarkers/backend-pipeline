import os,sys
import string
import glob
import json
import datetime
import requests
from optparse import OptionParser





###############################
def main():

    
    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-b","--batch",action="store",dest="batch",help="")
        
    (options,args) = parser.parse_args()

    for key in ([options.batch]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    batch = options.batch

    canon_list = open("tests/temp/aclist.txt", "r").read().split("\n")

    log_file = "tests/temp/out.%s.log" % (batch)
    with open(log_file, "w") as FW:
        FW.write("started\n")
    for canon in canon_list:
        url = "https://beta-api.glygen.org/protein/detail/%s/" % (canon)
        res = requests.get(url)
        with open(log_file, "a") as FW:
            FW.write("%s,%s\n" % (canon, res.status_code) )

    

if __name__ == '__main__':
    main()


