from flask import Flask
from flask_talisman import Talisman
from flask_login import LoginManager
from os import getenv



app = Flask(__name__)
Talisman(app)
app.secret_key = getenv("SECRET_KEY")

import routes
