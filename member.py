from db import db
from flask import session, abort
from werkzeug.security import check_password_hash, generate_password_hash
from os import urandom

import datetime
from collections import namedtuple
import times
import poll

### Member related functions ###

def get_customer_reservation_length(member_id):
    sql = 'SELECT reservation_length FROM Customers WHERE member_id=:member_id'
    length = db.session.execute(sql, {'member_id': member_id}).fetchone()

    if length is None:
        return None
    return length[0]

def initialize_poll_member_times(member_id, grade):
    start, end = get_parent_poll_datetime_range(member_id)
    times.add_member_time_grading(member_id, start, end, grade)

def get_member_type(member_id):
    sql = 'SELECT C.reservation_length \
           FROM PollMembers P LEFT JOIN Customers C \
           ON P.id=C.member_id WHERE P.id=:member_id'

    details = db.session.execute(sql, {'member_id': member_id}).fetchone()

    if details is None:
        return None

    if details[0] is None:
        member_type = 'resource'
    else:
        member_type = 'customer'

    return member_type

def get_parent_poll_phase(member_id):
    sql = 'SELECT P.end_time, P.has_final_results FROM Polls P, \
           PollMembers M WHERE P.id=M.poll_id AND M.id=:member_id'
    result = db.session.execute(sql, {'member_id': member_id}).fetchone()
    if result is None:
        return None
    return poll.poll_details_to_phase(result[0], result[1])

def get_parent_poll_details(member_id):
    sql = 'SELECT P.* FROM Polls P, PollMembers M WHERE P.id=M.poll_id \
           AND M.id=:member_id'
    poll_data = db.session.execute(sql, {'member_id': member_id}).fetchone()
    if poll_data is None:
        return None

    phase = poll.poll_details_to_phase(poll_data[6], poll_data[7])
    return poll.Poll(*poll_data, phase)

def user_owns_parent_poll(member_id):
    sql = 'SELECT COUNT(*) FROM Polls P, PollMembers M \
           WHERE P.id=M.poll_id AND M.id=:member_id \
           AND P.owner_user_id=:user_id'
    user_id = session.get('user_id')
    count = db.session.execute(sql, {'user_id': user_id,
                                     'member_id': member_id}).fetchone()
    return count[0] > 0

# TODO how should this be named? should be separate from having
# an access through poll ownership
def user_has_access(user_id, member_id):
    sql = 'SELECT COUNT(*) FROM UsersPollMembers WHERE \
           member_id=:member_id AND user_id=:user_id'

    count = db.session.execute(sql, {'user_id': user_id,
                                     'member_id': member_id}).fetchone()
    return count[0] > 0

# NOTE fails if user_id is not in users!
def give_user_access_to_member(user_id, member_id):
    if user_has_access(user_id, member_id):
        return 'User already has access to the poll member'

    sql = 'INSERT INTO UsersPollMembers (user_id, member_id) \
           VALUES (:user_id, :member_id)'
    db.session.execute(sql, {'user_id': user_id, 'member_id': member_id})
    return None

MemberDetails = namedtuple('MemberDetails', ['name', 'poll_id', 'reservation_length', 'type'])
#assumes that member_id exists
def get_member_details(member_id):
    sql = 'SELECT P.name, P.poll_id, C.reservation_length \
           FROM PollMembers P LEFT JOIN Customers C \
           ON P.id=C.member_id WHERE P.id=:member_id'

    details = db.session.execute(sql, {'member_id': member_id}).fetchone()

    if details[2] is None:
        member_type = 'resource'
    else:
        member_type = 'customer'
    return MemberDetails(*details, member_type)


def process_modify_customer(member_id, reservation_length):
    try:
        member_id = int(member_id)
        reservation_length = int(reservation_length)
    except:
        return 'Inputs were not integers'
    if reservation_length <= 0:
        return 'Reservation length has to be positive'
    if reservation_length % 5 != 0:
        return 'Reservation length has to be divisible by 5 min'
    # TODO this should probably be done elsewhere so we could easily allow
    # also other users than the admin to modify the customer
    if not user_owns_parent_poll(member_id):
        return 'User has no rights to modify the customer'
    #from now on, assume that member_id is valid

    if get_parent_poll_phase(member_id) == 2:
        return 'Poll in the final result phase'

    error = update_reservation_length(member_id, reservation_length)
    if error is None:
        db.session.commit()
    return error

# reservation_length should is in minutes
def update_reservation_length(member_id, reservation_length):
    # to seconds
    length_str = str(reservation_length*60)
    sql = 'UPDATE Customers SET reservation_length=:length_str \
           WHERE member_id=:member_id'
    db.session.execute(sql, {'member_id': member_id, 'length_str': length_str})
    return None

def process_delete_member(member_id):
    try:
        member_id = int(member_id)
    except:
        return 'Member id not an interger'
    if not user_owns_parent_poll(member_id):
        return 'User has no rights to delete the member'
    if get_parent_poll_phase(member_id) == 2:
        return 'Poll in the final results phase'

    delete_member(member_id)
    db.session.commit()

# member id should be an integer
# does not check any rights
def delete_member(member_id):
    sql = 'DELETE FROM PollMembers WHERE id=:member_id'
    db.session.execute(sql, {'member_id': member_id})

def get_parent_poll_datetime_range(member_id):
    sql = 'SELECT P.first_appointment_date, P.last_appointment_date FROM \
            Polls P, PollMembers M WHERE P.id=M.poll_id AND M.id=:member_id'
    start, end = db.session.execute(sql, {'member_id': member_id}).fetchone()
    start = datetime.datetime.combine(start, datetime.time(0, 0, 0))
    end += datetime.timedelta(days=1)
    end = datetime.datetime.combine(end, datetime.time(0, 0, 0))
    return (start, end)
