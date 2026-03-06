import json
import requests


#port = "8082"
#port = "4042"
port = "4442"

#api_name = "batch_retrieval"
api_name = "isoform_mapper"


test_info = {
    "isoform_mapper":{
        "url":"http://localhost:%s/job/addnew/" % (port),
        "infile":"tmp/isoform_mapper.1.csv",
        "payload":{
            "jobtype":"isoform_mapper",
            "parameters":{}
        }
    },
    "batch_retrieval":{
        "url":"http://localhost:%s/job/addnew/" % (port),
        #"infile":"tmp/Protein_search_human.csv",
        "infile":"tmp/Raja.s_example_list.csv",
        #"infile":"tmp/toy.txt",
        "payload":{
            "jobtype":"batch_retrieval",
            "parameters":json.dumps(
                {
                    "inputnamespace":"UniProtKB", 
                    "columns":[{"id":"species","label":"Species","filter_type":"none","output_type":"id","order":1},{"id":"go_mf","label":"GO Molecular Function","filter_type":"none","output_type":"id","order":2}]
                })
        }
    }
}


url = test_info[api_name]["url"]
in_file = test_info[api_name]["infile"]
req_obj = test_info[api_name]["payload"]

files = {"userfile": open(in_file, 'rb')}
res = requests.post(url, files=files, data=req_obj)
res_obj = json.loads(res.content)
print (res.status_code)
print (json.dumps(res_obj, indent=4))





