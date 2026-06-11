## Data release pipeline
### Step-1: downloading raw input files
This is coming soon ...

Make sure any new input files have the column `component_group` after `assessed_biomarker_entity_id`. This field is important -- it tells the pipeline how the `assessed_biomarker_entity_id` should be grouped to create a biomarker record. Example:
```
$ head microplastics.tsv
biomarker_id    biomarker       assessed_biomarker_entity       assessed_biomarker_entity_id    component_group assessed_entity_type    condition       condition_id    exposure_agent  exposure_agent_id       best_biomarker_role      specimen        specimen_id     loinc_code      evidence_source evidence        tag     biomarker_controlled_vocab
        Presence of Polystyrene microplastics   Polystyrene     CHEBI:53276     1       metabolite                      Polystyrene     CHEBI:53276     monitoring      placenta        UBERON:000198           PubMed:38366932  "Py-GC-MS revealed that microplastics were present in all participants’ placentae, with concentrations ranging widely from 6.5 to 685mg NMPs per gram of placental tissue, averaging 126.8±147.5mg/g (mean±SD)"  assessed_biomarker_entity;assessed_biomarker_entity_id;assessed_entity_type;best_biomarker_role;biomarker;exposure_agent;exposure_agent_id;specimen;specimen_id;evidence_source;evidence
        Presence of Polystyrene microplastics   Polystyrene     CHEBI:53276     2       metabolite                      Polystyrene     CHEBI:53276     monitoring      kidney  UBERON:0002113          PubMed:33956507  "PS-MPs were evaluated in human kidney proximal tubular epithelial cells (HK-2 cells) and male C57BL/6 mice"    assessed_biomarker_entity;assessed_biomarker_entity_id;assessed_entity_type;best_biomarker_role;biomarker;exposure_agent;exposure_agent_id;specimen;specimen_id;evidence_source;evidence
```

