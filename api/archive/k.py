import os,sys
import string
from optparse import OptionParser
import glob
import json
from bson import json_util
import pymongo
from pymongo import MongoClient
import datetime


__version__="1.0"
__status__ = "Dev"



###############################
def main():

    doc = json.load(open("glygen/conf/job_init.json"))
    print (json.dumps(doc, indent=4))

    return




if __name__ == '__main__':
    main()
