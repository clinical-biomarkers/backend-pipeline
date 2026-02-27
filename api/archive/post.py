import requests

api_url = "http://172.17.0.1:10980/submit"
req_obj = {
    'developer_email': 'rykahsay@gwu.edu', 
    'task': '{"align": "substructure", "seq": "RES\\n1b:x-dglc-HEX-1:5\\n2b:x-dgal-HEX-1:5\\n3b:x-dgro-dgal-NON-2:6|1:a|2:keto|3:d\\n4s:n-glycolyl\\n5b:x-dgro-dgal-NON-2:6|1:a|2:keto|3:d\\n6s:n-glycolyl\\nLIN\\n1:1o(-1+1)2d\\n2:2o(-1+2)3d\\n3:3d(5+1)4n\\n4:3o(-1+2)5d\\n5:5d(5+1)6n"}'
}

res = requests.post(api_url, json=req_obj, verify=False)
            
print (res.status_code)
           