### Step-2: creating directory structure for a release 
Run the following commands to create required subdirectories for your release (release 3.1.1 is used as an example here).
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
Make sure to update `misc/xref_info.csv` if there were new namespaces added to the `evidence_source` column in the downloaded TSVs. You would need to provide the URL. Example of an `xref_info` entry:
```
xref_key,xref_lbl,xref_url,xref_id_examples
edrn,EDRN,https://edrn.nci.nih.gov/@@dataDispatch?subjectURI=http://edrn.jpl.nasa.gov/bmdb/biomarkers/view/%s,27
```
This entry corresponds to the `EDRN:<id>` namespace as seen here:
```
$ head /../shared/biomarkerdb/downloads/edrn/current/edrn.tsv
biomarker_id  biomarker                        ...  evidence_source  ...
BB1528-1      increased levels of Osteopontin  ...  EDRN:27          ...
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


### Step-5: updating local citations archive
This step makes sure that all PMIDs mentioned in the dataset files have citation information in our local 
citations archive ("/../shared/biomarkerdb/downloads/ncbi/medline_json/pmid.*.json"). Use the following steps
to make sure all PMIDs mentioned in datasets have corresponding "/../shared/biomarkerdb/downloads/ncbi/medline_json/pmid.$PMID.json"
file. 

#### Step-5.1

```
$ cd /../shared/repos/backend-pipeline/object-maker/
$ python3 medline-download-step-1.py -r 3.2.1 &
```
The above command creates output file "/../shared/biomarkerdb/logs/medline-download-list.txt" which contains list of PMIDs
that do not have entry as "/../shared/biomarkerdb/downloads/ncbi/medline_json/pmid.$PMID.json".

IMPORTANT: if this file is empty, skip Step-5


#### Step-5.2
If "/../shared/biomarkerdb/logs/medline-download-list.txt" is not empty, continue and perform the following. First, update 
/../shared/repos/backend-pipeline/object-maker/conf/medline.json by visiting "https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/"
and https://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/" to get the "start" and "end" indexes and also the year. As of now, the file
has the following content:
```
{
   "baseline":{
      "url":"https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/",
      "start":1,
      "end":1334,
      "year":26
   },
   "updatefiles":{
      "url":"https://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/",
      "start":1335,
      "end":1438,
      "year":25
   }
}
```
Next, run the following command to download xml files and place them under /../shared/biomarkerdb/downloads/ncbi/medline_xml/.
```
nohup python3 medline-download-step-2.py &
```
Monitor the files being created under  /../shared/biomarkerdb/downloads/ncbi/medline_xml/ and make sure all are downloaded before you proceed
to next step (based on the current conf/medline.json file, there should be 1438 pubmed26n*.xml.gz files under /../shared/biomarkerdb/downloads/ncbi/medline_xml/.


#### Step-5.3
After Step-5.2 finishes, run the following:
```
nohup python3 medline-download-step-3.py
```
Make sure this step creates files under /data/shared/biomarkerdb/downloads/ncbi/medline_list/

#### Step-5.4
After Step-5.3 finishes, run the following:
```
nohup python3 medline-download-step-4.py
```
Make sure this step creates /../shared/biomarkerdb/logs/medline_xml_file_list.4.json


#### Step-5.5
After Step-5.4 finishes, run the following:
```
nohup python3 medline-download-step-5.py
```
Make sure this step creates files under /data/shared/biomarkerdb/downloads/ncbi/medline_json/



### Step-6: creating MongoDB objects
Run the following commands to create various JSON objects that will be loaded to MongoDB. The location of the objects created in this record is /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/*db/

```
$ cd /../shared/repos/backend-pipeline/object-maker/
$ nohup python3 run-pipeline.py -r 3.1.1 -p $PREV_REL &
```
The above command will output logfile /data/shared/biomarkerdb/logs/run-pipeline.log

$ cat /../shared/biomarkerdb/logs/run-pipeline.log
```
Started logging ...
created xxxxxx citation records under /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/citedb/*
created xxxxxx normalranges records under /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/normalrangesdb/*
created xxxxxx disease records under /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/diseasedb/*
created 203476 biomarker records under /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/biomarkerdb/*
created 203530 idtrack records under /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/idtrackdb/*
created 203476 list records under /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/listdb/*
created 203476 index records under /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/indexdb/*
created 144 sort records under /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/sortdb/*
created 4 searchinit records under /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/searchinitdb/*
created 1 stat records under /../shared/biomarkerdb/releases/data/v-3.1.1/jsondb/statdb/*
updated 18 dataset files under /../shared/biomarkerdb/releases/data/v-3.1.1/reviewed/*
```

### Step-7: loading MongoDB objects
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


### Step-8: updating init caches
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


### Step-9: updating version label for data 
Run the following commands to update version label data 
```
$ cd /../shared/repos/backend-pipeline/api/
$ python3 update_version.py -s $SERVER -v 3.1.1 -c data
```

## Ontology update - as needed
1. Make a new directory (name format yyyy_mm_dd) under `/../shared/repos/extraction/downloads/obci/` and `/../shared/biomarkerdb/downloads/ontology/`. Point the `current` symlinks to the new directories.
   ```bash
   cd /../shared/repos/extraction/downloads/obci
   mkdir <yyyy_mm_dd>
   ln -sfn <new_dir> current
   cd /../shared/biomarkerdb/downloads/ontology
   mkdir <yyyy_mm_dd>
   ln -sfn <new_dir> current
2. Place the new OWL file under `/../shared/repos/extraction/downloads/obci/current/`
3. Activate the virtual environment
   ```bash
   cd /../shared/repos/biomarker-backend-api
   source env/bin/activate
   ```
4. Run the ontology OWL to JSON converter
   ```bash
   cd misc_scripts
   python ontology_preprocessing.py /../shared/repos/extraction/downloads/obci/current/<obci_filename>.owl
   ```
   This creates `obci.json` under `/../shared/repos/biomarker-backend-api/misc_scripts/`
5. Extract OBCI terms from `obci.json`
   ```bash
   mv obci.json /../shared/repos/extraction/downloads/obci/current/
   cd /../shared/repos/extraction
   source env/bin/activate
   cd scripts/obci/
   python transform_ontology.py ../../downloads/obci/current/obci.json /../shared/biomarkerdb/downloads/ontology/current/ontology.json
   ```
   This creates `ontology.json` under `/../shared/biomarkerdb/downloads/ontology/current/`
6. Place the new `ontology.json` under `/../shared/biomarkerdb/releases/data/v-<new_version>/jsondb/ontologydb/` (in this example v-3.2.1 was used)
7. Load the new ontology into the `c_ontology` MongoDB collection
   ```
   cd /../shared/repos/backend-pipeline/api
   python3 populate_collection.py -s <server> -v 3.2.1 -c c_ontology






