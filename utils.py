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
    print(user_query)
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
    print(session['csrf_token'], csrf_token)
    if session['csrf_token'] != csrf_token:
        abort(403)

def process_registration(username, password):
    if username is None or not check_alphanum_string(username, 1, 20):
        return 'Username not valid'

    if password is None or len(password) == 0:
        return 'Empty password not allowed'

    sql = 'SELECT COUNT(*) FROM Users WHERE username=:username'
    user_count = db.session.execute(sql, {'username':username}).fetchone()
    print('user_count: ', user_count)

    if user_count[0] > 0:
        return 'Username already in use!'

    password_hash = generate_password_hash(password)

    print('salasana ja hash: ', password + '  ' + password_hash)

    sql = 'INSERT INTO Users (username, password_hash) \
            VALUES (:username, :password_hash)'
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
    if 'user_id' in session:
        del session['user_id']
    if 'username' in session:
        del session['username']
    if 'csrf_token' in session:
        del session['csrf_token']

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
        return 'Incorrect time/date formats!'

    if end.minute%5 != 0:
        return 'End time should be divisible by 5 minutes'
    if first_date > last_date:
        return 'The last available date cannot be before the first one!'

    if end <= datetime.datetime.today() + datetime.timedelta(seconds=2):
        return 'Poll end should not be in the past'

    if last_date - first_date > datetime.timedelta(days=30):
        return 'Poll date range cannot be longer than 31 days'

    #TODO be more descriptivie
    if name is None or len(name) < 1 or len(name) > 30:
        return 'Not valid poll name'

    if description is None or len(description) == 0 or len(description) > 10000:
        return 'Not valid poll description'

    sql = 'INSERT INTO Polls \
           (owner_user_id, poll_name, poll_description,  \
           first_appointment_date, last_appointment_date, \
           poll_end_time, has_final_results) VALUES \
           (:owner_user_id, :poll_name, :poll_description, \
           :first_appointment_date, :last_appointment_date, :poll_end_time, \
           :has_final_results)'

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

#returns list of member_ids
def get_poll_resource_members(poll_id):
    sql = 'SELECT M.id FROM PollMembers M, Resources R \
           WHERE M.id=R.member_id AND M.poll_id=:poll_id'
    member_ids = db.session.execute(sql, {'poll_id': poll_id}).fetchall()
    if member_ids is None:
        return []

    return [x[0] for x in member_ids]

#returns list of member_ids
def get_poll_customer_members(poll_id):
    sql = 'SELECT M.id FROM PollMembers M, Customers C \
           WHERE M.id=C.member_id AND M.poll_id=:poll_id'
    member_ids = db.session.execute(sql, {'poll_id': poll_id}).fetchall()
    if member_ids is None:
        return []

    return [x[0] for x in member_ids]

#returns ids of all polls that user somehow part of
#(either owner, participant or owner of a resource)
#TODO think about which of these following 4 should take user id as a parameter
#should this take some parameter?

#assumes that poll_id is an integer
def process_get_poll(poll_id):
    user_id = session.get('user_id', 0)
    sql = 'SELECT P.* FROM Polls P \
           LEFT JOIN PollMembers M ON P.id=M.poll_id \
           LEFT JOIN UsersPollMembers U ON M.id=U.member_id \
           WHERE (P.owner_user_id=:user_id OR U.user_id=:user_id) AND \
           P.id=:poll_id LIMIT 1'
    result = db.session.execute(sql, {'poll_id': poll_id, 'user_id': user_id})
    poll = result.fetchone()
    print(poll)
    if poll is None:
        return None
    return db_tuple_to_poll(poll)

def get_user_polls():
    tmp = get_user_poll_ids()
    return get_polls_by_ids(tmp)

def get_user_poll_ids():
    if 'user_id' not in session:
        return []

    polls = poll_ids_owned_by(session['user_id'])
    polls += poll_ids_where_user_is_member(session['user_id'])
    return sorted(list(set(polls)))

def poll_ids_owned_by(user_id):
    sql = 'SELECT id FROM Polls WHERE owner_user_id=:user_id'
    result = db.session.execute(sql, {'user_id':user_id})
    polls = result.fetchall()
    if polls is None:
        return []

    poll_ids = [x[0] for x in polls]
    return poll_ids

def poll_ids_where_user_is_member(user_id):
    sql = 'SELECT P.poll_id FROM PollMembers P, UsersPollMembers U \
           WHERE P.id=U.member_id AND U.user_id=:user_id'
    result = db.session.execute(sql, {'user_id':user_id})
    polls = result.fetchall()
    if polls is None:
        return []

    poll_ids = [x[0] for x in polls]
    return poll_ids

