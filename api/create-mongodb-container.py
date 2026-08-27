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

    config_file = "conf/config.json"
    config_obj = json.loads(open(config_file, "r").read())

    api_container = "running_bmkb_api_%s" % (server)
    mongo_container = "running_bmkb_mongo_%s" % (server)
    mongo_network = config_obj["dbinfo"]["bridge_network"] + "_" + server
    mongo_port = config_obj["dbinfo"]["port"][server]
    data_path = config_obj["data_path"]

    u, p = config_obj["dbinfo"]["admin"]["user"], config_obj["dbinfo"]["admin"]["password"]
    e_params = "-e MONGO_INITDB_ROOT_USERNAME=%s -e MONGO_INITDB_ROOT_PASSWORD=%s" % (u, p)


    cmd_list = []
    for c in [mongo_container, api_container]:
        cmd = "docker ps --all |grep %s" % (c)
        container_id = subprocess.getoutput(cmd).split(" ")[0].strip()
        if container_id.strip() != "":
            cmd_list.append("docker rm -f %s " % (container_id))


    cmd = "docker network ls| grep %s" % (mongo_network)
    x = subprocess.getoutput(cmd).split()
    if x != []:
        if x[1] == mongo_network:
            cmd_list.append("docker network rm %s | true" % (mongo_network))
    
    cmd_list.append("docker network create -d bridge %s" % (mongo_network))
    
    cmd = "docker create --name %s --network %s -p 127.0.0.1:%s:27017" % (mongo_container, mongo_network,mongo_port)
    cmd += " -v %s/db/%s:/data/db %s mongo" % (data_path, server,  e_params)
    
    cmd_list.append(cmd)

    for cmd in cmd_list:
        x = subprocess.getoutput(cmd)
        #print (cmd)
        print (x)


if __name__ == '__main__':
    main()


