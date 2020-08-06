from db import db
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash
from os import urandom
import datetime
from collections import namedtuple


### User session related functions ###

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

#TODO fix, fails with large reservation_lengths
def process_new_invitation(invitation_type, poll_id, resource_id,
                                reservation_length):

    if 'user_id' not in session:
        return False
    print(invitation_type)
    if invitation_type == 'poll_participant':
        #check if user has rights to do the operation
        #and that the target poll exists
        if not user_owns_poll(poll_id):
            print("does not own")
            return False

        #TODO
        #check reservation_length
        url_id = urandom(16).hex()

        sql = "INSERT INTO PollMembershipLinks \
               (poll_id, url_id, reservation_length)\
               VALUES (:poll_id, :url_id, :reservation_length)"

        #TODO find out a good way to put the reservation length to the
        #database
        #why is it string?
        reservation_length = str(int(reservation_length)*60)
        db.session.execute(sql, {'poll_id': poll_id, 'url_id': url_id,
                                 'reservation_length': reservation_length})
        db.session.commit()
        return True
    if invitation_type == 'resource_owner':
        #check user is the owner of the resource parent poll
        if not user_owns_parent_poll(resource_id):
            print("user does not own the resource")
            return False

        url_id = urandom(16).hex()

        sql = "INSERT INTO ResourceMembershipLinks \
               (resource_id, url_id) VALUES (:resource_id, :url_id)"
        db.session.execute(sql, {'resource_id': resource_id, 'url_id': url_id})
        db.session.commit()
        return True

    print("incorrect invitation type")
    return False

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

#adds user to a poll and initializes the user time preferences to 0
def apply_poll_invitation(url_id):
    details = participant_invitation_by_url_id(url_id)
    
    #TODO think about doing this differently
    #TODO split into functions
    poll_id = details[3]

    if user_is_participant(poll_id):
        return False

    user_id = session['user_id']
    reservation_length = details[2]

    sql = "INSERT INTO PollMembers (poll_id) VALUES (:poll_id) RETURNING id"

    member_id = db.session.execute(sql, {'poll_id': poll_id}).fetchone()

    sql = "INSERT INTO UsersPollMembers \
          (user_id, member_id, reservation_length) VALUES \
          (:user_id, :member_id, :reservation_length)"

    db.session.execute(sql, {'user_id': user_id, 'member_id': member_id[0],
                             'reservation_length': reservation_length})

    start, end = get_poll_date_range(poll_id)
    end += datetime.timedelta(days=1)

    #convert to datetime.datetime
    start = datetime.datetime(start.year, start.month, start.day)
    end = datetime.datetime(end.year, end.month, end.day)

    add_member_time_preference(member_id[0], start, end, 0)

    db.session.commit()

    return True

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
        return False

    sql = "INSERT INTO UsersResources (user_id, resource_id) \
           VALUES (:user_id, :resouce_id)"
    db.session.execute(sql, {'user_id': user_id, 'resouce_id': resource_id})
    db.session.commit()
    return True

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

#TODO check that identical resource has not already been added
def process_new_resource(poll_id, resource_description):
    if not user_owns_poll(poll_id):
        return False

    #TODO return some error message
    if resource_description_in_poll(poll_id, resource_description):
        return False

    sql = "INSERT INTO PollMembers (poll_id) VALUES (:poll_id) RETURNING id"
    member_id = db.session.execute(sql, {'poll_id': poll_id}).fetchone()

    sql = "INSERT INTO Resources (resource_description, member_id) \
            VALUES (:resource_description, :member_id)"

    db.session.execute(sql, {'resource_description': resource_description,
                             'member_id': member_id[0]})
    db.session.commit()
    return True

def get_poll_resources(poll_id):
    sql = "SELECT R.resource_description, R.resource_id FROM \
           Polls P, PollMembers M, Resources R WHERE \
           P.poll_id=M.poll_id AND M.id=R.member_id \
           AND P.poll_id=:poll_id"
    result = db.session.execute(sql, {'poll_id': poll_id})
    resources = result.fetchall()
    if resources is None:
        return []
    return resources

### Time preference related functions ###

#TODO think if I should store both ends of the interval or just the beginning
#TODO think if I need to modify the content of these
TimeInterval = namedtuple('TimeInterval', ['start', 'end', 'satisfaction'])

#time preferences for one day (date)
PreferencesDay = namedtuple('PreferencesDay', ['date', 'intervals'])

#type(day) = datetime.date
#get an ordered list of time intervals that overlap with 'day'
def get_member_time_preferences_for_day(member_id, day):
    sql = "SELECT GREATEST(time_beginning, :day),\
           LEAST(time_end, :day + '1 day'::interval), satisfaction FROM \
           MemberTimeSelections WHERE member_id=:member_id \
           AND time_end > :day AND time_beginning < (:day + '1 day'::interval)\
           ORDER BY time_beginning"

    result = db.session.execute(sql, {'member_id': member_id,
                                      'day':day}).fetchall()

    #print("result: ", result)
    if result is None:
        return []

    return [TimeInterval(*x) for x in result]

