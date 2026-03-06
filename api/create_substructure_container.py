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
    image = "glyomics/substructure"
    port = config_obj["ss_port"][server]
    container_name = "running_substructure"
    if server == "beta":
        container_name = "running_substructure_%s" % (server)

    #network = config_obj["dbinfo"]["bridge_network"]
    #if server in ["prd", "beta"]:
    #    network = config_obj["dbinfo"]["bridge_network"] + "_" + server
    network = "host"

    cmd_list = []
    cmd_list.append("sudo systemctl stop docker-glygen-substructure-%s.service" % (server)) 
    

    cmd = "docker ps --all |grep %s" % (container_name)
    container_id = subprocess.getoutput(cmd).split(" ")[0].strip()
    if container_id.strip() != "":
        cmd_list.append("docker rm -f %s " % (container_id))


    #cmd = "docker create --name %s --network %s -p %s:%s" % (container_name, network, port, port)
    #cmd = "docker create --name %s --net=%s " % (container_name, network)
    
    # get into the container and use "ip addr" to find the actual port
    cmd = "docker create --name %s -p 0.0.0.0:%s:%s" % (container_name, port, "80")
    cmd += " -e WEBSERVICE_BASIC_PORT=%s -e WEBSERVICE_BASIC_MAX_CPU_CORE=3 %s " % (port, image)
    cmd_list.append(cmd)

    cmd_list.append("sudo systemctl start docker-glygen-substructure-%s.service" % (server))
    

    for cmd in cmd_list:
        x = subprocess.getoutput(cmd)
        print (x)



if __name__ == '__main__':
    main()
