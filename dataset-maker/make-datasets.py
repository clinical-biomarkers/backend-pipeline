import os,sys
import json
import glob
import numpy as np
import datetime
from optparse import OptionParser
import csvutil




def load_geneid2uniprotac():

    tmp_dict = {}
    in_file = downloads_dir + "glygen/current/human_protein_xref_geneid.csv"
    with open(in_file, "r") as FR:
        f_list, lcount = [], 0
        for line in FR:
            lcount += 1
            row = line[1:-2].strip().split("\",\"")
            if lcount == 1:
                f_list = row
            else:
                ac = row[f_list.index("uniprotkb_canonical_ac")].split("-")[0]
                gene_id = row[f_list.index("xref_id")]
                if gene_id not in tmp_dict:
                    tmp_dict[gene_id] = {}
                tmp_dict[gene_id][ac] = True

    return tmp_dict


def load_geneinfo(in_file):

    ac2genename, ac2geneid = {}, {}
    with open(in_file, "r") as FR:
        for line in FR:
            if line.find("Gene_Name") == -1 and line.find("GeneID") == -1:
                continue
            row = line.strip().split("\t")
            if line.find("Gene_Name") != -1:
                ac, gene_name = row[0], row[2]
                if ac not in ac2genename:
                    ac2genename[ac] = {}
                ac2genename[ac][gene_name] = True
            if line.find("GeneID") != -1:
                ac, gene_id = row[0], row[2]
                if ac not in ac2geneid:
                    ac2geneid[ac] = {}
                ac2geneid[ac][gene_id] = True

    genename2geneid = {}
    for ac in ac2genename:
        if ac not in ac2geneid:
            continue
        for gene_name in ac2genename[ac]:
            for gene_id in ac2geneid[ac]:
                if gene_name not in genename2geneid:
                    genename2geneid[gene_name] = {}
                genename2geneid[gene_name][gene_id] = True

    return ac2genename, genename2geneid






def load_cmb2id():

    cmb2id = {}
    file_list = glob.glob(release_dir + "misc/cmb2biomarkerid.*-*.csv")
    for in_file in file_list:
        with open(in_file, "r") as FR:
            f_list, lcount = [], 0
            for line in FR:
                lcount += 1
                row = line[1:-2].strip().split("\",\"")
                if lcount == 1:
                    f_list = row
                else:
                    biomarker_id = row[f_list.index("biomarker_id")]
                    biomarker = row[f_list.index("biomarker")]
                    biomarker_controlled_vocab = row[f_list.index("biomarker_controlled_vocab")]
                    entity_id = row[f_list.index("entity_id")]
                    condition_id = row[f_list.index("condition_id")]
                    cmb = "%s|%s|%s" % (entity_id,condition_id,biomarker_controlled_vocab)
                    cmb = cmb.lower()
                    if cmb not in cmb2id:
                        cmb2id[cmb] = {}
                    cmb2id[cmb][biomarker_id] = True

    return cmb2id



def make_masterlist_ds(dataset):

    conditionid2loincid = {}
    cmb2id = load_cmb2id()


    row_list = []
    newrow = ["biomarker_id","biomarker","biomarker_orig","assessed_biomarker_entity","assessed_biomarker_entity_id"]
    newrow += ["assessed_entity_type","condition","condition_id","exposure_agent","exposure_agent_id"]
    newrow += ["best_biomarker_role","specimen","specimen_id","loinc_code","evidence_source","evidence"]
    newrow += ["tag","data_source","flag"]
    row_list.append(newrow)
    file_list = glob.glob(release_dir + "unreviewed/biomarkers_*.tsv")
    for in_file in file_list:
        data_source = in_file.split("/")[-1].split(".")[0].replace("biomarkers_", "")
        df = {}
        csvutil.load_sheet(df, in_file, [], "\t")
        f_list = df["fields"]
        for row in df["data"]:
            assessed_biomarker_entity_id = row[f_list.index("assessed_biomarker_entity_id")]
            biomarker_orig = row[f_list.index("biomarker")]
            biomarker = row[f_list.index("biomarker_controlled_vocab")]
            assessed_biomarker_entity = row[f_list.index("assessed_biomarker_entity")]
            assessed_entity_type = row[f_list.index("assessed_entity_type")]
            condition = row[f_list.index("condition")]
            condition_id = row[f_list.index("condition_id")]
            exposure_agent = row[f_list.index("exposure_agent")] 
            exposure_agent_id = row[f_list.index("exposure_agent_id")]
            best_biomarker_role = row[f_list.index("best_biomarker_role")]
            specimen = row[f_list.index("specimen")]
            specimen_id = row[f_list.index("specimen_id")]
            loinc_code = row[f_list.index("loinc_code")]
            evidence_source = row[f_list.index("evidence_source")]
            evidence = row[f_list.index("evidence")]
            tag = row[f_list.index("tag")]

            cmb = "%s|%s|%s" % (assessed_biomarker_entity_id, condition_id, biomarker)
            cmb_lc = cmb.lower()
            biomarker_id_list = ["NO_BIOMARKER_ID"]
            if cmb_lc in cmb2id:
                biomarker_id_list = list(cmb2id[cmb_lc].keys())
            biomarker_id = ";".join(biomarker_id_list)
            flag = "one2many" if len(biomarker_id_list) > 1 else "one2one"
            newrow = [biomarker_id,biomarker,biomarker_orig,assessed_biomarker_entity,assessed_biomarker_entity_id]
            newrow += [assessed_entity_type, condition, condition_id,exposure_agent,exposure_agent_id]
            newrow += [best_biomarker_role,specimen,specimen_id,loinc_code,evidence_source,evidence,tag]
            newrow += [data_source,flag]
            row_list.append(newrow)
   
    file_format = "tsv"
    out_file = release_dir + "unreviewed/%s.%s" % (dataset, file_format)
    write_output(row_list, out_file, file_format)
 
    return


