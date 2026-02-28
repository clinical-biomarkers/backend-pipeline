### Downloads
dfafdasfadsfads


### Dataset Maker
#### Step-1: creating directory structure for a release 
Run the following commands to create required subdirectories for your release ( release 3.1.1 is used as an example here).

```
$ mkdir -p /../../biomarkerdb/releases/data/v-3.1.1/unreviewed
$ mkdir -p /../../biomarkerdb/releases/data/v-3.1.1/reviewed
$ mkdir -p /../../biomarkerdb/releases/data/v-3.1.1/logs
```

For the "misc" and "compiled", use the following command to inherit it from the last production release $PREV_REL
```
$ cp -r /../../biomarkerdb/releases/data/v-$PREV_REL/misc /../../biomarkerdb/releases/data/v-3.1.1/
$ cp -r /../../biomarkerdb/releases/data/v-$PREV_REL/compiled /../../biomarkerdb/releases/data/v-3.1.1/
```

#### Step-2: creating dataset files
Run the following commands to create all datasets. This step depends on the file /../../biomarkerdb/releases/data/v-3.1.1/misc/datasets.json.
```
python3 wrap-make-datasets.py -r 3.1.1
```
The output datasets will be created under /../../biomarkerdb/releases/data/v-3.1.1/unreviewed/

#### Step-3: qualtity control of dataset files
Compare dataset files created above to older version files from $PREV_REL
```
python3 qc-datasets.py -r 3.1.1 -p $PREV_REL
```
The output for this step will be created under /../../biomarkerdb/releases/data/v-3.1.1/logs/qc-datasets.csv


#### Step-4: creating MongoDB objects
Run the following commands to create various JSON objects that will be loaded to MongoDB. The location of the objects creates in this record is /../../biomarkerdb/releases/data/v-3.1.1/jsondb/*db/

```
nohup python3 run-pipeline.py -r 3.1.1 -p 2.4.1 &
```
The above command will output logfile /data/shared/biomarkerdb/logs/run-pipeline.log

$ cat /data/shared/biomarkerdb/logs/run-pipeline.log
```
Started logging ...
created 203476 biomarker records under /data/shared/biomarkerdb/releases/data/v-3.1.1/jsondb/biomarkerdb/*
created 203530 idtrack records under /data/shared/biomarkerdb/releases/data/v-3.1.1/jsondb/idtrackdb/*
created 203476 list records under /data/shared/biomarkerdb/releases/data/v-3.1.1/jsondb/listdb/*
created 203476 index records under /data/shared/biomarkerdb/releases/data/v-3.1.1/jsondb/indexdb/*
created 144 sort records under /data/shared/biomarkerdb/releases/data/v-3.1.1/jsondb/sortdb/*
created 4 searchinit records under /data/shared/biomarkerdb/releases/data/v-3.1.1/jsondb/searchinitdb/*
created 1 stat records under /data/shared/biomarkerdb/releases/data/v-3.1.1/jsondb/statdb/*
updated 18 dataset files
```









