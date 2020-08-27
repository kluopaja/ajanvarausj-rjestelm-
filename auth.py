from db import db
from flask import session, abort
from werkzeug.security import check_password_hash, generate_password_hash
from os import urandom

import datetime
from collections import namedtuple
import times


### User session related functions ###

def process_login(username, password):
    if username is None:
        return 'No username'
    if password is None:
        return 'No password'

    sql = 'SELECT id, password_hash FROM Users WHERE username=:username'
    user_query = db.session.execute(sql, {'username':username}).fetchone()

    if user_query is None:
        return 'Username not found'
    if check_password_hash(user_query[1], password):
        session['user_id'] = user_query[0]
        session['username'] = username
        return None
    return 'Incorrect password'

def set_csrf_token():
    session['csrf_token'] = urandom(16).hex()

def check_csrf_token(csrf_token):
    if 'csrf_token' not in session:
        abort(403)
    if session['csrf_token'] != csrf_token:
        abort(403)

def process_registration(username, password):
    if username is None or not check_alphanum_string(username, 1, 20):
        return 'Username not valid'
    if password is None or len(password) == 0:
        return 'Empty password not allowed'

    sql = 'SELECT COUNT(*) FROM Users WHERE username=:username'
    user_count = db.session.execute(sql, {'username':username}).fetchone()

    if user_count[0] > 0:
        return 'Username already in use!'

    password_hash = generate_password_hash(password)
    sql = 'INSERT INTO Users (username, password_hash) \
            VALUES (:username, :password_hash)'
    db.session.execute(sql, {'username': username,
                            'password_hash':password_hash})
    db.session.commit()
    return None

#TODO put checks inside try except
def check_alphanum_string(s, min_length, max_length):
    if len(s) < min_length or len(s) > max_length:
        return False
    return s.isalnum()

def process_logout():
    if 'user_id' in session:
        del session['user_id']
    if 'username' in session:
        del session['username']
    if 'csrf_token' in session:
        del session['csrf_token']
