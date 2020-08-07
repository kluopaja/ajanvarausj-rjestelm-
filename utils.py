from db import db
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash
from os import urandom
import datetime
from collections import namedtuple
import times


### User session related functions ###

def process_login(username, password):
    if username is None:
        return "No username"

    if password is None:
        return "No password"

    sql = "SELECT user_id, password_hash FROM Users WHERE username=:username"
    user_query = db.session.execute(sql, {"username":username}).fetchone()
    print(user_query)
    if user_query is None:
        return "Username not found"

    if check_password_hash(user_query[1], password):
        session['user_id'] = user_query[0]
        session['username'] = username
        return None

    return "Incorrect password"

def process_registration(username, password):
    if username is None or not check_alphanum_string(username, 1, 20):
        return "Username not valid"

    if password is None or len(password) == 0:
        return "Empty password not allowed"

    sql = "SELECT COUNT(*) FROM Users WHERE username=:username"
    user_count = db.session.execute(sql, {"username":username}).fetchone()
    print("user_count: ", user_count)

    if user_count[0] > 0:
        return "Username already in use!"

    password_hash = generate_password_hash(password)

    print("salasana ja hash: ", password + "  " + password_hash)

    sql = "INSERT INTO Users (username, password_hash) \
            VALUES (:username, :password_hash)"
    db.session.execute(sql, {'username': username,
                            'password_hash':password_hash})
    db.session.commit()
    return None

def check_alphanum_string(s, min_length, max_length):
    if len(s) < min_length or len(s) > max_length:
        return False
    try:
        if not s.isalnum():
            return False
        return True
    except:
        return False

def process_logout():
    del session['user_id']
    del session['username']

### Poll related functions ###

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
        first_date = datetime.date.fromisoformat(first_date)
        last_date = datetime.date.fromisoformat(last_date)
        end_date = datetime.date.fromisoformat(end_date)
        end_time = datetime.time.fromisoformat(end_time)
        end = datetime.datetime.combine(end_date, end_time)
        tmp = Poll(owner, name, description, first_date, last_date, end,
                   has_final_results)
        return tmp



def process_new_poll(user_id, name, description, first_date, last_date,
                     end_date, end_time):
    try:
        first_date = datetime.date.fromisoformat(first_date)
        last_date = datetime.date.fromisoformat(last_date)
        end_date = datetime.date.fromisoformat(end_date)
        end_time = datetime.time.fromisoformat(end_time)
        end = datetime.datetime.combine(end_date, end_time)
    except ValueError:
        return "Incorrect time/date formats!"

    if first_date > last_date:
        return "The last available date must be after the first one!"

    if end <= datetime.datetime.today() + datetime.timedelta(seconds=2):
        return "Poll end should not be in the past"

    if not check_alphanum_string(name, 1, 30):
        return "Not valid poll name"

    if not check_alphanum_string(description, 1, 10000):
        return "Not valid poll description"

    sql = "INSERT INTO Polls \
           (owner_user_id, poll_name, poll_description,  \
           first_appointment_date, last_appointment_date, \
           poll_end_time, has_final_results) VALUES \
           (:owner_user_id, :poll_name, :poll_description, \
           :first_appointment_date, :last_appointment_date, :poll_end_time, \
           :has_final_results)"



    parameter_dict = {'owner_user_id': user_id,
                      'poll_end_time': end,
                      'first_appointment_date': first_date,
                      'last_appointment_date': last_date,
                      'poll_name': name,
                      'poll_description': description,
                      'has_final_results': False}

    db.session.execute(sql, parameter_dict)
    db.session.commit()
    return None

#returns ids of all polls that user somehow part of
#(either owner, participant or owner of a resource)

#TODO think about which of these following 4 should take user id as a parameter
#should this take some parameter?
#TODO think how to replace this. just use Poll objects?

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
    sql = 'SELECT M.poll_id FROM Resources R, UsersResources U, PollMembers M\
           WHERE M.id=R.member_id AND R.resource_id=U.resource_id \
           AND U.user_id=:user_id'

    result = db.session.execute(sql, {'user_id':user_id})
    polls = result.fetchall()
    if polls is None:
        return []

    poll_ids = [x[0] for x in polls]
    return poll_ids

def poll_ids_where_user_participant(user_id):
    sql = 'SELECT M.poll_id FROM PollMembers M, UsersPollMembers U \
           WHERE U.user_id=:user_id AND U.member_id=M.id'

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

def user_owns_poll(poll_id):
    sql = "SELECT owner_user_id FROM Polls WHERE poll_id=:poll_id"
    result = db.session.execute(sql, {'poll_id': poll_id})
    user = result.fetchone()

    if user is None:
        return False
    if user[0] == session['user_id']:
        return True

    return False