def make_xrefmap_biomarkerkb2uniprotkb_ds(dataset):

    geneid2uniprotac = load_geneid2uniprotac()
    
    cmb2id = load_cmb2id()
    seen_row = {}
    row_list = []
    newrow = ["uniprotkb_primary_accession","biomarkerkb_id","biomarker","disease"]
    row_list.append(newrow)
    file_list = glob.glob(release_dir + "unreviewed/biomarkers_*.tsv")
    for in_file in file_list:
        data_source = in_file.split("/")[-1].split(".")[0].replace("biomarkers_", "")
        df = {}
        csvutil.load_sheet(df, in_file, [], "\t")
        f_list = df["fields"]
        for row in df["data"]:
            assessed_biomarker_entity_id = row[f_list.index("assessed_biomarker_entity_id")]
            biomarker = row[f_list.index("biomarker_controlled_vocab")]
            assessed_biomarker_entity = row[f_list.index("assessed_biomarker_entity")]
            assessed_entity_type = row[f_list.index("assessed_entity_type")]
            condition = row[f_list.index("condition")]
            condition_id = row[f_list.index("condition_id")]
   
            prefix = assessed_biomarker_entity_id.split(":")[0].upper()
            if prefix not in ["UPKB", "NCBI"]:
                continue
            if biomarker.find("biomarker_term_in_review") != -1:
                continue
            ent_id = assessed_biomarker_entity_id.split(":")[1]
            uniprot_ac_list = []
            if prefix == "UPKB":
                uniprot_ac_list = [ent_id]
            elif prefix == "NCBI":
                if ent_id in geneid2uniprotac:
                    uniprot_ac_list = list(geneid2uniprotac[ent_id].keys())
            if uniprot_ac_list == []:
                continue
 
            cmb = "%s|%s|%s" % (assessed_biomarker_entity_id, condition_id, biomarker)
            cmb_lc = cmb.lower()
            
            biomarker_id_list = []
            if cmb_lc in cmb2id:
                biomarker_id_list = list(cmb2id[cmb_lc].keys())
            if biomarker_id_list == []:
                continue

            for biomarker_id in biomarker_id_list:
                for uniprot_ac in uniprot_ac_list:
                    newrow = [uniprot_ac,biomarker_id, biomarker, condition]
                    row_str = json.dumps(newrow)
                    if row_str not in seen_row:
                        row_list.append(newrow)
                        seen_row[row_str] = True
            

    file_format = "tsv"
    out_file = release_dir + "unreviewed/%s.%s" % (dataset, file_format)
    write_output(row_list, out_file, file_format)
    

    return



 



def get_gene_name(entity_id, entity_type, entity, ac2genename, genename2geneid):

    gene_name = ""
    if entity_type == "gene":
        gene_name = entity
    elif entity_type == "protein" or entity_id.find("UPKB:") != -1:
        ac = entity_id.split(":")[1]
        gene_name_list = list(ac2genename[ac].keys()) if ac in ac2genename else []
        gene_name = gene_name_list[0] if gene_name_list != [] else gene_name
    if gene_name == "" and entity != "":
        gene_name = entity[0].lower() + entity[1:]

    gene_id = ""
    if gene_name in genename2geneid:
        gene_id_list = list(genename2geneid[gene_name].keys())
        gene_id = gene_id_list[0]

    return gene_name, gene_id


def get_entity_type_list():
    tmp_list = []
    in_file = generated_dir + "misc/biomarker_controlled_vocabulary/current/biomarker_entity_type.txt"
    with open(in_file, "r") as FR:
        for line in FR:
            if line[0:2] == "ID":
                tmp_list.append(line[3:].strip())
    return tmp_list



