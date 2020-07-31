from app import app
from flask import render_template
from werkzeug.urls import url_parse
from flask import session, request, redirect

from utils import process_login, process_registration, process_logout
from utils import check_poll_validity, process_new_poll
from utils import Poll

@app.route('/')
def index():
    polls = [(str(i), f'kysely {i}') for i in range(4)]
    return render_template("index.html", polls=polls)


