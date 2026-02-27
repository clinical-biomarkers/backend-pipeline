import os,sys
from flask_restx import Namespace, Resource, fields
from flask import (request, current_app, session, jsonify)
from bmkb.db import get_mongodb, log_error, log_request
from bmkb.document import get_one, get_many, insert_one, update_one, delete_one, order_json_obj
from werkzeug.utils import secure_filename
import datetime
import time
import subprocess
import json
import bcrypt

from flask_jwt_extended import (
    jwt_required, create_access_token,
    create_refresh_token,
    get_jwt_identity, set_access_cookies, get_csrf_token,
    set_refresh_cookies, unset_jwt_cookies
    )

from bmkb.auth_apilib import auth_userid, auth_notify, auth_contact, auth_register, auth_aisearch, auth_login,  auth_userinfo, auth_userupdate, auth_userdelete, auth_contactlist, auth_contactupdate, auth_contactdelete

from bmkb.util import get_req_obj
import traceback



api = Namespace("auth", description="Auth APIs")


register_query_model = api.model("Auth Register Query",
    { 
        "email":fields.String(required=True, default=""),
        "password":fields.String(required=True, default="")
    }
)
aisearch_query_model = api.model("Auth AI Search Query",
    {
        "glycan_ai_search":fields.String(required=True, default=""),
        "protein_ai_search":fields.String(required=True, default="")
    }
)

login_query_model = api.model("Auth Login Query",
    { 
        "email":fields.String(required=True, default=""),
        "password":fields.String(required=True, default="")
    }
)
userid_query_model = api.model("Auth UserID Query",{})
userinfo_query_model = api.model("Auth User Info Query",
    { 
        "email":fields.String(required=True, default="")
    }
)
contactlist_query_model = api.model("Auth Contact List Query",
    { 
        "visibility":fields.String(required=True, default="all")
    }
)
contactupdate_query_model = api.model("Auth Contact Update Query",
    { 
        "id":fields.String(required=True, default="")
    }
)
contactdelete_query_model = api.model("Auth Contact Delete Query",
    { 
        "id":fields.String(required=True, default="")
    }
)
contact_query_model = api.model("Auth Contact Query",
    {
        "fname":fields.String(required=True, default=""),
        "lname":fields.String(required=True, default=""),
        "email":fields.String(required=True, default=""),
        "subject":fields.String(required=True, default=""),
        "message":fields.String(required=True, default="")
    }
)

notify_query_model = api.model("Auth Notify Query",
    {
        "fname":fields.String(required=True, default=""),
        "lname":fields.String(required=True, default=""),
        "subject":fields.String(required=True, default=""),
        "message":fields.String(required=True, default="")
    }
)



