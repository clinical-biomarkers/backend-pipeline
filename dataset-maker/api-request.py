import json
import requests


api_url = "https://api.biomarkerkb.org/biomarker/search"
req_obj = {}
#req_obj= {"biomarker_id":"AN4608-1"}

res = requests.post(api_url, json=req_obj)
res_obj =  json.loads(res.content)
list_id = res_obj["list_id"]

api_url = "https://api.biomarkerkb.org/biomarker/list"


limit = 1000
offset = 1
req_obj = {"id":list_id, "offset":offset, "limit":limit}
#print (req_obj)
res = requests.post(api_url, json=req_obj)
res_obj =  json.loads(res.content)
total_length = res_obj["pagination"]["total_length"]
for obj in res_obj["results"]:
    biomarker_id = obj["biomarker_id"]
    biomarker = obj["biomarker"]
    entity_id = obj["assessed_biomarker_entity_id"]
    condition_id = "no_condition"
    if "condition" in obj:
        condition_id = obj["condition"].split("(")[1].replace(")", "")
    cmb = "%s|%s|%s|%s" % (biomarker_id, entity_id, condition_id, biomarker)
    print (cmb)
    #print (obj)

for i in range(1, 1000000):
    offset = limit*i + 1
    if offset > total_length:
        break
    req_obj = {"id":list_id, "offset":offset, "limit":limit}
    #print (req_obj)
    res = requests.post(api_url, json=req_obj)
    res_obj =  json.loads(res.content)
    for obj in res_obj["results"]:
        biomarker_id = obj["biomarker_id"]
        biomarker = obj["biomarker"]
        entity_id = obj["assessed_biomarker_entity_id"]
        condition_id = "no_condition"
        if "condition" in obj:
            condition_id = obj["condition"].split("(")[1].replace(")", "")
        cmb = "%s|%s|%s|%s" % (biomarker_id, entity_id, condition_id, biomarker)
        print (cmb)

