import os,sys
import string
from optparse import OptionParser
import glob
import json
from bson import json_util
import pymongo
from pymongo import MongoClient
import datetime
import pytz
import subprocess
import orjson

__version__="1.0"
__status__ = "Dev"




def write_progress_msg(msg, flag):
    ts = datetime.datetime.now()
    with open(log_file,  flag) as F:
        F.write("%s [%s]\n" % (msg, ts))
    return

            

def get_coll_list(db_list):
    coll_list = []
    for d in db_list:
        if d[-2:] != "db":
            continue                                    
        coll = "c_" + d[:-2]
        if coll in ["c_jumbo"]:
            continue                                                                            
        coll_list.append(coll)
    
    return coll_list


def get_archived_docs(coll):

    tmp_list = []

    cmd = "ls -tr " + "/data/shared/glygen/archive/%s-*.json" % (coll)
    file_list = subprocess.getoutput(cmd).split("\n")
    in_file = file_list[-1]

    doc_list = []
    b = open(in_file, "r").read()
    if b.strip() != "":
        tmp_list = json.loads(b)
        for doc in tmp_list:
            if "_id" in doc:
                doc.pop("_id")
            for p in ["start_date", "end_date", "createdts", "updatedts"]:
                if p in doc:
                    doc[p] = datetime.datetime.strptime(doc[p].split(".")[0], '%Y-%m-%d %H:%M:%S')
            doc_list.append(doc)

    return doc_list


