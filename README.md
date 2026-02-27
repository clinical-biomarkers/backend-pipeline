### Dataset Maker
#### Step-1: creating directory structure for a release 
Run the following commands to create required subdirectories for your release ( release 3.1.1 is used as an example here).

```
$ mkdir -p /../../biomarkerdb/releases/data/v-3.1.1/unreviewed
$ mkdir -p /../../biomarkerdb/releases/data/v-3.1.1/reviewed
$ mkdir -p /../../biomarkerdb/releases/data/v-3.1.1/misc
$ mkdir -p /../../biomarkerdb/releases/data/v-3.1.1/compiled
$ mkdir -p /../../biomarkerdb/releases/data/v-3.1.1/logs
```
Under the   "dataset-maker" subdirectory, create the following symbolic links 

```
$ cd dataset-maker
$ ln -s /data/shared/biomarkerdb/downloads downloads
$ 


Under the "dataset-maker" folder, create the following 

fdfdafa
compiled -> /data/shared/biomarkerdb/releases/data/v-3.1.1/compiled
downloads -> /data/shared/biomarkerdb/downloads
generated -> /data/shared/biomarkerdb/generated
logs -> /data/shared/biomarkerdb/releases/data/v-3.1.1/logs
misc -> /data/shared/biomarkerdb/releases/data/v-3.1.1/misc
reviewed -> /data/shared/biomarkerdb/releases/data/v-3.1.1/reviewed
unreviewed -> /data/shared/biomarkerdb/releases/data/v-3.1.1/unreviewed