def user_is_participant(poll_id):
    user_id = session.get('user_id')
    sql = "SELECT COUNT(*) FROM PollMembers M, UsersPollMembers U WHERE \
           M.id=U.member_id AND M.poll_id=:poll_id AND U.user_id=:user_id"

    tmp = db.session.execute(sql, {'poll_id': poll_id, 'user_id': user_id})
    count = tmp.fetchone()[0]
    if count > 0:
        return True

    return False

#TODO output to datetime.date
def get_poll_date_range(poll_id):
    sql = "SELECT first_appointment_date, last_appointment_date FROM \
           Polls WHERE poll_id=:poll_id"
    poll = db.session.execute(sql, {'poll_id': poll_id}).fetchone()
    if poll is None:
        return None
    return poll


def db_tuple_to_poll(t):
    return Poll(t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[0])

### Invitation related functions ###

#TODO contents divide into two functions
def process_new_invitation(invitation_type, poll_id, resource_id,
                                reservation_length):
    print(invitation_type)

    if invitation_type == 'poll_participant':
        if poll_id is None:
            return "No poll id was provided"

        if reservation_length is None:
            return "No resource_length was provided"
        try:
            reservation_length = int(reservation_length)
        except ValueError:
            return "Reservation length should be an integer"

        if reservation_length > 24*60:
            return "Maximum reservation length is 24 hours"
        if reservation_length <= 0:
            return "Reservation length should be positive"

        if not user_owns_poll(poll_id):
            return "User does not own the poll"

        url_id = urandom(16).hex()
        sql = "INSERT INTO PollMembershipLinks \
               (poll_id, url_id, reservation_length)\
               VALUES (:poll_id, :url_id, :reservation_seconds)"

        reservation_seconds = str(reservation_length*60)
        db.session.execute(sql, {'poll_id': poll_id, 'url_id': url_id,
                                 'reservation_seconds': reservation_seconds})
        db.session.commit()
        return None

    elif invitation_type == 'resource_owner':
        if resource_id is None:
            return "No resource id was provided"
        #check user is the owner of the resource parent poll
        if not user_owns_parent_poll(resource_id):
            return "User does not own the resource"

        url_id = urandom(16).hex()
        sql = "INSERT INTO ResourceMembershipLinks \
               (resource_id, url_id) VALUES (:resource_id, :url_id)"
        db.session.execute(sql, {'resource_id': resource_id, 'url_id': url_id})
        db.session.commit()
        return None

    else:
        return "Incorrect invitation type"

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



def get_participant_invitations(poll_id):
    sql = "SELECT url_id, reservation_length FROM PollMembershipLinks\
           WHERE poll_id=:poll_id"

    result = db.session.execute(sql, {'poll_id': poll_id})
    invitations = result.fetchall()
    return invitations

def get_resource_invitations(poll_id):
    sql = "SELECT L.url_id, R.resource_description \
           FROM PollMembers P, Resources R, ResourceMembershipLinks L \
           WHERE P.poll_id=:poll_id AND P.id=R.member_id \
           AND R.resource_id=L.resource_id"
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
           R.resource_id \
           FROM Polls P, PollMembers M, Resources R, ResourceMembershipLinks L \
           WHERE P.poll_id=M.poll_id AND M.id=R.member_id \
           AND R.resource_id=L.resource_id AND L.url_id=:url_id"

    result = db.session.execute(sql, {"url_id": url_id}).fetchall()
    if result is None:
        return None

    return result[0]

#TODO take invitation as a parameter and not as url_id
def initialize_poll_member_times(member_id, poll_id, satisfaction):
    start, end = get_poll_date_range(poll_id)
    end += datetime.timedelta(days=1)

    #convert to datetime.datetime
    start = datetime.datetime(start.year, start.month, start.day)
    end = datetime.datetime(end.year, end.month, end.day)

    times.add_member_preference(member_id, start, end, 0)

#adds user to a poll and initializes the user time preferences to 0
#assumes that the url_id is valid
def apply_poll_invitation(url_id):
    details = participant_invitation_by_url_id(url_id)

    #this should never be possible
    if details is None:
        return "No invitation found"

    #TODO think about doing this differently
    #TODO split into functions
    poll_id = details[3]

    if user_is_participant(poll_id):
        print('already participant')
        return "User is already a participant"

    user_id = session['user_id']
    reservation_length = details[2]

    sql = "INSERT INTO PollMembers (poll_id) VALUES (:poll_id) RETURNING id"

    member_id = db.session.execute(sql, {'poll_id': poll_id}).fetchone()

    sql = "INSERT INTO UsersPollMembers \
          (user_id, member_id, reservation_length) VALUES \
          (:user_id, :member_id, :reservation_length)"

    db.session.execute(sql, {'user_id': user_id, 'member_id': member_id[0],
                             'reservation_length': reservation_length})

    initialize_poll_member_times(member_id[0], poll_id, 0)

    db.session.commit()

    return None


#assumes that the url_id is valid
def apply_resource_invitation(url_id):
    details = resource_invitation_by_url_id(url_id)
    user_id = session['user_id']
    resource_id = details[3]
    return add_user_to_resource(user_id, resource_id)