def get_vocab_term(biomarker_orig, vocab_ptrn, entity, entity_id, entity_type, ac2genename, genename2geneid): 
    conn_dict = {
        "expression": "of",
        "level": "of",
        "activity": "of",
        "sequence variation": "in", 
        "methylation": "in"
    }
    change_type,aspect_type,mod_type = vocab_ptrn.split("|")
    status = False
    gene_name, gene_id = get_gene_name(entity_id, entity_type, entity, ac2genename,genename2geneid)

              
    mutation_term_list = csvutil.get_mutation_term_list()

    #print ("1111-0|%s|%s|%s|%s" % (biomarker_orig, change_type,aspect_type,mod_type))
    if gene_name != "" and change_type != "not_specified" and aspect_type != "not_specified":
        #print ("1111-1|%s|%s|%s" % (biomarker_orig, change_type, mod_type))
        if aspect_type in conn_dict:
            conn = conn_dict[aspect_type]
            c_vocab = "%s %s %s %s %s/%s" 
            c_vocab = c_vocab % (change_type, aspect_type,conn,entity_type, gene_name, entity_id)
            c_vocab = c_vocab[0].upper() + c_vocab[1:]
            status = True
    elif gene_name != "" and change_type != "not_specified" and mod_type != "not_specified":
        #print ("1111-3|%s|%s|%s" % (biomarker_orig, change_type, mod_type))
        if mod_type in conn_dict:
            mut_w_flag, mut_w = csvutil.has_mutation_word(biomarker_orig)
            #print ("1111-4|%s|%s|%s" % (biomarker_orig, mut_w, mut_w_flag))
            if entity_id.find("dbSNP") != -1:
                c_vocab = "Presence of %s sequence variation in %s %s/NCBI:%s" 
                c_vocab = c_vocab % (entity_id,entity_type,gene_name,gene_id)
                c_vocab = c_vocab[0].upper() + c_vocab[1:]
                status = True
                #print ("SSS-1|%s|%s" % (biomarker_orig, c_vocab))
            elif mod_type == "sequence variation":
                if mut_w_flag:
                    mut_id = mut_w
                    c_vocab = "Presence of bmkb_I::%s sequence variation in %s %s/NCBI:%s"
                    c_vocab = c_vocab % (mut_id,entity_type,gene_name,gene_id)
                    c_vocab = c_vocab[0].upper() + c_vocab[1:]
                    status = True
                    #print ("SSS-2|%s|%s" % (biomarker_orig, c_vocab))
                else:
                    tmp_flag = False
                    kw_match_list = []
                    for kw in mutation_term_list:
                        if biomarker_orig.lower().find(kw) != -1:
                            tmp_flag = True
                            kw_match_list.append(kw.lower())
                    if tmp_flag:
                        w_list = []
                        for w in biomarker_orig.split(" "):
                            if w.lower() not in [gene_name.lower()]:
                                w_list.append(w.lower())
                        mut_id = ":".join(w_list)
                        c_vocab = "Presence of bmkb_II::%s sequence variation in %s %s/NCBI:%s"
                        c_vocab = c_vocab % (mut_id,entity_type,gene_name,gene_id)
                        c_vocab = c_vocab[0].upper() + c_vocab[1:]
                        status = True
                        #print ("SSS-3|%s|%s" % (biomarker_orig, c_vocab))
            elif mod_type == "methylation":
                c_vocab = "%s methylation of %s %s/%s"
                c_vocab = c_vocab % (change_type,entity_type,gene_name,entity_id)
                c_vocab = c_vocab[0].upper() + c_vocab[1:]
                status = True
                #print ("MMM-1|%s|%s" % (biomarker_orig, c_vocab))
            elif mod_type == "expression":
                xx = 1
                #print ("EEE-1|%s|%s" % (biomarker_orig, c_vocab))
            
    if status == False:
        c_vocab = biomarker_orig + " [biomarker_term_in_review]"




    return c_vocab




 


