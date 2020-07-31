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


class Poll():
    def __init__(self, owner, name, description, first_date, last_date,
            end_date, end_time, has_final_results):
        self.owner = owner
        self.name = name
        self.description = description
        self.first_date = first_date
        self.last_date = last_date
        self.end_date = end_date
        self.end_time = end_time
        self.has_final_results = has_final_results

def check_poll_validity(poll):
    if None in [poll.name, poll.description, poll.first_date, poll.last_date,
                poll.end_date, poll.end_time]:
        return False
    return True


def process_new_poll(poll):
    sql = "INSERT INTO Polls \
           (owner_user_id, poll_end_time, first_appointment_date, \
           last_appointment_date, poll_name, poll_description, \
           has_final_results) VALUES \
           (:owner_user_id, :poll_end_time, :first_appointment_date, \
           :last_appointment_date, :poll_name, :poll_description, \
           :has_final_results)"

    poll_end_timestamp = poll.end_date + " " + poll.end_time;

    parameter_dict = {'owner_user_id': poll.owner, 
                      'poll_end_time': poll_end_timestamp,
                      'first_appointment_date': poll.first_date,
                      'last_appointment_date': poll.last_date,
                      'poll_name': poll.name,
                      'poll_description': poll.description,
                      'has_final_results': poll.has_final_results}

    db.session.execute(sql, parameter_dict)
    db.session.commit()

#returns ids of all polls that user somehow part of
#(either owner, participant or owner of a resource)
def get_user_polls():
    pass
    #sql = "SELECT * FROM Polls WHERE 
