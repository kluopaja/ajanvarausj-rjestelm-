from flask import Flask
from flask_login import LoginManager
from os import getenv
app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")
#app.url_map.strict_slashes = False


import routes
