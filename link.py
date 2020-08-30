from db import db
from flask import session, abort
from werkzeug.security import check_password_hash, generate_password_hash
from os import urandom
import base64

import datetime
from collections import namedtuple
import times
import poll
import member

### Invitation related functions ###

def create_new_url_key():
    return base64.urlsafe_b64encode(urandom(15)).decode('ascii')

def process_new_new_customer_link(poll_id):
    if poll_id is None:
        return 'No poll id was provided'
    if not poll.user_owns_poll(poll_id):
        return 'User does not own the poll'

    url_key = create_new_url_key()
    sql = 'INSERT INTO NewCustomerLinks \
           (poll_id, url_key) \
           VALUES (:poll_id, :url_key)'
    db.session.execute(sql, {'poll_id': poll_id, 'url_key': url_key})
    db.session.commit()
    return None

def process_new_member_access_link(member_id):
    if member_id is None:
        return 'No member id was provided'
    # check user is the owner of the resource parent poll
    if not member.user_owns_parent_poll(member_id):
        return 'User does not own the parent poll'

    url_key = create_new_url_key()
    sql = 'INSERT INTO MemberAccessLinks \
           (member_id, url_key) VALUES (:member_id, :url_key)'
    db.session.execute(sql, {'member_id': member_id, 'url_key': url_key})
    db.session.commit()
    return None

def get_invitation_type(url_key):
    sql = 'SELECT COUNT(*) FROM NewCustomerLinks WHERE url_key=:url_key'
    count = db.session.execute(sql, {'url_key': url_key}).fetchone()

    if count[0] > 0:
        return 'poll_customer'

    sql = 'SELECT COUNT(*) FROM MemberAccessLinks WHERE url_key=:url_key'
    count = db.session.execute(sql, {'url_key': url_key}).fetchone()

    if count[0] > 0:
        return 'member_access'
    return None

def get_new_customer_link_poll_id(url_key):
    sql = 'SELECT poll_id FROM NewCustomerLinks WHERE url_key=:url_key'
    poll_id = db.session.execute(sql, {'url_key': url_key}).fetchone()

    if poll_id is None:
        return None
    return poll_id[0]

# TODO return named tuple after we know what field are necessary for it
# we need poll name, poll description, reservation length, poll_id
def customer_type_details_by_url_key(url_key):
    sql = 'SELECT P.name, P.description, P.id \
           FROM Polls P, NewCustomerLinks L \
           WHERE P.id=L.poll_id AND L.url_key=:url_key'
    return db.session.execute(sql, {'url_key': url_key}).fetchone()

# we need poll name, poll description, name, member_id, poll_id, member type
# TODO it's horrible, change after modifying the database more
def member_details_by_url_key(url_key):
    sql = 'SELECT P.name, P.description, \
           M.name, M.id, P.id, \
           CASE \
           WHEN C.member_id IS NULL THEN \'resource\' \
           ELSE \'customer\' END \
           FROM Customers C FULL JOIN Resources R ON FALSE, \
           Polls P, PollMembers M, MemberAccessLinks L \
           WHERE P.id=M.poll_id AND \
           (M.id=R.member_id or M.id=C.member_id)\
           AND M.id=L.member_id AND L.url_key=:url_key'

    return db.session.execute(sql, {'url_key': url_key}).fetchone()

def process_new_customer_url(url_key, reservation_length, customer_name):
    poll_id = get_new_customer_link_poll_id(url_key)
    if poll_id is None:
        return 'No poll corresponding to the link found'
    if poll.get_poll_phase(poll_id) >= 1:
        return 'Poll has ended.'

    error = poll.check_new_customer_attributes(reservation_length,
                                               customer_name)
    if error is not None:
        return error

    error = poll.add_new_customer(poll_id, reservation_length, customer_name)
    if error is not None:
        return error

    update_new_customer_link_usage(url_key)
    db.session.commit()
    return None

def update_new_customer_link_usage(url_key):
    sql = 'UPDATE NewCustomerLinks SET times_used=times_used+1 WHERE url_key=:url_key'

    db.session.execute(sql, {'url_key': url_key})

def process_access(url_key):
    member_id = get_member_id(url_key)
    if member_id is None:
        return 'No member id corresponding to url was found'
    if member.get_parent_poll_phase(member_id) >= 1:
        return 'Poll has ended'
    user_id = session['user_id']
    error = member.give_user_access_to_member(user_id, member_id)
    if error is not None:
        return error

    db.session.commit()
    return None

def get_member_id(url_key):
    sql = 'SELECT member_id FROM MemberAccessLinks WHERE url_key=:url_key'
    member_id = db.session.execute(sql, {'url_key': url_key}).fetchone()
    if member_id is None:
        return None
    return member_id[0]

def process_delete_new_customer_link(url_key):
    user_id = session.get('user_id')
    error = delete_new_customer_link(url_key, user_id)
    # Note that this is not checked for the poll state since it doesn't
    # really matter even if the user could delete some of these
    if error is not None:
        return error
    db.session.commit()
    return None

def delete_new_customer_link(url_key, owner_user_id):
    sql = 'DELETE FROM NewCustomerLinks L USING Polls P \
            WHERE P.id=L.poll_ID AND P.owner_user_id=:owner_user_id AND \
            L.url_key=:url_key RETURNING 1'
    deleted = db.session.execute(sql, {'url_key': url_key,
                                     'owner_user_id': owner_user_id}).fetchone()
    if deleted is None:
        return 'User does not own the link or the link does not exist'

    return None

def process_delete_member_access_link(url_key):
    user_id = session.get('user_id')
    error = delete_member_access_link(url_key, user_id)
    # Note that this is not checked for the poll state since it doesn't
    # really matter even if the user could delete some of these
    if error is not None:
        return error
    db.session.commit()
    return None

def delete_member_access_link(url_key, owner_user_id):
    sql = 'DELETE FROM MemberAccessLinks L USING Polls P, PollMembers M \
           WHERE P.id=M.poll_id AND M.id=L.member_id \
           AND P.owner_user_id=:owner_user_id AND \
           L.url_key=:url_key RETURNING 1'
    deleted = db.session.execute(sql, {'url_key': url_key,
                                     'owner_user_id': owner_user_id}).fetchone()

    if deleted is None:
        return 'User does not own the link or the link does not exist'
    return None
