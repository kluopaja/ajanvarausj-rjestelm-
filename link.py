from db import db
from flask import session, abort
from werkzeug.security import check_password_hash, generate_password_hash
from os import urandom

import datetime
from collections import namedtuple
import times
import poll
import member

### Invitation related functions ###

def process_new_new_customer_link(poll_id):
    if poll_id is None:
        return 'No poll id was provided'

    if not poll.user_owns_poll(poll_id):
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
    if not member.user_owns_parent_poll(member_id):
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
    return poll.process_add_customer(poll_id, reservation_length, customer_name)

def process_access(url_id):
    member_id = get_member_id(url_id)
    if member_id is None:
        return "No member id corresponding to url was found"

    user_id = session['user_id']
    error = member.give_user_access_to_member(user_id, member_id)
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