def get_polls_by_ids(poll_ids):
    if len(poll_ids) == 0:
        return []

    sql = 'SELECT * FROM Polls WHERE id in :poll_ids'
    result = db.session.execute(sql, {'poll_ids':tuple(poll_ids)})
    polls = result.fetchall()
    if polls is None:
        return []

    return [db_tuple_to_poll(x) for x in polls]

def user_owns_poll(poll_id):
    user_id = session.get('user_id', 0)

    sql = 'SELECT COUNT(*) FROM Polls WHERE id=:poll_id \
           AND owner_user_id=:user_id'
    result = db.session.execute(sql, {'poll_id': poll_id,
                                      'user_id': user_id}).fetchone()
    if result[0] > 0:
        return True
    return False

def user_is_customer(poll_id):
    user_id = session.get('user_id')

    sql = 'SELECT COUNT(*) \
           FROM PollMembers P, Customers C, UsersPollMembers U WHERE \
           P.id=C.member_id AND P.id=U.member_id AND P.poll_id=:poll_id \
           AND U.user_id=:user_id'

    tmp = db.session.execute(sql, {'poll_id': poll_id, 'user_id': user_id})
    count = tmp.fetchone()[0]
    if count > 0:
        return True

    return False

def get_poll_date_range(poll_id):
    sql = 'SELECT first_appointment_date, last_appointment_date FROM \
           Polls WHERE id=:poll_id'
    poll = db.session.execute(sql, {'poll_id': poll_id}).fetchone()
    if poll is None:
        return None
    return poll

def db_tuple_to_poll(t):
    return Poll(t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[0])

def get_user_poll_customer_member_ids(user_id, poll_id):
    sql = 'SELECT P.id FROM PollMembers P, UsersPollMembers U, \
           Customers C \
           WHERE P.id=U.member_id AND P.id=C.member_id AND \
           P.poll_id=:poll_id AND U.user_id=:user_id'

    tmp = db.session.execute(sql, {'user_id': user_id, 'poll_id': poll_id})
    member_ids = tmp.fetchall()
    if member_ids is None:
        return []

    return [x[0] for x in member_ids]

#what should these return?
#Now they just return some random things... Maybe only member_ids?
#TODO look at user.get_user_poll_member_ids and similar to these
def get_user_poll_resources(user_id, poll_id):
    sql = 'SELECT M.name, M.id FROM \
           PollMembers M, UsersPollMembers U, Resources R WHERE \
           M.id=R.member_id AND M.id=U.member_id \
           AND M.poll_id=:poll_id AND U.user_id=:user_id'

    result = db.session.execute(sql, {'user_id': user_id,
                                      'poll_id': poll_id})
    resources = result.fetchall()
    if resources is None:
        return []
    return resources

def get_poll_resources(poll_id):
    sql = 'SELECT M.name, M.id FROM \
           PollMembers M, Resources R WHERE \
           M.id=R.member_id AND M.poll_id=:poll_id'

    result = db.session.execute(sql, {'poll_id': poll_id})
    resources = result.fetchall()
    if resources is None:
        return []
    return resources

#need member_id, reservation_length, (customer_name, TODO)
def get_user_poll_customers(user_id, poll_id):
    sql = 'SELECT P.id, C.reservation_length, P.name FROM PollMembers P, UsersPollMembers U, \
           Customers C \
           WHERE P.id=U.member_id AND P.id=C.member_id AND \
           P.poll_id=:poll_id AND U.user_id=:user_id'

    tmp = db.session.execute(sql, {'user_id': user_id, 'poll_id': poll_id})
    customers = tmp.fetchall()
    if customers is None:
        return []

    return customers

def get_poll_customers(poll_id):
    sql = 'SELECT P.id, C.reservation_length, P.name \
           FROM PollMembers P, Customers C \
           WHERE P.id=C.member_id AND P.poll_id=:poll_id'

    tmp = db.session.execute(sql, {'poll_id': poll_id})
    customers = tmp.fetchall()
    if customers is None:
        return []

    return customers

def resource_name_in_poll(poll_id, resource_member_name):
    sql = 'SELECT COUNT(*) FROM PollMembers M, Resources R \
           WHERE M.id=R.member_id AND M.poll_id=:poll_id \
           AND M.name=:resource_member_name'

    tmp = db.session.execute(sql,
                            {'poll_id': poll_id,
                             'resource_member_name': resource_member_name})
    count = tmp.fetchone()
    if count[0] == 1:
        return True
    return False

