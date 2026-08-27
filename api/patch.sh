ser="prd"
#ser="dev"

ver="3.2.2"
#colls="c_stat,c_searchinit,c_ontology,c_idtrack,c_index,c_list,c_biomarker,c_sort"
colls="c_searchinit"

python3 populate_collection.py  -s $ser -v $ver -c $colls



