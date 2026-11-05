import os,sys
import string
from optparse import OptionParser
import glob
import json
import subprocess
import socket

__version__="1.0"
__status__ = "Dev"



###############################
def main():

            
    host_name = socket.gethostname()
    host_vm = host_name.split("-")[-1]




    config_file = "conf/config.json"
    config_obj = json.loads(open(config_file, "r").read())

    api_container = "running_bmkb_api"
    mongo_container = "running_bmkb_mongo"
    mongo_network = config_obj["dbinfo"]["bridge_network"]
    mongo_port = config_obj["dbinfo"]["port"]
    data_path = config_obj["data_path"]

    u, p = config_obj["dbinfo"]["admin"]["user"], config_obj["dbinfo"]["admin"]["password"]
    e_params = "-e MONGO_INITDB_ROOT_USERNAME=%s -e MONGO_INITDB_ROOT_PASSWORD=%s" % (u, p)

    cmd_list = []

    cmd = "docker create --name %s --network %s -p 127.0.0.1:%s:27017" % (mongo_container, mongo_network,mongo_port)
    cmd += " -v %s/db/%s:/data/db %s mongo" % (data_path, host_vm,  e_params)
    cmd_list.append(cmd)

    for cmd in cmd_list:
        x = subprocess.getoutput(cmd)
        #print (cmd)
        print (x)


if __name__ == '__main__':
    main()


