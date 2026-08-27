rel="3.1.1"
prev_rel="2.4.1"
release_dir="/data/shared/biomarkerdb/releases/data/v-$rel"

#rm -f $release_dir/jsondb/biomarkerdb/*
#python3 make-biomarkerdb.py -r $rel
#exit

rm -f $release_dir/jsondb/idtrackdb/*
python3 make-idtrackdb.py -r $rel -p $prev_rel

rm -f $release_dir/jsondb/interm/listdb/*
python3 make-listdb.py -r $rel

rm -f $release_dir/jsondb/listdb/*
python3 update-listdb.py -r $rel

rm -f $release_dir/jsondb/indexdb/*
python3 wrap-make-indexdb.py -r $rel

rm -f $release_dir/jsondb/sortdb/*
python3 make-sortdb.py -r $rel

rm -f $release_dir/jsondb/searchinitdb/*
python3 make-searchinitdb.py -r $rel

rm -f $release_dir/jsondb/interm/statdb/*
python3 wrap-make-statdb.py -r $rel

sleep 1200

rm -f $release_dir/jsondb/statdb/*
python3 update-statdb.py -r $rel


rm -f $release_dir/reviewed/*
python3 update-dataset-files.py -r $rel


