#ser="prd"
#ser="beta"
#ser="tst"
ser="dev"

ver="3.1.1"
#colls="c_stat,c_searchinit,c_ontology,c_idtrack,c_index,c_list,c_biomarker,c_sort"
colls="c_biomarker"

python3 populate_collection.py  -s $ser -v $ver -c $colls



