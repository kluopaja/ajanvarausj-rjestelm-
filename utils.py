from db import db
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash
from os import urandom
from datetime import datetime, date, time


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
    #times are stored as python datetime.date or datetime.datetime
    def __init__(self, owner, name, description, first_date, last_date,
            end, has_final_results, poll_id=None):
        self.owner = owner
        self.name = name
        self.description = description
        self.first_date = first_date
        self.last_date = last_date
        self.end = end
        self.has_final_results = has_final_results
        self.poll_id=poll_id

    @classmethod
    def from_form(self, owner, name, description, first_date, last_date,
            end_date, end_time, has_final_results):
        first_date = date.fromisoformat(first_date)
        last_date = date.fromisoformat(last_date)
        end_date = date.fromisoformat(end_date)
        end_time = time.fromisoformat(end_time)
        end = datetime.combine(end_date, end_time)
        tmp = Poll(owner, name, description, first_date, last_date, end,
                   has_final_results)

        return tmp

def check_poll_validity(poll):
    if None in [poll.name, poll.description, poll.first_date, poll.last_date,
                poll.end]:
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

    poll_end_timestamp = poll.end

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
    tmp = get_user_poll_ids()
    return get_polls_by_ids(tmp)
def get_user_poll_ids():
    if 'user_id' not in session:
        return []

    polls = poll_ids_owned_by(session['user_id'])
    polls += poll_ids_where_user_owns_resource(session['user_id'])
    polls += poll_ids_where_user_participant(session['user_id'])

    #return unique
    return sorted(list(set(polls)))

def poll_ids_owned_by(user_id):
    sql = 'SELECT poll_id FROM Polls WHERE owner_user_id=:user_id'
    result = db.session.execute(sql, {'user_id':user_id})
    polls = result.fetchall()
    if polls is None:
        return []

    poll_ids = [x[0] for x in polls]
    return poll_ids

def poll_ids_where_user_owns_resource(user_id):
    sql = 'SELECT owner_poll_id FROM Resources R, UsersResources U\
           WHERE R.resource_id=U.resource_id AND U.user_id=:user_id'

    result = db.session.execute(sql, {'user_id':user_id})
    polls = result.fetchall()
    if polls is None:
        return []

    poll_ids = [x[0] for x in polls]
    return poll_ids


def poll_ids_where_user_participant(user_id):
    sql = 'SELECT poll_id FROM UsersPolls WHERE user_id=:user_id'

    result = db.session.execute(sql, {'user_id':user_id})
    polls = result.fetchall()
    if polls is None:
        return []

    poll_ids = [x[0] for x in polls]
    return poll_ids

def get_polls_by_ids(poll_ids):
    if len(poll_ids) == 0:
        return []

    sql = 'SELECT * FROM Polls WHERE poll_id in :poll_ids'
    result = db.session.execute(sql, {'poll_ids':tuple(poll_ids)})
    polls = result.fetchall()
    if polls is None:
        return []
    #TODO fix
    print(polls[0])
    print(db_tuple_to_poll(polls[0]).poll_id)
    return [db_tuple_to_poll(x) for x in polls]

def db_tuple_to_poll(t):
    return Poll(t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[0])

#TODO fix, fails with large reservation_lengths
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
