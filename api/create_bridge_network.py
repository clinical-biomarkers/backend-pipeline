import os,sys
import string
from optparse import OptionParser
import glob
import json
import subprocess

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
    api_image = "glygen_api_%s" % (server)
    api_container = "running_" + api_image
    substructure_container = "running_substructure"

    mongo_container = "running_glygen_mongo_%s" % (server)
    mongo_port = config_obj["dbinfo"]["port"][server] 


    network_name = config_obj["dbinfo"]["bridge_network"]
    if server in ["prd", "beta"]:
        network_name = config_obj["dbinfo"]["bridge_network"] + "_" + server


    cmd_list = []
    for c in [mongo_container, api_container, substructure_container]:
        cmd = "docker ps --all |grep %s" % (c)
        container_id = subprocess.getoutput(cmd).split(" ")[0].strip()
        if container_id.strip() != "":
            cmd_list.append("docker rm -f %s " % (container_id))

    cmd = "docker network ls| grep %s" % (network_name)
    x = subprocess.getoutput(cmd).split()
    if x != []:
        if x[1] == network_name:
            cmd_list.append("docker network rm %s | true" % (network_name))
    cmd_list.append("docker network create -d bridge %s" % (network_name))

    for cmd in cmd_list:
        print (cmd)
        x = subprocess.getoutput(cmd)
        print (x)




if __name__ == '__main__':
    main()
