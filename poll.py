from db import db
from flask import session, abort
from werkzeug.security import check_password_hash, generate_password_hash
from os import urandom
import base64

import datetime
from collections import namedtuple
import times
import member


### Poll related functions ###
Poll = namedtuple('Poll', ['id', 'owner_user_id', 'name', 'description',
                           'first_appointment_date', 'last_appointment_date',
                           'end_time', 'has_final_results'])

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
    # TODO be more descriptivie
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

# 0 = running
# 1 = ended
# 2 = final results
def get_poll_phase(poll_id):
    sql = "SELECT poll_end_time, has_final_results FROM Polls \
           WHERE id=:poll_id"
    result = db.session.execute(sql, {'poll_id': poll_id}).fetchone()
    if result[1]:
        return 2
    current_time = datetime.datetime.today()
    if current_time > result[0]:
        return 1
    return 0

def poll_details_to_phase(poll_end_time, has_final_results):
    if has_final_results:
        return 2
    current_time = datetime.datetime.today()
    if current_time > poll_end_time:
        return 1
    return 0

# returns list of member_ids
def get_poll_resource_members(poll_id):
    sql = 'SELECT M.id FROM PollMembers M, Resources R \
           WHERE M.id=R.member_id AND M.poll_id=:poll_id'
    member_ids = db.session.execute(sql, {'poll_id': poll_id}).fetchall()
    return [x[0] for x in member_ids]

# returns list of member_ids
def get_poll_customer_members(poll_id):
    sql = 'SELECT M.id FROM PollMembers M, Customers C \
           WHERE M.id=C.member_id AND M.poll_id=:poll_id'
    member_ids = db.session.execute(sql, {'poll_id': poll_id}).fetchall()
    return [x[0] for x in member_ids]

# returns ids of all polls that user somehow part of
# (either owner, participant or owner of a resource)
# TODO think about which of these following 4 should take user id as a parameter
# should this take some parameter?

# assumes that poll_id is an integer
def process_get_poll(poll_id):
    user_id = session.get('user_id', 0)
    sql = 'SELECT P.* FROM Polls P \
           LEFT JOIN PollMembers M ON P.id=M.poll_id \
           LEFT JOIN UsersPollMembers U ON M.id=U.member_id \
           WHERE (P.owner_user_id=:user_id OR U.user_id=:user_id) AND \
           P.id=:poll_id LIMIT 1'
    poll_data = db.session.execute(sql, {'poll_id': poll_id,
                                         'user_id': user_id}).fetchone()
    if poll_data is None:
        return None

    return Poll(*poll_data)

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
    polls = db.session.execute(sql, {'user_id':user_id}).fetchall()
    return [x[0] for x in polls]

def poll_ids_where_user_is_member(user_id):
    sql = 'SELECT P.poll_id FROM PollMembers P, UsersPollMembers U \
           WHERE P.id=U.member_id AND U.user_id=:user_id'
    polls = db.session.execute(sql, {'user_id':user_id}).fetchall()
    return [x[0] for x in polls]

def get_polls_by_ids(poll_ids):
    if len(poll_ids) == 0:
        return []

    sql = 'SELECT * FROM Polls WHERE id in :poll_ids'
    polls = db.session.execute(sql, {'poll_ids':tuple(poll_ids)}).fetchall()
    return [Poll(*x) for x in polls]

# check if this fails with poll_id=None
def user_owns_poll(poll_id):
    user_id = session.get('user_id', 0)
    sql = 'SELECT COUNT(*) FROM Polls WHERE id=:poll_id \
           AND owner_user_id=:user_id'
    count = db.session.execute(sql, {'poll_id': poll_id,
                                     'user_id': user_id}).fetchone()
    return count[0] > 0

def user_is_customer(poll_id):
    user_id = session.get('user_id')
    sql = 'SELECT COUNT(*) \
           FROM PollMembers P, Customers C, UsersPollMembers U WHERE \
           P.id=C.member_id AND P.id=U.member_id AND P.poll_id=:poll_id \
           AND U.user_id=:user_id'
    count = db.session.execute(sql, {'poll_id': poll_id,
                                     'user_id': user_id}).fetchone()
    return count[0] > 0

