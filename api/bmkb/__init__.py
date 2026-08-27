import os
import datetime
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from flask_restx import Api, Resource, fields

from bmkb.db import load_network_docs

from .html import api as html_api
from .auth import api as auth_api
from .data import api as data_api
from .globalsearch import api as globalsearch_api
from .pages import api as pages_api
#from .cart import api as cart_api
from .typeahead import api as typeahead_api
from .log import api as log_api
from .event import api as event_api
from .misc import api as misc_api
from .biomarker import api as biomarker_api
from .pagination import api as pagination_api


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.url_map.strict_slashes = False

    CORS(app, supports_credentials=True)
    #CORS(app)

    #api = Api(app, version='1.0', title='GlyGen APIs', description='Documentation for the GlyGen APIs',)
    api = Api(app, template_folder='templates', ui_params={'layout': 'BaseLayout'})
   
    # Specify the custom template folder relative to your app.py
    # If the 'templates' folder is in the same directory as app.py
    # The 'layout': 'BaseLayout' is often required to ensure default Swagger UI functionality 
    # is loaded correctly.

    api.add_namespace(biomarker_api)
    #api.add_namespace(globalsearch_api)
    api.add_namespace(data_api)
    api.add_namespace(pages_api)
    api.add_namespace(typeahead_api)
    api.add_namespace(auth_api)
    api.add_namespace(log_api)
    #api.add_namespace(video_api)
    api.add_namespace(event_api)
    #api.add_namespace(cart_api) 
    api.add_namespace(misc_api)
    #api.add_namespace(pagination_api)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.config.from_pyfile('config.py', silent=True)
    settings = app.config.get('RESTFUL_JSON', {})
    settings.setdefault('indent', 2)
    #settings.setdefault('sort_keys', True)
    app.config['RESTFUL_JSON'] = settings

    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(days=1)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = datetime.timedelta(days=30)
    app.config['PROPAGATE_EXCEPTIONS'] = True
    #app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    app.config['JSON_SORT_KEYS'] = False

 
    jwt = JWTManager(app)




    return app
