rel="3.1.1"
prev_rel="2.4.1"

#rm -f jsondb/biomarkerdb/*
#python3 make-biomarkerdb.py

rm -f jsondb/idtrackdb/*
python3 make-idtrackdb.py -r $rel -p $prev_rel

rm -f jsondb/interm/listdb/*
python3 make-listdb.py

rm -f jsondb/listdb/*
python3 update-listdb.py

rm -f jsondb/indexdb/*
python3 wrap-make-indexdb.py

rm -f jsondb/sortdb/*
python3 make-sortdb.py

rm -f jsondb/searchinitdb/*
python3 make-searchinitdb.py


rm -f jsondb/interm/statdb/*
python3 wrap-make-statdb.py
sleep 1200

rm -f jsondb/statdb/*
python3 update-statdb.py

