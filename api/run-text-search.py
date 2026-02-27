import os,sys
import json
from optparse import OptionParser
import glob
import json
import pymongo
from pymongo import MongoClient




def parse_sent(s,  max_word_count, min_word_count):

    tmp_dict = {}
    if s.strip() == "":
        return
    s = s.lower().replace(",", " ").replace("-", " ").replace(";", " ")
    s = s.replace("(", " ").replace(")", " ").replace("[", " ").replace("]", " ")
    w_list = s.split(" ")
    word_count = len(w_list) + 1
    word_count = max_word_count if word_count > max_word_count else word_count
    for wlen in range(0, word_count):
        if wlen > len(w_list):
            continue
        for i in range(0, len(w_list)):
            l = []
            for ww in w_list[i:i+wlen]:
                ww = ww.strip()
                if ww != "":
                    l.append(ww)
            if len(l) >= min_word_count:
                phrase = " ".join(l)
                if len(phrase) == 1:
                    continue
                tmp_dict[phrase] = True

    phrase_dict = {}
    for phrase in tmp_dict:
        n = len(phrase.split(" "))
        phrase_dict[n] = phrase

    return phrase_dict



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
    #mongo_port = config_obj["dbinfo"]["port"][server]
    mongo_port = "27017"
    host = "mongodb://127.0.0.1:%s" % (mongo_port)

    db_obj = config_obj["dbinfo"][db_name]
    glydb_name, db_user, db_pass =  db_obj["db"], db_obj["user"], db_obj["password"]

    try:
        client = pymongo.MongoClient(host,
            username=db_user,
            password=db_pass,
            authSource=glydb_name,
            authMechanism='SCRAM-SHA-1',
            serverSelectionTimeoutMS=10000
        )
        client.server_info()
        dbh = client[glydb_name]
        
        prj_obj = {"record_type":1, "record_id":1, "section":1}
        s = "prostate cancer"
        phrase_dict = parse_sent(s, 6, 1)
        hit_dict = {}
        for word_count in sorted(phrase_dict, reverse=True):
            phrase = phrase_dict[word_count]
            qry_obj = {"phraselist":{"$eq":phrase}}
            #doc_list = list(dbh["c_index"].find(qry_obj, prj_obj))
            #print (len(doc_list), qry_obj)
            for doc in dbh["c_index"].find(qry_obj, prj_obj):
                record_type, record_id, sec = doc["record_type"], doc["record_id"], doc["section"]
                if record_type not in hit_dict:
                    hit_dict[record_type] = {"all":{}}
                hit_dict[record_type]["all"][record_id] = True
                if sec not in hit_dict[record_type]:
                    hit_dict[record_type][sec] = {}
                hit_dict[record_type][sec][record_id] = True


        exact_match_list = [{"id": "G17689DH","name": "G17689DH","type": "glycan"}]
        res_obj = {"exact_matches":exact_match_list, "other_matches":{}}
        for record_type in hit_dict:
            for sec in ["all"]:
                list_id = "xx"
                n = len(hit_dict[record_type][sec].keys())
                if record_type not in res_obj["other_matches"]:
                    res_obj["other_matches"][record_type] = {}
                if sec not in res_obj["other_matches"][record_type]:
                    res_obj["other_matches"][record_type][sec] = {"count":n, "list_id":list_id}
        print (json.dumps(res_obj, indent=4))
 
    except pymongo.errors.ServerSelectionTimeoutError as err:
        print (err)
    except pymongo.errors.OperationFailure as err:
        print (err)

    return




if __name__ == '__main__':
    main()


