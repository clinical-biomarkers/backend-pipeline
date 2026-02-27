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


    db_name = "glydb_beta" if server == "beta" else "glydb"

    config_obj = json.loads(open("./conf/config.json", "r").read())

    image = "glygen_api_%s" % (server) 
    api_container = "running_" + image
    mongo_container = "running_glygen_mongo_%s" %(server)
    port = config_obj["api_port"][server]
    data_path = config_obj["data_path"]
    testdb_path = "/local/glygen/testdb"

    downloads_path = config_obj["downloads_path"]
    #network = config_obj["dbinfo"]["bridge_network"] 
    #if server in ["prd", "beta"]:
    #    network = config_obj["dbinfo"]["bridge_network"] + "_" + server

    mongo_user = config_obj["dbinfo"][db_name]["user"]
    mongo_password = config_obj["dbinfo"][db_name]["password"]
    mongo_db =  config_obj["dbinfo"][db_name]["db"]
    mail_server = config_obj["mail"]["server"]
    mail_port = config_obj["mail"]["port"]
    mail_sender = config_obj["mail"]["sender"]

    host_ip = config_obj["host_ip"][server]
    #conn_str = "mongodb://%s:%s@%s:27017/?authSource=%s" % (mongo_user, mongo_password, mongo_container, mongo_db)
    conn_str = "mongodb://%s:%s@%s:27017/?authSource=%s" % (mongo_user, mongo_password, host_ip, mongo_db)

 
    cmd_list = []
    cmd_list.append("sudo systemctl stop docker-glygen-api-%s.service" % (server))
        
    if os.path.isdir(data_path) == False:
        cmd_list.append("mkdir -p %s" % (data_path))

    cmd_list.append("python3 setup.py bdist_wheel")
    cmd_list.append("docker build --network=host -t %s ." % (image))
    for c in [api_container]:
        cmd = "docker ps --all |grep %s" % (c)
        container_id = subprocess.getoutput(cmd).split(" ")[0].strip()
        if container_id.strip() != "":
            cmd_list.append("docker rm -f %s " % (container_id))


    aiseach_token_file = data_path + "/auth/glygen_ai_container_api_key.json"
    token_doc = json.load(open(aiseach_token_file))
    aisearch_token = token_doc[server]["AI_SEARCH_STATIC_BEARER_TOKEN"]
   
 
    #cmd = "docker create --name %s --network %s -p 127.0.0.1:%s:80" % (api_container, network, port)
    cmd = "docker create --name %s -p 127.0.0.1:%s:80" % (api_container, port)
    cmd += " -v /var/run/docker.sock:/var/run/docker.sock -v /usr/bin/docker:/usr/bin/docker"
    cmd += " -v %s:%s -v %s:%s -v %s:%s -e MONGODB_CONNSTRING=%s -e DB_NAME=%s" % (downloads_path, downloads_path, data_path, data_path, testdb_path, testdb_path, conn_str, mongo_db)
    cmd += " -e MAIL_SERVER=%s -e MAIL_PORT=%s -e MAIL_SENDER=%s -e DATA_PATH=%s -e DOWNLOADS_PATH=%s -e SERVER=%s -e AISEARCH_TOKEN=%s  %s" % (mail_server, mail_port, mail_sender, data_path, downloads_path, server, aisearch_token, image)  
    cmd_list.append(cmd)


    for cmd in cmd_list:
        print (cmd)
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
