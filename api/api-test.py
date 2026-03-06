import json
import requests



list_id_dict = {}
in_file = "tests/temp/q.json"
config_obj = json.loads(open(in_file, "r").read())
for api_name in config_obj:
    url = "http://localhost:8082/" + api_name
    #cache_id_in = config_obj[api_name]["id"]
    req_obj = config_obj[api_name]
    res = requests.post(url, json=req_obj, verify=False)
    res_obj = json.loads(res.content)             
    if "list_id" in res_obj:
        list_id_dict[api_name] = res_obj["list_id"]
        continue
    elif "results_summary" in res_obj:
        list_id_dict[api_name] = res_obj["results_summary"]["site"]["list_id"]


for api_name in list_id_dict:
    api_grp = api_name.split("/")[1]
    api_grp = "site" if api_grp == "supersearch" else api_grp
    list_api_name = api_name.replace("/search", "/list")
    cache_id = list_id_dict[api_name]
    url = "http://localhost:8082/" + list_api_name
    req_obj = {"id":cache_id} 
    res = requests.post(url, json=req_obj, verify=False)
    res_obj = json.loads(res.content)
    if "error_list" in res_obj:
        print ("FAILED", url, res_obj)
        continue
    cache_id, listcache_id = res_obj["cache_info"]["cache_id"], res_obj["cache_info"]["listcache_id"]
    print ("PASSED", url, res_obj["cache_info"]["cache_id"], res_obj["cache_info"]["listcache_id"])
    print (json.dumps(res_obj, indent=4))
    exit()
    url = "http://localhost:8082/data/list_download/"
    req_obj = {"id":listcache_id, "format": "csv", "compressed": False}
    req_obj["download_type"] = api_grp + "_list"
    res = requests.post(url, json=req_obj, verify=False)
    #row_list = str(res.content).split("\n")
    print (res.content)