def get_poll_date_range(poll_id):
    sql = 'SELECT first_appointment_date, last_appointment_date FROM \
           Polls WHERE id=:poll_id'
    poll = db.session.execute(sql, {'poll_id': poll_id}).fetchone()
    return poll

def get_user_poll_customer_member_ids(user_id, poll_id):
    sql = 'SELECT P.id FROM PollMembers P, UsersPollMembers U, \
           Customers C \
           WHERE P.id=U.member_id AND P.id=C.member_id AND \
           P.poll_id=:poll_id AND U.user_id=:user_id'
    member_ids = db.session.execute(sql, {'user_id': user_id,
                                          'poll_id': poll_id}).fetchall()
    return [x[0] for x in member_ids]

# what should these return?
# Now they just return some random things... Maybe only member_ids?
# TODO look at user.get_user_poll_member_ids and similar to these
def get_user_poll_resources(user_id, poll_id):
    sql = 'SELECT M.name, M.id FROM \
           PollMembers M, UsersPollMembers U, Resources R WHERE \
           M.id=R.member_id AND M.id=U.member_id \
           AND M.poll_id=:poll_id AND U.user_id=:user_id'
    resources = db.session.execute(sql, {'user_id': user_id,
                                         'poll_id': poll_id}).fetchall()
    return resources

def get_poll_resources(poll_id):
    sql = 'SELECT M.name, M.id FROM \
           PollMembers M, Resources R WHERE \
           M.id=R.member_id AND M.poll_id=:poll_id'
    resources = db.session.execute(sql, {'poll_id': poll_id}).fetchall()
    return resources

# need member_id, reservation_length, member_name
def get_user_poll_customers(user_id, poll_id):
    sql = 'SELECT P.id, C.reservation_length, P.name FROM PollMembers P, UsersPollMembers U, \
           Customers C \
           WHERE P.id=U.member_id AND P.id=C.member_id AND \
           P.poll_id=:poll_id AND U.user_id=:user_id'
    customers = db.session.execute(sql, {'user_id': user_id,
                                         'poll_id': poll_id}).fetchall()
    return customers

def get_poll_customers(poll_id):
    sql = 'SELECT P.id, C.reservation_length, P.name \
           FROM PollMembers P, Customers C \
           WHERE P.id=C.member_id AND P.poll_id=:poll_id'
    customers = db.session.execute(sql, {'poll_id': poll_id}).fetchall()
    return customers

def resource_name_in_poll(poll_id, resource_member_name):
    sql = 'SELECT COUNT(*) FROM PollMembers M, Resources R \
           WHERE M.id=R.member_id AND M.poll_id=:poll_id \
           AND M.name=:resource_member_name'
    count = db.session.execute(sql,
                             {'poll_id': poll_id,
                              'resource_member_name': resource_member_name}).fetchone()
    return count[0] > 0

def customer_name_in_poll(poll_id, name):
    sql = 'SELECT COUNT(*) FROM PollMembers M, Customers C \
           WHERE M.id=C.member_id AND M.poll_id=:poll_id \
           AND M.name=:name'
    count = db.session.execute(sql,
                             {'poll_id': poll_id, 'name': name}).fetchone()
    return count[0] > 0

# TODO should this return a list of string, not a list of tuples?
def get_new_customer_links(poll_id):
    sql = 'SELECT url_id FROM NewCustomerLinks\
           WHERE poll_id=:poll_id'

    links = db.session.execute(sql, {'poll_id': poll_id}).fetchall()
    return links

def get_customer_access_links(poll_id):
    sql = 'SELECT L.url_id, P.name, P.id, C.reservation_length \
           FROM PollMembers P, Customers C, MemberAccessLinks L \
           WHERE P.poll_id=:poll_id AND P.id=C.member_id \
           AND P.id=L.member_id'
    access_links = db.session.execute(sql, {'poll_id': poll_id}).fetchall()
    return access_links