def get_user_poll_member_id(user_id, poll_id):
    sql = "SELECT member_id FROM PollMembers P, UsersPollMembers U \
           WHERE P.id=U.member_id AND P.poll_id=:poll_id \
           AND U.user_id=:user_id"

    tmp = db.session.execute(sql, {'user_id': user_id, 'poll_id': poll_id})
    member_id = tmp.fetchone()
    if member_id is None:
        return None

    return member_id[0]


### Resource related functions ###
def get_resource_member_id(resource_id):
    sql = "SELECT member_id FROM Resources WHERE resource_id=:resource_id"

    member_id = db.session.execute(sql, {'resource_id': resource_id}).fetchone()
    if member_id is None:
        return None

    return member_id[0]


def get_resource_parent_poll(resource_id):
    sql = "SELECT P.poll_id FROM PollMembers P, Resources R \
           WHERE P.id=R.member_id AND R.resource_id=:resource_id"

    poll_id = db.session.execute(sql, {'resource_id': resource_id}).fetchone()

    if poll_id is None:
        return None

    return poll_id[0]

def user_owns_parent_poll(resource_id):
    sql = "SELECT COUNT(*) FROM Polls P, PollMembers M, Resources R \
           WHERE P.poll_id=M.poll_id AND M.id=R.member_id \
           AND P.owner_user_id=:user_id AND R.resource_id=:resource_id"

    user_id = session.get('user_id')
    count = db.session.execute(sql, {'user_id': user_id,
                                     'resource_id': resource_id}).fetchone()
    if count[0] == 1:
        return True
    if count[0] > 1:
        print("ERROR! count should not be > 1")
        return False

    return False

def user_in_resource(user_id, resource_id):
    sql = "SELECT COUNT(*) FROM UsersResources WHERE \
           resource_id=:resource_id AND user_id=:user_id"

    count = db.session.execute(sql, {'user_id': user_id,
                                     'resource_id': resource_id}).fetchone()
    if count[0] == 1:
        return True
    if count[0] == 0:
        return False


def add_user_to_resource(user_id, resource_id):
    if user_in_resource(user_id, resource_id):
        return "User already in the resource"

    sql = "INSERT INTO UsersResources (user_id, resource_id) \
           VALUES (:user_id, :resouce_id)"
    db.session.execute(sql, {'user_id': user_id, 'resouce_id': resource_id})
    db.session.commit()
    return None

def resource_description_in_poll(poll_id, resource_description):
    sql = "SELECT COUNT(*) FROM PollMembers M, Resources R \
           WHERE M.id=R.resource_id AND M.poll_id=:poll_id \
           AND R.resource_description=:resource_description"

    tmp = db.session.execute(sql,
                            {'poll_id': poll_id,
                             'resource_description': resource_description})
    count = tmp.fetchone()
    if count[0] == 1:
        return True

    return False

def process_new_resource(poll_id, resource_description):
    print("process_new_resource", poll_id)

    if poll_id is None:
        return "No poll id was provided"
    if resource_description is None:
        return "No resource descrption was provided"


    if not user_owns_poll(poll_id):
        return "User does not own the poll"

    if resource_description_in_poll(poll_id, resource_description):
        return "Resource with an identical resource_descrpition already \
                exists in the poll"

    sql = "INSERT INTO PollMembers (poll_id) VALUES (:poll_id) RETURNING id"
    member_id = db.session.execute(sql, {'poll_id': poll_id}).fetchone()

    sql = "INSERT INTO Resources (resource_description, member_id) \
            VALUES (:resource_description, :member_id)"

    db.session.execute(sql, {'resource_description': resource_description,
                             'member_id': member_id[0]})

    initialize_poll_member_times(member_id[0], poll_id, 0)
    db.session.commit()

    return None

def get_poll_resources(poll_id):
    sql = "SELECT R.resource_description, R.resource_id, M.id FROM \
           Polls P, PollMembers M, Resources R WHERE \
           P.poll_id=M.poll_id AND M.id=R.member_id \
           AND P.poll_id=:poll_id"
    result = db.session.execute(sql, {'poll_id': poll_id})
    resources = result.fetchall()
    if resources is None:
        return []
    return resources

def get_user_poll_resources(user_id, poll_id):
    sql = "SELECT R.resource_description, R.resource_id, M.id FROM \
           PollMembers M, Resources R, UsersResources U WHERE \
           M.id=R.member_id AND R.resource_id=U.resource_id \
           AND M.poll_id=:poll_id AND U.user_id=:user_id"

    result = db.session.execute(sql, {'user_id': user_id,
                                      'poll_id': poll_id})
    resources = result.fetchall()
    if resources is None:
        return []
    return resources



#TODO modify SQL INSERT INTO queries so that the queries would already
#have the final parameter names. So the dict should be always: 'asdf': asdf etc

#TODO This is the db.commit() applied too early sometimes now?
#It should always be applied only when all the modifications have been
#done!