def make_biomarker_ds(dataset):

    #cmb2grpid = csvutil.load_cmb2grpid(release_dir)
    ptrn_dict = json.load(open("conf/rules.json"))
    resource = dataset.replace("biomarkers_", "")
    entity_type_list = get_entity_type_list()
    entity_type_map = json.load(open(release_dir + "misc/entity_type_map.json"))
        

    ignore_field_list = ["pmid", "idx"]

    out_rows, fl_rows = [], []
    for in_file_name in ds_dict["biomarkers"][dataset]:
        in_file = downloads_dir  + "%s/current/%s" % (resource, in_file_name)
        if os.path.isfile(in_file) == False:
            print ("input file %s does not exist" % (in_file))
            exit()
        remove_index = -1
        with open(in_file, "r") as FR:
            file_name = in_file.split("/")[-1]
            lcount = 0
            f_list = []
            for line in FR:
                lcount += 1
                if lcount == 1:
                    line = line.replace("assesed_biomarker_entity", "assessed_biomarker_entity")
                    row = line.replace("\n", "").replace("\"", "\'").split("\t")
                    fl_rows.append(row + ["failure_flags"])
                    f_list = row
                    if out_rows == []:
                        newrow = []
                        for f in f_list:
                            if f not in ignore_field_list:
                                newrow.append(f)
                        out_rows.append(newrow + ["biomarker_controlled_vocab"])
                else:
                    tmp_row = line.replace("\n", "").replace("\"", "\'").split("\t")
                    row = tmp_row
                    entity_id = row[f_list.index("assessed_biomarker_entity_id")]
                    entity_type = row[f_list.index("assessed_entity_type")]
                    condition_id = row[f_list.index("condition_id")]
                    agent_id = row[f_list.index("exposure_agent_id")] if "exposure_agent_id" in f_list else ""
                    evidence_source = row[f_list.index("evidence_source")]    
                    biomarker = row[f_list.index("biomarker")] if "biomarker" in f_list else ""
                    biomarker_controlled_vocab = ""
                    if "biomarker_controlled_vocab" in f_list:
                        biomarker_controlled_vocab = row[f_list.index("biomarker_controlled_vocab")]
                    biomarker_id = row[f_list.index("biomarker_id")] if "biomarker_id" in f_list else ""
                    ff = evidence_source in ["", ":"]
                    raw_flag_list = []
                    if ff:
                        raw_flag_list.append("empty_evidence_source")
                    if entity_id == "":
                        raw_flag_list.append("empty_entity_id")
                    e_type_list = []
                    if entity_type in entity_type_list:
                        e_type_list = [entity_type]
                    elif entity_type in entity_type_map:
                        e_type_list = entity_type_map[entity_type]
                    if agent_id.find("<utils.data_types.json_types") != -1:
                        agent_id = ""
                    
                    vocab_ptrn, flag_list = "", ["already_mapped"]
                    if biomarker_controlled_vocab == "":
                        vocab_ptrn, flag_list = csvutil.get_vocab_pattern(entity_id,biomarker, ptrn_dict,e_type_list)
                    newrow = []
                    for f in f_list:
                        if f not in ignore_field_list: 
                            newrow.append(row[f_list.index(f)])
                    if raw_flag_list == []:
                        out_rows.append(newrow + ["not_mapped"])
                    else:
                        fl_rows.append(row + [";".join(raw_flag_list)])

    typo_dict = {
        "NRAS (Q61)":"NRAS Q61",
        "FLT3-ITD":"FLT3 ITD",
        "FLT3 (D835)":"FLT3 D835"    
    }

    compiled_rules = json.load(open("conf/rules_compiled.json"))

    f_list = out_rows[0]
    for i in range(1, len(out_rows)):
        biomarker_orig = out_rows[i][f_list.index("biomarker")] if "biomarker" in f_list else ""
        for w in typo_dict:
            biomarker_orig = biomarker_orig.replace(w, typo_dict[w])
        #print (biomarker_orig)
        #vocab_ptrn = out_rows[i][f_list.index("vocab_pattern")]
        entity = out_rows[i][f_list.index("assessed_biomarker_entity")]
        entity_id = out_rows[i][f_list.index("assessed_biomarker_entity_id")]
        entity_type = out_rows[i][f_list.index("assessed_entity_type")]
        change_type = out_rows[i][f_list.index("change_type_vocab")]
        aspect_type = out_rows[i][f_list.index("aspect_type_vocab")]
        mod_type = out_rows[i][f_list.index("mod_type_vocab")]
        
        vocab_ptrn = "%s|%s|%s" % (change_type, aspect_type, mod_type)
        c_vocab = get_vocab_term(biomarker_orig, vocab_ptrn, entity, entity_id, entity_type, ac2genename,genename2geneid)
        if biomarker_orig in compiled_rules:
            c_vocab = compiled_rules[biomarker_orig]
        c_vocab = c_vocab.replace("Presense of","Presence of")
        out_rows[i][f_list.index("biomarker_controlled_vocab")] = c_vocab
        #out_rows[i][f_list.index("biomarker_controlled_vocab")] = "%s [biomarker_term_in_review]" % (biomarker_orig)


    for i in range(0, len(out_rows)):
        if len(out_rows[i]) != len(out_rows[0]):
            print ("output file has QC problem")
            exit()

    file_format = "tsv"
    out_file = release_dir + "unreviewed/%s.%s" % (dataset, file_format)
    write_output(out_rows, out_file, file_format)

    log_file = release_dir + "logs/%s.csv" % (dataset)
    write_output(fl_rows,log_file, file_format)
 

    return

    
def write_output(out_rows, out_file, file_format):

    sep = "\",\"" if file_format == "csv" else "\t"
    if len(out_rows) > 1:
        FW = open(out_file, "w")
        seen = {}
        for newrow in out_rows:
            s = json.dumps(newrow)
            if s not in seen:
                if file_format == "csv":
                    FW.write("\"%s\"\n" % (sep.join(newrow)))
                else:
                    FW.write("%s\n" % (sep.join(newrow)))
                seen[s] = True
        FW.close()

            
    return