def get_resource_access_links(poll_id):
    sql = 'SELECT L.url_id, P.name, P.id \
           FROM PollMembers P, Resources R, MemberAccessLinks L \
           WHERE P.poll_id=:poll_id AND P.id=R.member_id \
           AND P.id=L.member_id'
    access_links = db.session.execute(sql, {'poll_id': poll_id}).fetchall()
    return access_links
def check_new_customer_attributes(reservation_length, customer_name):
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
    return None

def process_add_customer(poll_id, reservation_length, customer_name,
                         from_url=False):
    if not user_owns_poll(poll_id):
        return 'No rights to add a new customer to the poll'
    # now we know that poll_id is valid

    if get_poll_phase(poll_id) == 2:
        return 'Poll in the final results phase'

    error = check_new_customer_attributes(reservation_length, customer_name)
    if error is not None:
        return error

    error = add_new_customer(poll_id, reservation_length, customer_name)
    if error is not None:
        return error

    db.session.commit()
    return None

def create_unique_customer_name(poll_id, name):
    name_candidate = name
    for i in range(5):
        print(name_candidate)
        if not customer_name_in_poll(poll_id, name_candidate):
            return name_candidate
        name_candidate = name + "-" + create_random_name_suffix()

    return None

def create_unique_resource_name(poll_id, name):
    name_candidate = name
    for i in range(5):
        print(name_candidate)
        if not resource_name_in_poll(poll_id, name_candidate):
            return name_candidate
        name_candidate = name + "-" + create_random_name_suffix()

    return None

def create_random_name_suffix():
    return base64.urlsafe_b64encode(urandom(3)).decode('ascii')

def name_is_unique(poll_id, name):
    sql = "SELECT COUNT(*) FROM PollMembers WHERE poll_id=:poll_id \
           AND name=:name"
    count = db.session.execute(sql, {'poll_id': poll_id,
                                     'name': name}).fetchone()
    return count[0] == 0

def process_new_resource(poll_id, resource_name):
    if poll_id is None:
        return 'No poll id was provided'
    if resource_name is None or len(resource_name) == 0:
        return 'No resource name was provided'
    if len(resource_name) > 30:
        return 'Resource name too long (> 30 characters)'
    if not user_owns_poll(poll_id):
        return 'User does not own the poll'
    if get_poll_phase(poll_id) == 2:
        return 'Poll in the final results phase'

    unique_name = create_unique_resource_name(poll_id, resource_name)
    if unique_name is None:
        return "Failed to create a unique resource name"

    sql = 'INSERT INTO PollMembers (poll_id, name) VALUES \
           (:poll_id, :resource_name) RETURNING id'
    member_id = db.session.execute(sql,
                                   {'poll_id': poll_id,
                                    'resource_name': unique_name}).fetchone()

    sql = 'INSERT INTO Resources (member_id) VALUES (:member_id)'
    db.session.execute(sql, {'member_id': member_id[0]})

    member.initialize_poll_member_times(member_id[0], poll_id, 0)
    db.session.commit()
    return None

# assumes that parameters are in correct format
# reservation_length is in minutes (str)
def add_new_customer(poll_id, reservation_length, name):
    user_id = session.get('user_id')
    name = create_unique_customer_name(poll_id, name)
    if name is None:
        return "Failed to create a unique customer name"

    sql = 'INSERT INTO PollMembers (poll_id, name) \
           VALUES (:poll_id, :name) RETURNING id'

    member_id = db.session.execute(sql, {'poll_id': poll_id,
                                         'name': name}).fetchone()

    reservation_length = str(int(reservation_length)*60)
    sql = 'INSERT INTO Customers \
           (member_id, reservation_length) VALUES \
           (:member_id, :reservation_length)'
    db.session.execute(sql, {'member_id': member_id[0],
                             'reservation_length': reservation_length})

    member.initialize_poll_member_times(member_id[0], poll_id, 0)
    member.give_user_access_to_member(user_id, member_id[0])
    return None

def member_in_poll(member_id, poll_id):
    sql = 'SELECT COUNT(*) FROM PollMembers WHERE id=:member_id \
           AND poll_id=:poll_id'
    count = db.session.execute(sql, {'member_id': member_id,
                                     'poll_id': poll_id}).fetchone()
    return count[0] > 0
