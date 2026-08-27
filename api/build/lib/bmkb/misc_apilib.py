import os
import string
import random
import hashlib
import json
import datetime,time
import pytz
import glob
from flask import Flask, request, jsonify, Response, stream_with_context
import zlib
import gzip
import struct           

from bmkb.db import get_mongodb



def verlist(config_obj):
    
    dbh, error_obj = get_mongodb()
    if error_obj != {}:
        return error_obj

    coll = "c_version"
    doc = dbh[coll].find_one({"component":"data"})
    version_list = doc["version_list"] if "version_list" in doc else []

    return version_list