def get_new_customer_links(poll_id):
    sql = 'SELECT url_id FROM NewCustomerLinks\
           WHERE poll_id=:poll_id'

    result = db.session.execute(sql, {'poll_id': poll_id})
    invitations = result.fetchall()
    #does this return none if no links were found?
    print("get_new_customer_links", invitations)
    return invitations

def get_customer_access_links(poll_id):
    sql = 'SELECT L.url_id, P.name, P.id, C.reservation_length \
           FROM PollMembers P, Customers C, MemberAccessLinks L \
           WHERE P.poll_id=:poll_id AND P.id=C.member_id \
           AND P.id=L.member_id'
    result = db.session.execute(sql, {'poll_id': poll_id})
    access_links = result.fetchall()
    return access_links

def get_resource_access_links(poll_id):
    sql = 'SELECT L.url_id, P.name, P.id \
           FROM PollMembers P, Resources R, MemberAccessLinks L \
           WHERE P.poll_id=:poll_id AND P.id=R.member_id \
           AND P.id=L.member_id'

    result = db.session.execute(sql, {'poll_id': poll_id})
    access_links = result.fetchall()
    return access_links

### Invitation related functions ###

def process_new_new_customer_link(poll_id):
    if poll_id is None:
        return 'No poll id was provided'

    if not user_owns_poll(poll_id):
        return 'User does not own the poll'

    url_id = urandom(16).hex()
    sql = 'INSERT INTO NewCustomerLinks \
           (poll_id, url_id) \
           VALUES (:poll_id, :url_id)'

    db.session.execute(sql, {'poll_id': poll_id, 'url_id': url_id})
    db.session.commit()
    return None

def process_new_member_access_link(member_id):
    if member_id is None:
        return 'No member id was provided'
    #check user is the owner of the resource parent poll
    if not user_owns_parent_poll(member_id):
        return 'User does not own the parent poll'

    url_id = urandom(16).hex()
    sql = 'INSERT INTO MemberAccessLinks \
           (member_id, url_id) VALUES (:member_id, :url_id)'
    db.session.execute(sql, {'member_id': member_id, 'url_id': url_id})
    db.session.commit()
    return None

def get_invitation_type(url_id):
    sql = 'SELECT COUNT(*) FROM NewCustomerLinks WHERE url_id=:url_id'
    result = db.session.execute(sql, {'url_id': url_id}).fetchone()
    if result[0] == 1:
        return 'poll_customer'

    sql = 'SELECT COUNT(*) FROM MemberAccessLinks WHERE url_id=:url_id'
    result = db.session.execute(sql, {'url_id': url_id}).fetchone()
    if result[0] == 1:
        return 'member_access'

    return None

def get_new_customer_link_poll_id(url_id):
    sql = 'SELECT poll_id FROM NewCustomerLinks WHERE url_id=:url_id'
    poll_id = db.session.execute(sql, {'url_id': url_id}).fetchone()
    if poll_id is None:
        return None

    return poll_id[0]

#TODO return named tuple after we know what field are necessary for it
#we need poll name, poll description, reservation length, poll_id
def customer_type_details_by_url_id(url_id):
    sql = 'SELECT P.poll_name, poll_description, P.id \
           FROM Polls P, NewCustomerLinks L \
           WHERE P.id=L.poll_id AND L.url_id=:url_id'

    result = db.session.execute(sql, {'url_id': url_id}).fetchall()
    if result is None:
        return None

    return result[0]

#we need poll name, poll description, name, member_id, poll_id, member type
#TODO it's horrible, change after modifying the database more
def member_details_by_url_id(url_id):
    sql = 'SELECT P.poll_name, P.poll_description, \
           M.name, M.id, P.id, \
           CASE \
           WHEN C.member_id IS NULL THEN \'resource\' \
           ELSE \'customer\' END \
           FROM Customers C FULL JOIN Resources R ON FALSE, \
           Polls P, PollMembers M, MemberAccessLinks L \
           WHERE P.id=M.poll_id AND \
           (M.id=R.member_id or M.id=C.member_id)\
           AND M.id=L.member_id AND L.url_id=:url_id'

    result = db.session.execute(sql, {'url_id': url_id}).fetchall()
    if result is None:
        return None

    return result[0]

def process_new_customer_url(url_id, reservation_length, customer_name):
    poll_id = get_new_customer_link_poll_id(url_id)
    if poll_id is None:
        return "No poll corresponding to the link found"
    return process_add_customer(poll_id, reservation_length, customer_name)

