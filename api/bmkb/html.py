import os,sys
from flask_restx import Namespace, Resource, fields
from flask import Flask, render_template


api = Namespace("html", description="Html APIs")
@api.route('/ui')  # Define a route for your UI
class UIRoot(Resource):
    def get(self):
        """
        Renders the main UI page.
        """
        return render_template(
            'index.html',
            title='My App',
            app_name='Flask-RESTX UI Example',
            message='Hello from the server!'
        )

