import requests
import json


def create_github_issue(url, authToken, issue_obj):

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + authToken,
        "X-GitHub-Api-Version":"2022-11-28"
    }
   
    res_obj = {} 
    try:
        response = requests.post(url, data=json.dumps(issue_obj), headers=headers)
        code = response.status_code
        if code == 201:
            res = response.json()
            res_obj = {"number":res["number"], "url":res["url"]}
        else:
            res_obj = {"error_list":[{"error_code": "Bad response status code: %s!" % (code)}]}
    except Exception as e:
        #res_obj =  log_error(traceback.format_exc())
        res_obj = {"xxx":"dfafas"}

    return res_obj




def main():

    url = "https://api.github.com/repos/glygener/glygen-issues/issues"
    authToken = "xxxx"
    issue_obj = {
        "title":"Test ... glygen frontend user issue",
        "body":" ... having a problem with this.",
        "assignees":["rykahsay"],
        "labels":["fronten_user_issue"]
    }

    res_obj = create_github_issue(url, authToken, issue_obj)
    print(json.dumps(res_obj, indent=4))

    return 


if __name__ == '__main__':
    main()