#TODO think if this should return a named tuple
def get_time_preferences(member_id, first_date, last_date):
    result = []
    i = first_date
    while i <= last_date:
        tmp = get_member_time_preferences_for_day(member_id, i)
        result.append(PreferencesDay(i,  tmp))
        i += datetime.timedelta(days=1)

    return result

def get_user_time_preferences(user_id, poll_id):
    first_date, last_date = get_poll_date_range(poll_id)
    member_id = get_user_poll_member_id(user_id, poll_id)
    print("userid, memberid", user_id, member_id, poll_id)
    print(first_date, last_date)
    return get_time_preferences(member_id, first_date, last_date)


#TODO output to datetime.date
def get_poll_date_range(poll_id):
    sql = "SELECT first_appointment_date, last_appointment_date FROM \
           Polls WHERE poll_id=:poll_id"
    poll = db.session.execute(sql, {'poll_id': poll_id}).fetchone()
    if poll is None:
        return None
    return poll

#Modifies existing time preference intervals so that truncates
#partially overlapping intervals and removes completely overlapping intervals
#and then adds the new inteval
#start and end are datetime.datetime
def add_member_time_preference(member_id, start, end, satisfaction):
    #fetch a segment inside which the new segment is
    #ooooooo
    # nnnn
    sql = "SELECT * FROM MemberTimeSelections WHERE member_id=:member_id \
           AND time_beginning < :start AND time_end > :end"

    result = db.session.execute(sql, {'member_id': member_id, 'start': start,
                             'end': end}).fetchone()

    if result is not None:
        sql = "DELETE FROM MemberTimeSelections WHERE member_id=:member_id \
               AND time_beginning < :start AND time_end > :end"
        db.session.execute(sql, {'member_id': member_id, 'start': start,
                                 'end': end})

        sql = "INSERT INTO MemberTimeSelections \
               (member_id, time_beginning, time_end, satisfaction) VALUES \
               (:member_id, :time_beginning, :time_end, :satisfaction)"
        db.session.execute(sql, {'member_id': result[0],
                                 'time_beginning': result[1],
                                 'time_end': start,
                                 'satisfaction': result[3]})

        db.session.execute(sql, {'member_id': result[0],
                                 'time_beginning': end,
                                 'time_end': result[2],
                                 'satisfaction': result[3]})


    #right side of the old segment is inside the new segment
    # ooooo
    #  nnnnnnn
    sql = "UPDATE MemberTimeSelections SET \
           time_end = :start \
           WHERE member_id=:member_id AND time_end >= :start \
           AND time_end <= :end"
    db.session.execute(sql, {'member_id': member_id, 'start': start,
                              'end': end})
    #left side of the old segment is inside the new segment
    #     ooooo
    #  nnnnnnn
    sql = "UPDATE MemberTimeSelections SET \
           time_beginning = :end \
           WHERE member_id=:member_id AND time_beginning >= :start \
           AND time_beginning <= :end"
    db.session.execute(sql, {'member_id': member_id, 'start': start,
                              'end': end})

    #remove non-positive length segments (in case these were generated by the
    #previous operations)
    sql = "DELETE FROM MemberTimeSelections WHERE member_id=:member_id \
           AND time_end<=time_beginning"
    db.session.execute(sql, {'member_id': member_id})

    #add new segment
    sql = "INSERT INTO MemberTimeSelections \
           (member_id, time_beginning, time_end, satisfaction) \
           VALUES \
           (:member_id, :start, :end, :satisfaction)"

    db.session.execute(sql, {'member_id': member_id, 'start': start,
                             'end': end, 'satisfaction': satisfaction})

    #TODO think if this function should commit.
    db.session.commit()

def process_new_time_preference(poll_id, start_time, end_time, date,
                                satisfaction):
    start_time = datetime.time.fromisoformat(start_time)
    end_time = datetime.time.fromisoformat(end_time)
    date = datetime.date.fromisoformat(date)

    user_id = session.get('user_id')
    start_datetime = datetime.datetime.combine(date, start_time)
    end_datetime = datetime.datetime.combine(date, end_time)

    if start_datetime >= end_datetime:
        print('start_datetime > end_datetime')
        return False

    if satisfaction not in ['0', '1', '2']:
        print("invalid satisfaction value")
        return False
    member_id = get_user_poll_member_id(user_id, poll_id)
    print("start_datetime, end_datetime: ", start_datetime, end_datetime)
    add_member_time_preference(member_id, start_datetime, end_datetime,
                               satisfaction)

    return True

#TODO modify SQL INSERT INTO queries so that the queries would already
#have the final parameter names. So the dict should be always: 'asdf': asdf etc

#TODO This is the db.commit() applied too early sometimes now?
#It should always be applied only when all the modifications have been
#done!
