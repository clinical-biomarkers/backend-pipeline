import os,sys
import string
from optparse import OptionParser
import glob
import json
import datetime


__version__="1.0"
__status__ = "Dev"



###############################
def main():


    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-s","--server",action="store",dest="server",help="dev/tst/beta/prd")
    (options,args) = parser.parse_args()

    for key in ([options.server]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    server = options.server
    config_obj = json.loads(open("./conf/config.json", "r").read())
    api_port = config_obj["api_port"][server] 

    line_list = json.loads(open("tests/TEST.json", "r").read())

    for line in line_list:
        cmd = "http POST :%s%s" % (api_port, line)
        print (cmd)  



if __name__ == '__main__':
    main()