def process_add_customer(poll_id, reservation_length, customer_name):
    try:
        reservation_length = int(reservation_length)
    except ValueError:
        return 'Reservation length should be an integer'

    if reservation_length > 24*60:
        return 'Reservation too long (over 24 hours)'
    if reservation_length <= 0:
        return 'Reservation length cannot be negative'
    if reservation_length%5 != 0:
        return 'Reservation length should be divisible by 5 min'

    if customer_name is None or len(customer_name) == 0:
        return 'Customer name missing'
    if len(customer_name) > 30:
        return 'Customer name too long (over 30 characters)'

    user_id = session.get('user_id')
    member_id = add_new_customer(poll_id, reservation_length, customer_name)
    print('process_new_customer_url ', member_id)
    give_access_to_member(user_id, member_id)
    db.session.commit()
    return None

#returns member_id
#assumes that parameters are correct
#reservation_length is in minutes
def add_new_customer(poll_id, reservation_length, name):
    sql = 'INSERT INTO PollMembers (poll_id, name) \
           VALUES (:poll_id, :name) RETURNING id'
    member_id = db.session.execute(sql, {'poll_id': poll_id,
                                         'name': name}).fetchone()[0]

    reservation_length = str(reservation_length*60)
    sql = 'INSERT INTO Customers \
           (member_id, reservation_length) VALUES \
           (:member_id, :reservation_length)'
    db.session.execute(sql, {'member_id': member_id,
                             'reservation_length': reservation_length})
    initialize_poll_member_times(member_id, poll_id, 0)
    return member_id

def process_access(url_id):
    member_id = get_member_id(url_id)
    if member_id is None:
        return "No member id corresponding to url was found"

    user_id = session['user_id']
    error = give_access_to_member(user_id, member_id)
    if error is not None:
        return error

    db.session.commit()
    return None

def get_member_id(url_id):
    sql = 'SELECT member_id FROM MemberAccessLinks WHERE url_id=:url_id'
    member_id = db.session.execute(sql, {'url_id': url_id}).fetchone()
    if member_id is None:
        return None
    return member_id[0]

def process_delete_new_customer_link(url_id):
    user_id = session.get('user_id')
    error = delete_new_customer_link(url_id, user_id)
    if error is not None:
        return error
    db.session.commit()
    return None

def delete_new_customer_link(url_id, owner_user_id):
    sql = 'DELETE FROM NewCustomerLinks L USING Polls P \
            WHERE P.id=L.poll_ID AND P.owner_user_id=:owner_user_id AND \
            L.url_id=:url_id RETURNING 1'
    deleted = db.session.execute(sql, {'url_id': url_id,
                                     'owner_user_id': owner_user_id})
    deleted = deleted.fetchone()

    if deleted is None:
        return "User does not own the link or the link doesn't exist"

    return None

def process_delete_member_access_link(url_id):
    user_id = session.get('user_id')
    error = delete_member_access_link(url_id, user_id)
    if error is not None:
        return error
    db.session.commit()
    return None

def delete_member_access_link(url_id, owner_user_id):
    sql = 'DELETE FROM MemberAccessLinks L USING Polls P, PollMembers M \
           WHERE P.id=M.poll_id AND M.id=L.member_id \
           AND P.owner_user_id=:owner_user_id AND \
           L.url_id=:url_id RETURNING 1'
    deleted = db.session.execute(sql, {'url_id': url_id,
                                     'owner_user_id': owner_user_id})
    deleted = deleted.fetchone()

    if deleted is None:
        return "User does not own the link or the link doesn't exist"

    return None

### Member related functions ###

def get_customer_reservation_length(member_id):
    sql = 'SELECT reservation_length FROM Customers WHERE member_id=:member_id'
    length = db.session.execute(sql, {'member_id': member_id}).fetchone()

    if length is None:
        return None

    return length[0]

#TODO remove poll_id from the parameters!
def initialize_poll_member_times(member_id, poll_id, grade):
    start, end = get_poll_date_range(poll_id)
    end += datetime.timedelta(days=1)

    #convert to datetime.datetime
    start = datetime.datetime(start.year, start.month, start.day)
    end = datetime.datetime(end.year, end.month, end.day)

    times.add_member_time_grading(member_id, start, end, grade)

def get_member_type(member_id):
    sql = 'SELECT CASE \
           WHEN COUNT(C.member_id) > 0 THEN \'customer\' \
           WHEN COUNT(R.member_id) > 0 THEN \'resource\' \
           END \
           FROM Customers C FULL JOIN Resources R ON FALSE WHERE \
           C.member_id=:member_id OR R.member_id=:member_id'

    member_type = db.session.execute(sql, {'member_id': member_id}).fetchone()
    print('member_type[0] ', member_type[0])
    if member_type[0] is None:
        return None
    return member_type[0]

