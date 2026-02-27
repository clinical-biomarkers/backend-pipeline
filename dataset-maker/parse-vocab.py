import os,sys
import json
import glob
import datetime
import csvutil
from optparse import OptionParser
import subprocess


def main():

    rel = "3.1.1"
    release_dir = "/data/shared/biomarkerdb/releases/data/v-%s/" % (rel)
    
    vocab_structure_list = [
        "{presence of} {entity_id} {sequence variation} in {gene}"
        ,"{presence of} {entity_id} {sequence variation} in {protein}"
        ,"{presence of} {sequence variation} in {gene}"
        ,"{presence of} {sequence variation} in {protein}"
        ,"{increased} {level} of {gene}"
        ,"{increased} {level} of {protein}"
        ,"{increased} {level} of {metabolite}"
        ,"{increased} {level} of {protein complex}"
        ,"{increased} {level} of {RNA}"
        ,"{increased} {level} of {glycan}"
        ,"{increased} {level} of {DNA}"
        ,"{increased} {level} of {cell}"
        ,"{increased} {level} of {amino acid}"
        ,"{increased} {level} of {chemical element}"
        ,"{increased} {level} of {lipid}"
        ,"{increased} {level} of {lipoprotein}"
        ,"{increased} {level} of {peptide}"
        ,"{increased} {level} of fucosylation on {protein}"
        ,"{increased} {level} of h3n2 on {protein}"
        ,"{increased} {level} of h5n2 on {protein}"
        ,"{increased} {level} of mannose on {protein}"
        ,"{increased} {level} of mucst on {protein}"
        ,"{increased} {level} of muct on {protein}"
        ,"{increased} {level} of neu5gc on {protein}"
        ,"{decreased} {level} of {gene}"
        ,"{decreased} {level} of {protein}"
        ,"{decreased} {level} of {metabolite}"
        ,"{decreased} {level} of {cell}"
        ,"{differential} {expression} of {gene}"
        ,"{differential} {expression} of {metabolite}"
        ,"{differential} {expression} of {RNA}"
        ,"{increased} {expression} of {gene}"
        ,"{decreased} {expression} of {gene}"
        ,"{presence of} {expression} of {gene}"
        ,"{increased} {methylation} of {gene}"
        ,"{increased} {methylation} of {miRNA}"
        ,"{increased} {expression} of exon 18 in {gene}"
        ,"{presence of} {methylation} of {gene}" 
        ,"{decreased} {activity} of {protein}"
        ,"{decreased} {level} of {chemical element}"
        ,"{decreased} {level} of {DNA}"
        ,"{decreased} {level} of {glycan}"
        ,"{decreased} {level} of {RNA}"
        ,"{presence of} {level} of {metabolite}"
        ,"{differential} {level} of {gene}"
        ,"{presence of} {activity} of {protein}"
        ,"[biomarker_term_in_review]" 
    ]


    mutation_term_list = ["mutation","deletion","fusion","insertion","rearrangement"]
  
    vocab_structure2parts = {} 
    stat_dict = {}
    for vocab_structure in vocab_structure_list:
        stat_dict[vocab_structure] = 0
    seen_disease_id = {}
    file_list = glob.glob(release_dir + "unreviewed/biomarkers_*.tsv")
    for in_file in file_list:
        source = in_file.split("/")[-1].replace("biomarkers_","").replace(".tsv","")
        with open(in_file, "r") as FR:
            f_list, lcount = [], 0
            for line in FR:
                lcount += 1
                row = line[0:-1].split("\t")
                if lcount == 1:
                    f_list = row
                else:
                    ent_id = row[f_list.index("assessed_biomarker_entity_id")]
                    condition_id = row[f_list.index("condition_id")]
                    ent_type = row[f_list.index("assessed_entity_type")]
                    vocab = row[f_list.index("biomarker_controlled_vocab")]
                    biomarker = row[f_list.index("biomarker")]
                    vocab_parts = row[f_list.index("vocab_pattern")]
                    r = vocab.lower().replace(ent_type.lower(), "{%s}" % (ent_type))
                    r = r.replace(ent_id.lower(), "{entity_id}")
                    for att in vocab_parts.split(";"):
                        if att.strip()  == "":
                            continue
                        f, v = att.split(":")
                        r = r.replace(v.lower(),"{%s}"%(v)).strip()
                    if r.find("bmkb_i") != -1:
                        w_list = []
                        for w in r.split(" "):
                            if w.find(">") == -1 and w.find(")") == -1:
                                w_list.append("{entity_id}" if w.find("bmkb_i") != -1 else w)
                        r = " ".join(w_list) 
                    cmb = "%s|%s" % (r,vocab)
                    flag = False
                    for vocab_structure in vocab_structure_list:
                        if r.find(vocab_structure) != -1:
                            stat_dict[vocab_structure] += 1
                            flag = True
                            if vocab_parts == "":
                                vocab_parts = "change_type:not_specified;aspect_type:not_specified"
                            if vocab_structure not in vocab_structure2parts:
                                vocab_structure2parts[vocab_structure] = {}
                            vocab_structure2parts[vocab_structure][vocab_parts] = True
                    if flag == False:
                        print (cmb)


    #for vocab_structure in vocab_structure2parts:
    #    n = len(vocab_structure2parts[vocab_structure].keys())
    #    for vocab_parts in vocab_structure2parts[vocab_structure]:
    #        print ("%s|%s" % (vocab_structure,vocab_parts))

 
    total = 0
    for vocab_structure in stat_dict:
        if stat_dict[vocab_structure] == 0:
            continue
        n = stat_dict[vocab_structure]
        total += n
        vocab_parts_list = []
        if vocab_structure in vocab_structure2parts:
            vocab_parts_list = list(vocab_structure2parts[vocab_structure].keys())
        if len(vocab_parts_list) > 1:
            print ("Error")
            exit()
        row = [str(n),vocab_parts_list[0], vocab_structure]
        print (",".join(row)) 
    #print (total, "total")

 
    return 




if __name__ == '__main__':
    main()
 
