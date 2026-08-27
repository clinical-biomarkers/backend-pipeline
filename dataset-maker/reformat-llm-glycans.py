
def main():

    in_file = "/data/shared/biomarkerdb/downloads/llm_glycan_v2/current/biomarkers.tsv"
    f_list_one = []
    row_dict = {}
    with open(in_file, "r") as FR:
        lcount = 0
        for line in FR:
            lcount += 1
            line = line.replace("assesed_biomarker_entity", "assessed_biomarker_entity")
            row = line.replace("\n", "").replace("\"", "\'").split("\t")
            if lcount == 1:
                f_list_one = row
            else:
                biomarker_id = row[f_list_one.index("unique_entry_id")]
                bgsl_id = row[f_list_one.index("bgsl_id")]
                ent_id = row[f_list_one.index("assessed_biomarker_entity_id")]
                condition_id = row[f_list_one.index("condition_id")]
                if condition_id == "":
                    continue
                if bgsl_id == "":
                    continue
                row_dict[biomarker_id] = {}
                for f in f_list_one:
                    row_dict[biomarker_id][f] = row[f_list_one.index(f)]

    f_list_two = [
        "biomarker_index",
        "component_index",
        "entity_index",
        "assessed_biomarker_entity",
        "assessed_biomarker_entity_id",
        "assessed_entity_type",
        "biomarker_controlled_vocab",
        "assessed_biomarker_entity_id",
        "condition","condition_id",
        "best_biomarker_role","specimen","specimen_id","loinc_code",
        "evidence_source","evidence"
    ]
    print ("\t".join(f_list_two))

    ent_id_field_list = ["bgsl_id", "assessed_biomarker_entity_id"]

    biomarker_idx = 0
    component_idx = 1
    for biomarker_id in row_dict:
        biomarker_idx += 1
        ent_id_list = []
        for f in ent_id_field_list:
            if row_dict[biomarker_id][f] != "":
                ent_id_list.append(row_dict[biomarker_id][f])
        entity_idx = 0
        for ent_id in ent_id_list:
            entity_idx += 1
            newrow = [str(biomarker_idx), str(component_idx), str(entity_idx)]
            for f in f_list_two[3:]:
                val = row_dict[biomarker_id][f] if f in row_dict[biomarker_id] else ""
                if f == "assessed_biomarker_entity_id":
                    val = ent_id
                if f == "assessed_entity_type" and ent_id.find("UPKB:") != -1:
                    val = "protein"
                if f == "biomarker_controlled_vocab":
                    val = row_dict[biomarker_id]["biomarker"]
                newrow.append(val)
            print ("\t".join(newrow))
                
    return


if __name__ == '__main__':
    main()
 
            


