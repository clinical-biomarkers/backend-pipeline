import csv
import json
from collections import defaultdict

def get_sheet_stats_detailed(in_file, separator=","):

    seen_row, seen = {}, {}
    row_count, id_count, field_count = 0, 0, 0
    f_list = []
    with open(in_file, 'r') as FR:
        csv_grid = csv.reader(FR, delimiter=separator, quotechar='\"')
        idx = 0
        for row in csv_grid:
            if json.dumps(row) in seen_row:
                continue
            seen_row[json.dumps(row)] = True
            if idx == 0:
                field_count = len(row)
                f_list = row
                for f in f_list:
                    seen[f] = {}
            else:
                value_count = len(row)
                if field_count != value_count:
                    print ("ERROR: row_number=%s field_count=%s value_count=%s" % (idx, field_count, value_count))
                    exit(-1)
                row_count += 1
                for j in range(0, len(f_list)):
                    seen[f_list[j]][row[j]] = True 
            idx += 1

    res_obj = {"uniquecount":{}, "rowcount":row_count}
    for f in seen:
        res_obj["uniquecount"][f] = len(list(seen[f].keys()))

    return res_obj