def user_owns_parent_poll(member_id):
    sql = 'SELECT COUNT(*) FROM Polls P, PollMembers M \
           WHERE P.id=M.poll_id AND M.id=:member_id \
           AND P.owner_user_id=:user_id'

    user_id = session.get('user_id')
    count = db.session.execute(sql, {'user_id': user_id,
                                     'member_id': member_id}).fetchone()
    if count[0] == 1:
        return True
    if count[0] > 1:
        print('ERROR! count should not be > 1')
        return False

    return False

def member_in_poll(member_id, poll_id):
    sql = 'SELECT COUNT(*) FROM PollMembers WHERE id=:member_id \
           AND poll_id=:poll_id'

    count = db.session.execute(sql, {'member_id': member_id,
                                     'poll_id': poll_id}).fetchone()

    if count[0] == 1:
        return True

    return False


#TODO how should this be named? should be separate from having
#an access through poll ownership
def user_has_access(user_id, member_id):
    sql = 'SELECT COUNT(*) FROM UsersPollMembers WHERE \
           member_id=:member_id AND user_id=:user_id'

    count = db.session.execute(sql, {'user_id': user_id,
                                     'member_id': member_id}).fetchone()
    if count[0] == 1:
        return True
    if count[0] == 0:
        return False

#NOTE fails if user_id is not in users!
def give_access_to_member(user_id, member_id):
    if user_has_access(user_id, member_id):
        return 'User already has access to the poll member'

    sql = 'INSERT INTO UsersPollMembers (user_id, member_id) \
           VALUES (:user_id, :member_id)'
    db.session.execute(sql, {'user_id': user_id, 'member_id': member_id})
    return None

def get_member_name(member_id):
    sql = 'SELECT name FROM PollMembers WHERE id=:member_id'

    result = db.session.execute(sql, {'member_id': member_id}).fetchone()
    if result is None:
        return ''

    return result[0]

def process_new_resource(poll_id, resource_name):
    print('process_new_resource', poll_id)

    if poll_id is None:
        return 'No poll id was provided'
    if resource_name is None or len(resource_name) == 0:
        return 'No resource name was provided'
    if len(resource_name) > 10000:
        return 'Resource name too long (> 10000 characters)'

    if not user_owns_poll(poll_id):
        return 'User does not own the poll'

    if resource_name_in_poll(poll_id, resource_name):
        return 'Resource with an identical resource name already \
                exists in the poll'

    sql = 'INSERT INTO PollMembers (poll_id, name) VALUES \
           (:poll_id, :resource_name) RETURNING id'
    result = db.session.execute(sql, {'poll_id': poll_id,
                                         'resource_name': resource_name})
    member_id = result.fetchone()

    sql = 'INSERT INTO Resources (member_id) \
            VALUES (:member_id)'

    db.session.execute(sql, {'member_id': member_id[0]})

    initialize_poll_member_times(member_id[0], poll_id, 0)
    db.session.commit()

    return None

def process_modify_customer(member_id, reservation_length):
    print(member_id, reservation_length)
    try:
        member_id = int(member_id)
        reservation_length = int(reservation_length)
    except:
        return 'Inputs were not integers'

    if reservation_length <= 0:
        return 'Reservation length has to be positive'

    if reservation_length % 5 != 0:
        return 'Reservation length has to be divisible by 5 min'

    #TODO this should probably be done elsewhere so we could easily allow
    #also other users than the admin to modify the customer
    if not user_owns_parent_poll(member_id):
        return 'User has no rights to modify the customer'

    error = update_reservation_length(member_id, reservation_length)
    if error is None:
        db.session.commit()
    return error

#reservation_length should is in minutes
def update_reservation_length(member_id, reservation_length):
    #to seconds
    length_str = str(reservation_length*60)
    sql = 'UPDATE Customers SET reservation_length=:length_str \
           WHERE member_id=:member_id'

    db.session.execute(sql, {'member_id': member_id,
                             'length_str': length_str})
    return None

def process_delete_member(member_id):
    try:
        member_id = int(member_id)
    except:
        return "Member id not an interger"

    if not user_owns_parent_poll(member_id):
        return "User has no rights to delete the member"

    #TODO check if the poll has final results. In that case, don't proceed

    delete_member(member_id)
    db.session.commit()

#member id should be an integer
#does not check any rights
def delete_member(member_id):
    sql = 'DELETE FROM PollMembers WHERE id=:member_id'
    db.session.execute(sql, {'member_id': member_id})