def load_entityname2id():

    tmp_dict = {}
    file_list = glob.glob(release_dir + "unreviewed/biomarkers_*.csv")
    for in_file in file_list:
        if in_file.find("clinvar") != -1:
            continue
        df = {}
        csvutil.load_sheet(df, in_file, [], ",")
        f_list = df["fields"]
        for row in df["data"]:
            ent_id = row[f_list.index("assessed_biomarker_entity_id")]
            ent_name = row[f_list.index("assessed_biomarker_entity")]
            ent_name_lc = ent_name.lower()
            if ent_name_lc not in tmp_dict:
                tmp_dict[ent_name_lc] = {}
            tmp_dict[ent_name_lc][ent_id] = ent_name


    in_file = release_dir + "compiled/entity_name2id_map.csv"
    df = {}
    csvutil.load_sheet(df, in_file, [], ",")
    f_list = df["fields"]
    for row in df["data"]:
        ent_name_src = row[f_list.index("entity_name_src")]
        ent_id = row[f_list.index("entity_id")]
        ent_name = row[f_list.index("entity_name")]
        ent_name_src_lc = ent_name_src.lower()
        if ent_name_src_lc not in tmp_dict:
                tmp_dict[ent_name_src_lc] = {}
        tmp_dict[ent_name_src_lc][ent_id] = ent_name


    return tmp_dict

def get_seen_comp_key(cmb_list):

    ignore_list = ["CSF", "CA-125"] 
    in_file = release_dir + "compiled/entity2ehr_mapping_gwdc.2.csv"
    df = {}
    csvutil.load_sheet(df, in_file, [], ",")
    f_list = df["fields"]
    for row in df["data"]:
        status = row[f_list.index("status")]
        entity_name = row[f_list.index("entity_term")]
        lab_term = row[f_list.index("lab_term")]
        comment = row[f_list.index("comment")]
        if status == "not valid" and comment == "":
            if entity_name not in ignore_list:
                ignore_list.append(entity_name)
    seen_comp_key = {}
    in_file = downloads_dir + "gwdc/current/stats.csv"
    df = {}
    csvutil.load_sheet(df, in_file, [], ",")
    f_list = df["fields"]
    for row in df["data"]:
        comp_key = row[f_list.index("comp_key")]
        entity_name = row[f_list.index("entity_name")]
        comp_name = row[f_list.index("comp_name")]
        count = row[f_list.index("count")]
        if len(entity_name) < 3 or entity_name in ignore_list:
            continue
        if int(count) < 10:
            continue
        seen_comp_key[comp_key] = True

    return seen_comp_key


def get_age_group(age,age_group_list):

    for g in age_group_list:
        if g == "all":
            continue
        g = "90_1000" if g == "90+" else g
        s, e = g.split("_")
        if int(age) >= int(s) and int(age) <= int(e):
            return g
    return "unknown"


def remove_outliers(tmp_m_list):

    # this parameter controls outlier trim level
    # set to 10% now
    TRIM_LEVEL = 0.1

    m_list = []
    tmp_m_list = sorted(tmp_m_list)
    n = len(tmp_m_list)
    offset = int(TRIM_LEVEL*n)
    m_list = tmp_m_list[offset:n-offset]

    return m_list

