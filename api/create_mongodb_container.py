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

    mongo_network = config_obj["dbinfo"]["bridge_network"]
    if server in ["prd", "beta"]:
        mongo_network = config_obj["dbinfo"]["bridge_network"] + "_" + server

    u, p = config_obj["dbinfo"]["admin"]["user"], config_obj["dbinfo"]["admin"]["password"]
    e_params = "-e MONGO_INITDB_ROOT_USERNAME=%s -e MONGO_INITDB_ROOT_PASSWORD=%s" % (u, p)

    cmd_list = []
    cmd_list.append("sudo systemctl stop docker-glygen-mongo-%s.service" % (server))
    for c in [mongo_container, api_container, substructure_container]:
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
    cmd += " -v /data/shared/glygen/mongodump/%s:/data/shared/glygen/mongodump -v /data/shared/glygen/db/%s:/data/shared/glygen/db %s mongo" % (server, server, e_params)
    cmd_list.append(cmd)

    for cmd in cmd_list:
        x = subprocess.getoutput(cmd)
        print (x)

    #remove dangling images
    cmd = "docker images -f dangling=true"
    line_list = subprocess.getoutput(cmd).split("\n")
    for line in line_list[1:]:
        image_id = line.split()[2]
        cmd = "docker image rm -f " + image_id
        x = subprocess.getoutput(cmd)



if __name__ == '__main__':
    main()
