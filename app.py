from flask import Flask
from flask_talisman import Talisman
from flask_login import LoginManager
from os import getenv
csp = {
    'default-src': '\'self\'',
    'script-src': '\'self\'',
}
app = Flask(__name__)
Talisman(app, content_security_policy=csp,content_security_policy_nonce_in=['script-src'])

app.secret_key = getenv("SECRET_KEY")

import routes
