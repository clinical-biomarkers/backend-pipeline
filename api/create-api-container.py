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
    image = "bmkb_api"
    api_container = "running_" + image
    mongo_container = "running_bmkb_mongo"
    api_port = config_obj["api_port"]

        
    db_name = "bmkbdb"

    data_path = config_obj["data_path"]
    network = config_obj["dbinfo"]["bridge_network"]
    mongo_user = config_obj["dbinfo"][db_name]["user"]
    mongo_password = config_obj["dbinfo"][db_name]["password"]
    mongo_db =  config_obj["dbinfo"][db_name]["db"]



    conn_str = "mongodb://%s:%s@%s:27017/?authSource=%s" % (mongo_user, mongo_password, mongo_container, mongo_db)
    cmd_list = []
    cmd_list.append("python3 setup.py bdist_wheel")
    cmd_list.append("docker build --network=host -t %s ." % (image))
    for c in [api_container]:
        cmd = "docker ps --all |grep %s" % (c)
        container_id = subprocess.getoutput(cmd).split(" ")[0].strip()
        if container_id.strip() != "":
            cmd_list.append("docker rm -f %s " % (container_id))


    env_list = [
        " -e MONGODB_CONNSTRING=%s" % (conn_str),
        " -e DB_NAME=%s" % (mongo_db),
        " -e DATA_PATH=%s" % (data_path), 
        " -e SERVER=%s" % (host_vm)
    ] 
    llm_dict = json.load(open("/data/shared/auth/.llm.json"))
    for k in llm_dict:
        env_list.append(" -e %s=%s" % (k, llm_dict[k]))

    cmd = "docker create --name %s --network %s -p 127.0.0.1:%s:8888" % (api_container, network, api_port)
    cmd += " -v %s:%s -v /software/pipes:/hostpipe " % (data_path, data_path)
    for env in env_list:
        cmd += env
    cmd += " %s" % (image)
    cmd_list.append(cmd)

    for cmd in cmd_list:
        subprocess.run(cmd, shell=True)
        #print (cmd)


if __name__ == '__main__':
    main()
