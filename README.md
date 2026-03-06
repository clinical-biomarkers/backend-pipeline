### Step-1: downloading raw input files
The is coming soon ...


### Step-2: creating directory structure for a release 
Run the following commands to create required subdirectories for your release ( release 3.1.1 is used as an example here).
```
$ cd /../shared/repos/backend-pipeline/dataset-maker/
$ mkdir -p /../shared/biomarkerdb/releases/data/v-3.1.1/unreviewed
$ mkdir -p /../shared/biomarkerdb/releases/data/v-3.1.1/reviewed
$ mkdir -p /../shared/biomarkerdb/releases/data/v-3.1.1/logs
```

For the "misc" and "compiled", use the following command to inherit it from the last production release $PREV_REL
```
$ cp -r /../shared/biomarkerdb/releases/data/v-$PREV_REL/misc /../shared/biomarkerdb/releases/data/v-3.1.1/
$ cp -r /../shared/biomarkerdb/releases/data/v-$PREV_REL/compiled /../shared/biomarkerdb/releases/data/v-3.1.1/
```

### Step-3: creating dataset files
Run the following commands to create all datasets. This step depends on the file /../shared/biomarkerdb/releases/data/v-3.1.1/misc/datasets.json.
```
$ cd /../shared/repos/backend-pipeline/dataset-maker/
$ python3 wrap-make-datasets.py -r 3.1.1
```
The output datasets will be created under /../shared/biomarkerdb/releases/data/v-3.1.1/unreviewed/

### Step-4: qualtity control of dataset files
Compare dataset files created above to older version files from $PREV_REL
```
$ cd /../shared/repos/backend-pipeline/dataset-maker/
$ python3 qc-datasets.py -r 3.1.1 -p $PREV_REL
```
The output for this step will be created under /../shared/biomarkerdb/releases/data/v-3.1.1/logs/qc-datasets.csv


### Step-5: creating MongoDB objects
Run the following commands to create various JSON objects that will be loaded to MongoDB. The location of the objects creates in this record is /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/*db/

```
$ cd /../shared/repos/backend-pipeline/object-maker/
$ nohup python3 run-pipeline.py -r 3.1.1 -p 2.4.1 &
```
The above command will output logfile /data/shared/biomarkerdb/logs/run-pipeline.log

$ cat /../shared/biomarkerdb/logs/run-pipeline.log
```
Started logging ...
created 203476 biomarker records under /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/biomarkerdb/*
created 203530 idtrack records under /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/idtrackdb/*
created 203476 list records under /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/listdb/*
created 203476 index records under /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/indexdb/*
created 144 sort records under /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/sortdb/*
created 4 searchinit records under /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/searchinitdb/*
created 1 stat records under /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/statdb/*
updated 18 dataset files under /../shared/biomarkerdb/releases/data/v-3.1.1/reviewed/*
```

### Step-6: loading MongoDB objects
Run the following commands to load objectst to MongoDB.
```
$ cd /../shared/repos/backend-pipeline/api/
$ nohup python3 populate_collection.py -s $SERVER -v 3.1.1  &
```
where $SERVER can be dev or prd. You can monitor the progress of the above command by looking into the logfiles /data/shared/biomarkerdb/logs/*_loading_progress_dev|prd.txt

$ ls /../shared/biomarkerdb/logs/*_loading_progress_dev.txt
```
$ ls  -ltr /data/shared/biomarkerdb/logs/*_loading_progress_dev.txt
-rw-rw-r--. 1 rykahsay biomarkerkb   466 Mar  1 14:46 /../shared/biomarkerdb/logs/c_init_loading_progress_dev.txt
-rw-rw-r--. 1 rykahsay biomarkerkb 17799 Mar  1 14:49 /../shared/biomarkerdb/logs/c_biomarker_loading_progress_dev.txt
-rw-rw-r--. 1 rykahsay biomarkerkb 15573 Mar  1 14:50 /../shared/biomarkerdb/logs/c_list_loading_progress_dev.txt
-rw-rw-r--. 1 rykahsay biomarkerkb   429 Mar  1 14:51 /../shared/biomarkerdb/logs/c_index_loading_progress_dev.txt
```


### Step-7: updating init caches
Run the following commands to update init caches -- they are used when users perform empty query searches that result in large number of results
```
$ cd /../shared/repos/backend-pipeline/api/
$ nohup python3 wrap-update-initcache.py -s $SERVER &
```
After the above command finishes, you will see file /../shared/biomarkerdb/logs/c_initcache.biomarker_all.$SERVER.log containing 1 line. Next, you do the following:
```
$ cd /../shared/repos/backend-pipeline/api/
$ nohup python3 wrap-update-initlistcache.py -s $SERVER &
```
Check the logfile  /../shared/biomarkerdb/logs/c_initlistcache.biomarker_all.$SERVER.log and you should see 9 lines in it.


### Step-8: updating version label for data 
Run the following commands to update version label data 
```
$ cd /../shared/repos/backend-pipeline/api/
$ python3 update_version.py -s $SERVER -v 3.1.1 -c data
```






