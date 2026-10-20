#ser="prd"
ser="dev"

ver="3.6.0"
#colls="c_stat,c_searchinit,c_ontology,c_idtrack,c_index,c_list,c_biomarker,c_sort"
#colls="c_ent,c_index,c_sort,c_idtrack,c_stat,c_searchinit,c_ontology"
colls="c_batch"

python3 populate_collection.py  -s $ser -v $ver -c $colls