def make_entity_normalranges_ds(dataset):


    if dataset == "entity_normalranges_gwdc":
        age_group_list = ["0_19","20_29","30_39","40_49","50_59","60_69","70_79","80_89","90+","all"]
        cmb_list = []
        for sex in ["male","female", "all"]:
            for age_group in age_group_list:
                cmb = "%s_%s" % (sex, age_group)
                cmb_list.append(cmb)
        out_rows, fl_rows = [], []
       
        newrow = ["entity_id","entity_name","entity_id_src","entity_name_src","entity_type"]
        newrow += ["age_group","sex","min_val","max_val","mean_val","median_val","sd_val","q1","q3"]
        newrow += ["iqr", "lower_whisker", "upper_whisker", "n_val","units"]
        out_rows.append(newrow)
   
        seen_comp_key = get_seen_comp_key(cmb_list)
        file_list = glob.glob(downloads_dir + "gwdc/current/measurements.*.csv")
        # "DurableKey_e","Sex","AgeInYears","IsCancerPatient","lab_comp_key","comp_name","entity",
        # "entity_ids","Value","NumericValue","Unit","Abnormal","IsFinal","Count"
        m_dict = {}
        for in_file in file_list:
            df = {}
            csvutil.load_sheet(df, in_file, [], ",")
            f_list = df["fields"]
            for row in df["data"]:
                comp_key = row[f_list.index("lab_comp_key")]
                comp_name = row[f_list.index("comp_name")]
                entity_name = row[f_list.index("entity")]
                entity_ids = row[f_list.index("entity_ids")]
                unit = row[f_list.index("Unit")]
                unit = "unknown" if unit == "nan" else unit
                sex = row[f_list.index("Sex")]
                age = row[f_list.index("AgeInYears")]
                m_value = row[f_list.index("NumericValue")]
                age_group = get_age_group(age,age_group_list)
                has_cancer = float(row[f_list.index("IsCancerPatient")]) == 1.0
                if sex.lower() not in ["male","female"]:
                    continue
                if m_value == "nan":
                    continue
                if has_cancer:
                    continue
                if comp_key not in seen_comp_key:
                    continue
                entity_id_list = []
                for e in entity_ids.split(";"):
                    entity_id_list.append(e.split(">")[0])
                cmb = "%s_%s" % (sex.lower(), age_group)
                
                if comp_key not in m_dict:
                    m_dict[comp_key] = {
                        "comp_name":comp_name, "entity_name":entity_name, "unit":unit,
                        "entityidlist":entity_id_list,
                        "valdict":{}
                    }
                if cmb not in m_dict[comp_key]["valdict"]:
                    m_dict[comp_key]["valdict"][cmb] = []
                m_dict[comp_key]["valdict"][cmb].append(float(m_value))
        for comp_key in m_dict:
            entity_name_src, entity_name = m_dict[comp_key]["comp_name"],m_dict[comp_key]["entity_name"]
            unit = m_dict[comp_key]["unit"]
            entity_id_list = m_dict[comp_key]["entityidlist"]
            for cmb in m_dict[comp_key]["valdict"]:
                tmp_m_list = m_dict[comp_key]["valdict"][cmb]
                if len(tmp_m_list) < 10:
                    continue
                m_list = remove_outliers(tmp_m_list)
                n = len(m_list)
                if n < 10:
                    continue
                mn, mx = str(np.min(m_list)), str(np.max(m_list))
                mean = str(round(np.mean(m_list), 3))
                median = str(round(np.median(m_list), 3))
                sd = str(round(np.std(m_list), 3))
                quartiles = np.quantile(m_list, [0.25, 0.5, 0.75, 1.0])
                q1, q3 = round(quartiles[0], 4), round(quartiles[2], 4)
                iqr = round(q3 - q1, 4)
                lower_whisker = round(q1 - 1.5*iqr, 4)
                upper_whisker = round(q3 + 1.5*iqr, 4)
                q1, q3 = str(q1), str(q3)
                iqr, lower_whisker, upper_whisker = str(iqr), str(lower_whisker), str(upper_whisker)

                sex = cmb.split("_")[0]
                age_group = "90+" if cmb.find("+") != -1 else cmb.split("_")[1] + "-" + cmb.split("_")[2]
                age_group = "90+" if age_group == "90-1000" else age_group
                for e_id in entity_id_list:
                    entity_id_src, entity_id = e_id.split(":")
                    entity_type = "protein"
                    newrow = [entity_id,entity_name,entity_id_src,entity_name_src,entity_type]
                    newrow += [age_group,sex,mn,mx,mean,median,sd,q1,q3,iqr,lower_whisker,upper_whisker]
                    newrow += [str(n),unit]
                    out_rows.append(newrow)
    elif dataset == "entity_normalranges_oracle_health_rwd":
        #entname2id = load_entityname2id()
        entity_name_dict = json.load(open(release_dir + "misc/labterm2entityname_map.json"))
        in_file = downloads_dir +  "oracle_health/current/stratified_stats_report_ALL.tsv"
        if os.path.isfile(in_file) == False:
            print ("input file %s does not exist" % (in_file))
            exit()
        out_rows, fl_rows = [], []
        with open(in_file, "r") as FR:
            lcount = 0
            f_list = []
            for line in FR:
                lcount += 1
                row = line.replace("\n", "").replace("\"", "\'").split("\t")
                if lcount == 1:
                    f_list = row
                    newrow = ["entity_id", "entity_name","entity_id_src","entity_name_src","entity_type"]
                    newrow += ["age_group", "sex","min_val","max_val","mean_val","median_val","sd_val"]
                    newrow += ["q1", "q3","iqr", "lower_whisker", "upper_whisker","n_val", "units"]
                    out_rows.append(newrow)
                    newrow = row + [ "flags"]
                    fl_rows.append(newrow)
                else:
                    entity_id = row[f_list.index("entity_id")]
                    entity_id_src = row[f_list.index("entity_id_source")]
                    entity_name = row[f_list.index("entity_name")]
                    entity_name_src = row[f_list.index("lab")]
                    entity_type = row[f_list.index("entity_type")]
                    age_group = row[f_list.index("agegroup")]
                    sex = row[f_list.index("sex")]
                    min_val = row[f_list.index("min")]
                    max_val = row[f_list.index("max")]
                    mean_val = row[f_list.index("mean")]
                    median_val = row[f_list.index("q2_median")]
                    sd_val = row[f_list.index("sd")]
                    q1 = float(row[f_list.index("q1")])
                    q3 = float(row[f_list.index("q3")])
    
                    if entity_name_src in entity_name_dict:
                        entity_name = entity_name_dict[entity_name_src]
                    #print ("%s|%s" % (entity_name_src, entity_name)) 
                    q1, q3 = round(q1, 4), round(q3, 4)
                    iqr = round(q3 - q1, 4)
                    lower_whisker = round(q1 - 1.5*iqr, 4)
                    upper_whisker = round(q3 + 1.5*iqr, 4)
                    q1, q3 = str(q1), str(q3)
                    iqr, lower_whisker, upper_whisker = str(iqr), str(lower_whisker), str(upper_whisker)
                    n_val = row[f_list.index("n")]
                    units = row[f_list.index("units")]
                    newrow = [entity_id,entity_name,entity_id_src,entity_name_src,entity_type] 
                    newrow += [age_group,sex,min_val,max_val,mean_val,median_val,sd_val,q1,q3]
                    newrow += [iqr, lower_whisker, upper_whisker, n_val,units]	
                    out_rows.append(newrow)

                    #ent_name_src_lc = ent_name_src.lower()
                    #if ent_name_src_lc not in entname2id:
                    #    continue
                    #for ent_id in entname2id[ent_name_src_lc]:
                    #    ent_name = entname2id[ent_name_src_lc][ent_id]
                    #    newrow = [ent_id, ent_name, ent_name_src] 
                    #    newrow += [age_group, sex, mean_val, median_val, sd_val,n_val, units]
                    #    out_rows.append(newrow)

    file_format = "tsv"
    out_file = release_dir + "unreviewed/%s.%s" % (dataset,file_format)
    log_file = release_dir + "logs/%s.csv" % (dataset)
    write_output(out_rows, out_file, file_format)
    write_output(fl_rows,log_file, file_format)
 

    return

