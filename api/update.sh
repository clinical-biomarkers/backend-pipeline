ser="prd"
#ser="dev"
rel="3.5.2"

#python3 populate_collection.py -s $ser -v $rel
python3 wrap-update-initcache.py -s $ser
python3 wrap-update-initlistcache.py -s $ser



