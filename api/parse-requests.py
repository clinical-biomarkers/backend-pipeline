import json

in_file_one = "tmp/exceptions.json"
in_file_two = "/data/shared/glygen/archive/c_request-2025-09-10.json"


doc_one = json.load(open(in_file_one))
doc_two = json.load(open(in_file_two))

for obj_one in doc_one:
    parts_one = obj_one["ts"].split(" ")[1].split(":")
    api_one = obj_one["api"]
    print ("\n>", obj_one["id"])
    for obj_two in doc_two:
        parts_two = obj_two["ts"].split(" ")[1].split(":")
        d1 = int(parts_two[0]) - int(parts_one[0])
        d2 = int(parts_two[1]) - int(parts_one[1])
        d3 = int(parts_two[2]) - int(parts_one[2])
        if d1 == 0 and d2 == 0 and d3 > -5:
            api_two = obj_two["api"]
            print (api_one, api_two, obj_two["req"])
            