def reduce_xref_dict(xref_dict):

    remove_dict = {}   
    with open(release_dir + "misc/crossrefs-removelist.txt","r") as FR:
        for line in FR:
            src,ent_type,xref_key = line.strip().split(" ")
            ent_type = "amino acid" if ent_type == "amino_acid" else ent_type
            if src not in remove_dict:
                remove_dict[src] = {}
            if ent_type not in remove_dict[src]:
                remove_dict[src][ent_type] = {}
            remove_dict[src][ent_type][xref_key] = True
    for src in xref_dict:
        for ent_type in xref_dict[src]:
            if src in remove_dict:
                if ent_type in remove_dict[src]:
                    for xref_key in remove_dict[src][ent_type]:
                        if "assessed_biomarker_entity" in xref_dict[src][ent_type]:
                            if xref_key in xref_dict[src][ent_type]["assessed_biomarker_entity"]:
                                xref_dict[src][ent_type]["assessed_biomarker_entity"].pop(xref_key)
    return


def make_annotations_ds(dataset):

    config_file = downloads_dir + "annotations/config.json"
    config_obj = json.load(open(config_file))
     
    header_row = ["assessed_biomarker_entity_id","xref_key","xref_id","annotation_category","annotation_term"]

    seen_row = {}
    out_rows = [header_row]
    annotation_category = "protein_function"
    for file_name in config_obj:
        for f in header_row:
            if f not in config_obj[file_name]["field_map"]:
                print ("field=%s is not mapped in %s" % (f, config_file))
                exit()
        
        ent_id_prefix = config_obj[file_name]["ent_id_prefix"]
        ent_id_t, ent_id_f = config_obj[file_name]["field_map"][header_row[0]].split("|")
        xref_key_t, xref_key_f = config_obj[file_name]["field_map"][header_row[1]].split("|")
        xref_id_t, xref_id_f = config_obj[file_name]["field_map"][header_row[2]].split("|")
        cat_t, cat_f = config_obj[file_name]["field_map"][header_row[3]].split("|")
        ann_t, ann_f = config_obj[file_name]["field_map"][header_row[4]].split("|")
        
        in_file = downloads_dir + "annotations/current/" + file_name
        df = {}
        csvutil.load_sheet(df, in_file, [], ",")
        f_list = df["fields"]
        for row in df["data"]:
            ent_id_v, xref_key_v, xref_id_v, cat_v, ann_v = "", "", "", "", "" 
            
            ent_id_v = row[f_list.index(ent_id_f)] if ent_id_f in f_list else ent_id_v
            ent_id_v = ent_id_f if ent_id_t == "constant" else ent_id_v
            xref_key_v = row[f_list.index(xref_key_f)] if xref_key_f in f_list else xref_key_v
            xref_key_v = xref_key_f if xref_key_t == "constant" else xref_key_v
            xref_key_v = "" if xref_key_t == "empty" else xref_key_v            
            xref_id_v = row[f_list.index(xref_id_f)] if xref_id_f in f_list else xref_id_v
            xref_id_v = xref_id_f if xref_id_t == "constant" else xref_id_v
            xref_id_v = "" if xref_id_t == "empty" else xref_id_v  
            cat_v = row[f_list.index(cat_f)] if cat_f in f_list else cat_v
            cat_v = cat_f if cat_t == "constant" else cat_v
            cat_v = "" if cat_t == "empty" else cat_v  
            ann_v = row[f_list.index(ann_f)] if ann_f in f_list else ann_v
            ann_v = ann_f if ann_t == "constant" else ann_v
            ann_v = "" if ann_t == "empty" else ann_v  
             
            ent_id_v = ent_id_prefix + ":" +  ent_id_v
            newrow = [ent_id_v,xref_key_v,xref_id_v,cat_v, ann_v]
            newrow_str = json.dumps(newrow)
            if newrow_str not in seen_row:
                out_rows.append(newrow)
                seen_row[newrow_str] = True 

    file_format = "tsv"
    out_file = release_dir + "unreviewed/%s.%s" % (dataset, file_format)
    write_output(out_rows, out_file, file_format)
    
    return