###############################
def main():


    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-s","--server",action="store",dest="server",help="dev/tst/beta/prd")
    parser.add_option("-v","--dataversion",action="store",dest="dataversion",help="2.0.2/2.0.3 ...")
    parser.add_option("-c","--coll",action="store",dest="coll",help="OPTIONAL c_glycan,c_protein ")
        
    (options,args) = parser.parse_args()

    for key in ([options.server, options.dataversion]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    global log_file

    server = options.server
    ver = options.dataversion


    db_name = "bmkbdb_beta" if server == "beta" else "bmkbdb"
    
    config_obj = json.loads(open("./conf/config.json", "r").read())
    mongo_port = config_obj["dbinfo"]["port"][server]
    host = "mongodb://127.0.0.1:%s" % (mongo_port)



    jsondb_dir = config_obj["data_path"] + "/releases/data/v-%s/jsondb/" % (ver)
    dump_dir = config_obj["data_path"] + "/mongodump/"
    tmpdb_user = config_obj["dbinfo"]["tmpdb"]["user"]
    tmpdb_pass = config_obj["dbinfo"]["tmpdb"]["password"]
    tmpdb_name =  config_obj["dbinfo"]["tmpdb"]["db"]
 
    db_user = config_obj["dbinfo"][db_name]["user"]
    db_pass = config_obj["dbinfo"][db_name]["password"]
    db_name =  config_obj["dbinfo"][db_name]["db"]
    text_indexed_colls = []
    index_dict = json.load(open("conf/indexes.json"))


    archived_colls = ["c_video", "c_outreach", "c_event"]

    batch_colls = ["c_biomarker","c_list","c_index", "c_idtrack"]

    db_list = config_obj["downloads"]["jsondb"]
    coll_list = get_coll_list(db_list)
    if options.coll != None:
        coll_list =  options.coll.split(",")


    try:
        tmpdb_client = pymongo.MongoClient(host,
            username=tmpdb_user,
            password=tmpdb_pass,
            authSource=tmpdb_name,
            authMechanism='SCRAM-SHA-1',
            serverSelectionTimeoutMS=10000
        )
        tmpdb_dbh = tmpdb_client[tmpdb_name]



        for coll in coll_list:

            log_file = "logs/%s_loading_progress_%s.txt" % (coll, server)
            msg = "\n ... started loading %s.%s version %s" % (db_name, coll, ver)
            write_progress_msg(msg, "w")

            #drop all existing collections 
            write_progress_msg(" ... dropping tmpdb.%s" % (coll), "a")
            tmpdb_dbh[coll].drop()

            if coll in text_indexed_colls:
                tmpdb_dbh[coll].drop_indexes()
            if coll in archived_colls:
                doc_list = get_archived_docs(coll)
                nrecords_total = len(doc_list)
                nrecords = 0
                for doc in doc_list:
                    result = tmpdb_dbh[coll].insert_one(doc)
                    nrecords += 1
                    if nrecords != 0 and nrecords%1000 == 0:
                        msg = " ... loaded %s out of %s documents to tmpdb.%s" % (nrecords, nrecords_total, coll)
                        write_progress_msg(msg, "a") 
            else:
                json_db = coll[2:] + "db"
                file_list = glob.glob(jsondb_dir + "/" + json_db + "/*.json")
                #file_list = glob.glob(jsondb_dir + "/" + json_db + "/G17689DH*.json")
                #exit()
                nrecords_total = len(file_list)
                nrecords = 0
                for in_file in file_list:
                    doc_list = []
                    if coll in batch_colls:
                        doc_list = orjson.loads(open(in_file, "r").read())
                    else:
                        doc_list = [orjson.loads(open(in_file, "r").read())]
                    for doc in doc_list:
                        if "_id" in doc:
                            doc.pop("_id")
                        if coll in ["c_index"]:
                            for obj in doc:
                                result = tmpdb_dbh[coll].insert_one(obj)
                        else:
                            result = tmpdb_dbh[coll].insert_one(doc)     
                        nrecords += 1
                        if nrecords != 0 and nrecords%1000 == 0:
                            msg = " ... loaded %s documents to tmpdb.%s" % (nrecords, coll)
                            write_progress_msg(msg, "a")
            ts = datetime.datetime.now()
            msg = " ... finished loading %s documents to tmpdb.%s" % (nrecords,coll)
            write_progress_msg(msg, "a")

            #CREATING COLLECTION
            if coll in text_indexed_colls:
                msg = "\n ... creating text index for tmpdb.%s" % (coll)
                write_progress_msg(msg, "a")
                res = tmpdb_dbh[coll].create_index([("$**", pymongo.TEXT)])
                msg = " ... finished creating text index for tmpdb.%s" % (coll)
                write_progress_msg(msg, "a")

            if coll in index_dict:
                index_name_list = []
                for cur in tmpdb_dbh[coll].list_indexes():
                    index_name_list.append(cur["name"])
                for path in index_dict[coll]:
                    index_name = index_dict[coll][path]
                    if index_name in index_name_list:
                        msg = "\n ... dropping field index (path=%s) for tmpdb.%s" % (path, coll)
                        write_progress_msg(msg, "a")
                        res = tmpdb_dbh[coll].drop_index(index_name)
                        msg = " ... finished dropping field index (path=%s) for tmpdb.%s"%(path,coll)
                        write_progress_msg(msg, "a")

                    msg = "\n ... creating field index (path=%s) for tmpdb.%s" % (path, coll)
                    write_progress_msg(msg, "a")
                    res = tmpdb_dbh[coll].create_index([(path, -1 )], name=index_name)
                    msg = " ... finished creating field index (path=%s) for tmpdb.%s" % (path, coll)
                    write_progress_msg(msg, "a")



            # NOW CREARING DUMP DIR
            write_progress_msg("\n ... removing old tmpdb dump", "a")
            cmd = "rm -rf %s/tmpdb " % (dump_dir)
            x = subprocess.getoutput(cmd)


            write_progress_msg("\n ... creating new tmpdb.%s dump" % (coll), "a")
            cmd = "mongodump  --port=%s --username %s --password %s "
            cmd += "--db tmpdb --collection %s --out %s "
            cmd = cmd % (mongo_port, tmpdb_user, tmpdb_pass, coll, dump_dir)
            x = subprocess.getoutput(cmd)

            write_progress_msg("\n ... restoring tmpdb dump to %s.%s" % (db_name, coll), "a")
            cmd = "mongorestore --port=%s --username %s --password %s --db %s "
            cmd += "%s/tmpdb --drop "
            cmd = cmd % (mongo_port, db_user, db_pass, db_name, dump_dir)
            x = subprocess.getoutput(cmd)
            write_progress_msg("\n ... finished restoring", "a") 

            #update supersearch_init
            if coll == "c_searchinit":
                cmd = "python3 update-search-init.py -s %s" % (server)
                x = subprocess.getoutput(cmd)


    except pymongo.errors.ServerSelectionTimeoutError as err:
        print (err)
    except pymongo.errors.OperationFailure as err:
        print (err)



if __name__ == '__main__':
    main()
