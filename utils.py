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
           (owner_user_id, poll_name, poll_description,  \
           first_appointment_date, last_appointment_date, \
           poll_end_time, has_final_results) VALUES \
           (:owner_user_id, :poll_name, :poll_description, \
           :first_appointment_date, :last_appointment_date, :poll_end_time, \
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


def process_new_invitation(invitation_type, target_id,
                                reservation_length):

    if 'user_id' not in session:
        return False
    print(invitation_type)
    if invitation_type == 'poll_participant':
        #check if user has rights to do the operation
        #and that the target poll exists
        if not user_owns_poll(target_id):
            print("does not own")
            return False

        #TODO
        #check reservation_length
        url_id = urandom(16).hex()

        sql = "INSERT INTO PollMembershipLinks \
               (poll_id, url_id, reservation_length)\
               VALUES (:target_id, :url_id, :reservation_length)"

        #TODO find out a good way to put the reservation length to the
        #database
        #why is it string?
        reservation_length = str(int(reservation_length)*60)
        db.session.execute(sql, {'target_id': target_id, 'url_id': url_id,
                                 'reservation_length': reservation_length})
        db.session.commit()
        return True

    print("incorrect invitation type")
    return False


def user_owns_poll(poll_id):
    sql = "SELECT owner_user_id FROM Polls WHERE poll_id=:poll_id"
    result = db.session.execute(sql, {'poll_id': poll_id})
    user = result.fetchone()

    if user is None:
        return False
    if user[0] == session['user_id']:
        return True

    return False

def get_participant_invitations(poll_id):
    sql = "SELECT url_id, reservation_length FROM PollMembershipLinks\
           WHERE poll_id=:poll_id"

    result = db.session.execute(sql, {'poll_id': poll_id})
    invitations = result.fetchall()
    return invitations

def get_resource_invitations(poll_id):
    sql = "SELECT L.url_id, R.resource_description \
           FROM ResourceMembershipLinks L, Resources R\
           WHERE L.resource_id=R.resource_id AND R.owner_poll_id=:poll_id"

    result = db.session.execute(sql, {"poll_id": poll_id})
    resource_invitations = result.fetchall()
    return resource_invitations



#TODO return named tuple after we know what field are necessary for it
#we need poll name, poll description, reservation length, poll_id
def participant_invitation_by_url_id(url_id):
    sql = "SELECT poll_name, poll_description, reservation_length, \
           P.poll_id \
           FROM Polls P, PollMembershipLinks L \
           WHERE P.poll_id=L.poll_id AND L.url_id=:url_id"

    result = db.session.execute(sql, {"url_id": url_id}).fetchall()
    if result is None:
        return None

    return result[0]


#we need poll name, poll description, resource description, resource_id
def resource_invitation_by_url_id(url_id):
    sql = "SELECT poll_name, poll_description, resource_description, \
           resource_id \
           FROM Polls P, Resources R, ResourceMembershipLinks L \
           WHERE P.poll_id=R.owner_poll_id AND R.resource_id=L.resource_id \
           AND L.url_id=:url_id"

    result = db.session.execute(sql, {"url_id": url_id}).fetchall()
    if result is None:
        return None

    return result[0]


def get_invitation_type(url_id):
    sql = "SELECT COUNT(*) FROM PollMembershipLinks WHERE url_id=:url_id"
    result = db.session.execute(sql, {'url_id': url_id}).fetchone()
    if result[0] == 1:
        return 'poll_participant'

    sql = "SELECT COUNT(*) FROM ResourceMembershipLinks WHERE url_id=:url_id"
    result = db.session.execute(sql, {'url_id': url_id}).fetchone()
    if result[0] == 1:
        return 'resource_owner'

    return None

#TODO take invitation as a parameter and not as url_id
def apply_poll_invitation(url_id):
    details = participant_invitation_by_url_id(url_id)
    sql = "INSERT INTO UsersPolls (user_id, poll_id, reservation_length) \
           VALUES (:user_id, :poll_id, :reservation_length)"

    #TODO think about doing this differently
    user_id = session['user_id']
    db.session.execute(sql, {'user_id': user_id, 'poll_id': details[3],
                             'reservation_length': details[2]})
    db.session.commit()

#TODO do not insert multiple times the same element!
def apply_resource_invitation(url_id):
    details = resource_invitation_by_url_id(url_id)
    sql = "INSERT INTO UsersResources (user_id, resource_id) \
           VALUES (:user_id, :resouce_id)"

    user_id = session['user_id']
    db.session.execute(sql, {'user_id': user_id, 'poll_id': details[3]})
    db.session.commit()

#so in invite function it would seem that we need an invitation class