@api.route('/userid/')
class Auth(Resource):
    @api.expect(userid_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            res_obj = log_request(req_obj, "/auth/userid/", request)
            if "error_list" not in res_obj:
                res_obj = auth_userid(config_obj)
        except Exception as e:
            res_obj =  log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()

@api.route('/contact/')
class Auth(Resource):
    @api.expect(contact_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            res_obj = log_request(req_obj, "/auth/contact/", request)
            if "error_list" not in res_obj:
                res_obj = auth_contact(req_obj, config_obj)
        except Exception as e:
            res_obj =  log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()


@api.route('/notify/')
class Auth(Resource):
    @api.expect(notify_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            res_obj = log_request(req_obj, "/auth/notify/", request)
            if "error_list" not in res_obj:
                res_obj = auth_notify(req_obj, config_obj)
        except Exception as e:
            res_obj =  log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()


@api.route('/aisearch/')
class Auth(Resource):
    @api.expect(aisearch_query_model)
    @jwt_required
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            res_obj = log_request(req_obj, "/auth/aisearch/", request)
            if "error_list" not in res_obj:
                res_obj = auth_aisearch(req_obj, config_obj)
        except Exception as e:
            res_obj =  log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()



@api.route('/register/')
class Auth(Resource):
    @api.expect(register_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            req_obj["status"], req_obj["access"], req_obj["role"] = 0, "readonly", ""
            if req_obj["email"] in config_obj["admin_list"]:
                req_obj["status"], req_obj["access"], req_obj["role"] = 1, "write", "admin"
            res_obj = log_request(req_obj, "/auth/register/", request)
            if "error_list" not in res_obj:
                res_obj = auth_register(req_obj, config_obj)
        except Exception as e:
            res_obj =  log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()


@api.route('/login/')
class Auth(Resource):
    @api.expect(login_query_model)
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            if req_obj == None:
                return {"error_list":[{"error_code":"invalid request payload"}]}
            for k in ["email", "password"]:
                if k not in req_obj:
                    return {"error_list":[{"error_code":"missing-parameter-%s" % (k)}]}
            username = req_obj["email"]
            password = req_obj["password"]
            mongo_dbh, error_obj = get_mongodb()
            if error_obj != {}:
                return error_obj, 500
            user_doc = mongo_dbh["c_users"].find_one({'email' : username })
            error = None
            if user_doc is None:
                error = "incorrect-email/password"
            elif "password" not in user_doc:
                error = "password does not exist for registerd user"
            else:
                submitted_password = password.encode('utf-8')
                #stored_password = user_doc['password'].encode('utf-8')
                stored_password = user_doc['password']
                if bcrypt.hashpw(submitted_password, stored_password) != stored_password:
                    error = "incorrect-email/password"
            res_obj = log_request(req_obj, "/auth/login/", request)
            if "error_list" not in res_obj:
                res_obj = {"status":1}
                if error is None:
                    if user_doc["status"] == 0:
                        res_obj = {"error_list":[{"error_code":"inactive account"}]}
                    else:
                        access_token = create_access_token(identity=username, expires_delta=None)
                        refresh_token = create_refresh_token(identity=username)
                        res_obj["access_token"] = access_token
                        res_obj["access_csrf"] = get_csrf_token(access_token)
                        res_obj["refresh_csrf"] = get_csrf_token(refresh_token)
                        res_obj["username"] = user_doc["email"]
                        session['email'] = user_doc["email"]
                        set_access_cookies(jsonify(res_obj), access_token)
                        set_refresh_cookies(jsonify(res_obj), refresh_token)
                else:
                    res_obj = {"error_list":[{"error_code":error}]}
        except Exception as e:
            res_obj =  log_error(traceback.format_exc())
        
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()





@api.route('/userinfo/')
class Auth(Resource):
    @api.doc(False)
    @api.expect(userinfo_query_model)
    @jwt_required
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            #current_user, user_info = "rykahsay@gwu.edu", {}
            current_user = get_jwt_identity()
            res_obj = log_request(req_obj, "/auth/userinfo/", request)
            if "error_list" not in res_obj:
                res_obj = auth_userinfo(current_user, req_obj, config_obj)
        except Exception as e:
            res_obj =  log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()


@api.route('/userupdate/')
class Auth(Resource):
    @api.doc(False)
    @jwt_required
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            #current_user, user_info = "rykahsay@gwu.edu", {}
            current_user = get_jwt_identity()
            res_obj = log_request(req_obj, "/auth/userupdate/", request)
            if "error_list" not in res_obj:
                res_obj = auth_userupdate(current_user, req_obj, config_obj)
        except Exception as e:
            res_obj =  log_error(traceback.format_exc())
        
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()

@api.route('/userdelete/')
class Auth(Resource):
    @api.doc(False)
    @jwt_required
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            #current_user, user_info = "rykahsay@gwu.edu", {}
            current_user = get_jwt_identity()
            res_obj = log_request(req_obj, "/auth/userdelete/", request)
            if "error_list" not in res_obj:
                res_obj = auth_userdelete(current_user, req_obj, config_obj)
        except Exception as e:
            res_obj =  log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()


@api.route('/contactlist/')
class Auth(Resource):
    @api.doc(False)
    @api.expect(contactlist_query_model)
    @jwt_required
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            #current_user, user_info = "rykahsay@gwu.edu", {}
            current_user = get_jwt_identity()
            res_obj = log_request(req_obj, "/auth/contactlist/", request)
            if "error_list" not in res_obj:
                res_obj = auth_contactlist(current_user, req_obj, config_obj)
        except Exception as e:
            res_obj =  log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()

@api.route('/contactupdate/')
class Auth(Resource):
    @api.doc(False)
    @api.expect(contactupdate_query_model)
    @jwt_required
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            #current_user, user_info = "rykahsay@gwu.edu", {}
            current_user = get_jwt_identity()
            res_obj = log_request(req_obj, "/auth/contactupdate/", request)
            if "error_list" not in res_obj:
                res_obj = auth_contactupdate(current_user, req_obj, config_obj)
        except Exception as e:
            res_obj =  log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()

@api.route('/contactdelete/')
class Auth(Resource):
    @api.doc(False)
    @api.expect(contactdelete_query_model)
    @jwt_required
    def post(self):
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "conf/config.json")
        config_obj = json.load(open(json_url))
        res_obj = {}
        try:
            req_obj = get_req_obj(request)
            #current_user, user_info = "rykahsay@gwu.edu", {}
            current_user = get_jwt_identity()
            res_obj = log_request(req_obj, "/auth/contactdelete/", request)
            if "error_list" not in res_obj:
                res_obj = auth_contactdelete(current_user, req_obj, config_obj)
        except Exception as e:
            res_obj =  log_error(traceback.format_exc())
        http_code = 500 if "error_list" in res_obj else 200
        return res_obj, http_code

    @api.doc(False)
    def get(self):
        return self.post()






