from db import db
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash


def process_login(username, password):
    sql = "SELECT user_id, password_hash FROM Users WHERE username=:username"
    user_query = db.session.execute(sql, {"username":username}).fetchone()
    print(user_query)
    if user_query is None:
        return False

    if check_password_hash(user_query[1], password):
        session['user_id'] = user_query[0]
        session['username'] = username
        return True

    return False

def process_registration(username, password):
    sql = "SELECT COUNT(*) FROM Users WHERE username=:username"
    user_count = db.session.execute(sql, {"username":username}).fetchone()
    print("user_count: ", user_count)
    if user_count[0] > 0:
        return False

    if not check_username(username):
        return False

    password_hash = generate_password_hash(password)

    print("salasana ja hash: ", password + "  " + password_hash)

    sql = "INSERT INTO Users (username, password_hash) \
            VALUES (:username, :password_hash)"
    db.session.execute(sql, {'username': username, 
                            'password_hash':password_hash})
    db.session.commit()

    return True

def check_username(username):
    if len(username) == 0:
        return False
    if not username.isalnum():
        return False
    return True
def process_logout():
    del session['user_id'] 
    del session['username']


