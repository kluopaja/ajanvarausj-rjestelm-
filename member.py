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

#TODO remove poll_id from the parameters!
def initialize_poll_member_times(member_id, poll_id, grade):
    start, end = poll.get_poll_date_range(poll_id)
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
def give_user_access_to_member(user_id, member_id):
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