def make_xrefs_ds(dataset):

    xref_dict = json.load(open(release_dir + "misc/crossrefs.json"))
    #reduce_xref_dict(xref_dict)

    
    seen_debug = {}
    out_rows = [["source_file","biomarker_idx","xref_key","xref_id"]]
    file_list = glob.glob(release_dir + "unreviewed/biomarkers_*.tsv")
    for in_file in file_list:
        source = in_file.split("/")[-1].replace("biomarkers_","").replace(".tsv","")
        df = {}
        csvutil.load_sheet(df, in_file, [], "\t")
        f_list = df["fields"]
        for row in df["data"]:
            ent_id = row[f_list.index("assessed_biomarker_entity_id")]
            ent_prefix = ent_id.split(":")[0].lower()
            ent_type = row[f_list.index("assessed_entity_type")]
            biomarker_idx = row[f_list.index("biomarker_index")]
            if source not in xref_dict:
                continue
            for t in xref_dict[source]:
                if ent_type != t:
                    continue
                for f in xref_dict[source][t]:
                    if f not in f_list:
                        continue
                    xref_id = row[f_list.index(f)]
                    if xref_id == "":
                        continue
                    if xref_id == ent_id:
                        xref_id = xref_id.split(":")[1]
                    for xref_key in xref_dict[source][t][f]:
                        if xref_key.find("|extra") != -1 or xref_key in ["loinc"]:
                            xref_key = xref_key.replace("|extra", "")
                            for x_id in xref_id.split(";"):
                                ignore_flag = f=="assessed_biomarker_entity" and x_id not in genename2geneid
                                newrow = [source,biomarker_idx,xref_key,x_id]
                                if ignore_flag == False:
                                    out_rows.append(newrow)
                                else:
                                    print ("\t".join(newrow))
                        elif xref_key == ent_prefix:
                            newrow = [source,biomarker_idx,xref_key,xref_id] 
                            out_rows.append(newrow)

    file_format = "tsv"
    out_file = release_dir + "unreviewed/%s.%s" % (dataset,file_format)
    write_output(out_rows, out_file, file_format)



    return



def main():

    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog " )
    parser.add_option("-r","--rel",action="store",dest="rel",help="")
    parser.add_option("-d","--dataset",action="store",dest="dataset",help="")

    (options,args) = parser.parse_args()
    for file in ([options.dataset, options.rel]):
        if not (file):
            parser.print_help()
            sys.exit(0)

    dataset = options.dataset
    rel = options.rel


    global ds_dict
    global ac2genename
    global genename2geneid
    global downloads_dir
    global generated_dir
    global release_dir

    downloads_dir = "/data/shared/biomarkerdb/downloads/"
    generated_dir = "/data/shared/biomarkerdb/generated/"
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)


    ds_dict = json.load(open(release_dir + "misc/datasets.json"))
    in_file = downloads_dir + "uniprotkb/current/HUMAN_9606_idmapping.dat"
    ac2genename, genename2geneid = load_geneinfo(in_file)
    
    
    biomarker_ds_list = ds_dict["biomarkers"]
    entity_normalranges_ds_list = ds_dict["entity_normalranges"]

    if dataset in biomarker_ds_list:
        make_biomarker_ds(dataset)
    elif dataset in entity_normalranges_ds_list:
        make_entity_normalranges_ds(dataset)
    elif dataset == "masterlist":
        make_masterlist_ds(dataset)
    elif dataset == "xrefmap_biomarkerkb2uniprotkb":
        make_xrefmap_biomarkerkb2uniprotkb_ds(dataset)
    elif dataset == "xrefs":
        make_xrefs_ds(dataset)
    elif dataset == "annotations":
        make_annotations_ds(dataset) 
     

    return 




if __name__ == '__main__':
    main()
 
