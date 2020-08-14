import datetime
from collections import namedtuple
from db import db
import utils
import optimization

### Time preference related functions ###

#TODO think if I should store both ends of the interval or just the beginning
#TODO think if I need to modify the content of these
TimeInterval = namedtuple('TimeInterval', ['start', 'end', 'grade'])

#time preferences for one day (date)
PreferencesDay = namedtuple('PreferencesDay', ['date', 'intervals'])

#type(day) = datetime.date
#get an ordered list of time intervals that overlap with 'day'
def get_member_preferences_for_day(member_id, day):
    sql = 'SELECT CAST(GREATEST(time_beginning, :day) as time),\
           CAST(LEAST(time_end, :day + \'1 day\'::interval - \'1 s\'::interval) \
           as time), \
           grade FROM \
           MemberTimeGrades WHERE member_id=:member_id \
           AND time_end > :day AND time_beginning < (:day + \'1 day\'::interval)\
           ORDER BY time_beginning'

    result = db.session.execute(sql, {'member_id': member_id,
                                      'day':day}).fetchall()
    #print('result: ', result)
    if result is None:
        return []

    return [TimeInterval(*x) for x in result]

#TODO think if this should return a named tuple
def get_preferences_for_days_range(member_id, first_date, last_date):
    result = []
    i = first_date
    while i <= last_date:
        tmp = get_member_preferences_for_day(member_id, i)
        result.append(PreferencesDay(i, tmp))
        i += datetime.timedelta(days=1)

    return result

def get_member_times_for_each_day(member_id, poll_id):
    first_date, last_date = utils.get_poll_date_range(poll_id)
    return get_preferences_for_days_range(member_id, first_date, last_date)

#return list x of (times, member_id, reservation_length)
#x[i][0] are the times for day i of the poll
def get_customer_times_for_each_day(user_id, poll_id):
    customer_times = []
    member_ids = utils.get_user_poll_customer_member_ids(user_id, poll_id)
    for member_id in member_ids:
        tmp = (get_member_times_for_each_day(member_id, poll_id),
               member_id, utils.get_customer_reservation_length(member_id))
        customer_times.append(tmp)
    return customer_times

#return list x of (times, member_id, resource_description)
#x[i][0] are the times for day i of the poll
def get_resource_times_for_each_day(user_id, poll_id):
    #(resource_description, resource_id, member_id)
    tmp = utils.get_user_poll_resources(user_id, poll_id)
    print('user poll resources ', tmp)
    #(times, member_id, resource_description)
    resource_times = []
    for x in tmp:
        resource_times.append((get_member_times_for_each_day(x[1], poll_id),
                               x[1], x[0]))
    return resource_times


#return list of TimeIntervals
def get_member_times(member_id):
    sql = 'SELECT time_beginning, time_end, grade FROM \
           MemberTimeGrades WHERE member_id=:member_id \
           ORDER BY time_beginning'

    result = db.session.execute(sql, {'member_id': member_id}).fetchall()
    if result is None:
        return []

    return [TimeInterval(*x) for x in result]


#return list x of (times, member_id)
def get_members_times(member_ids):
    return [get_member_times(x) for x in member_ids]

#return list x of (times, member_id)
#one element for each member_id
def get_resource_times(poll_id):
    member_ids = utils.get_poll_resource_members(poll_id)
    times = get_members_times(member_ids)
    return list(zip(times, member_ids))

#return list x of (times, member_id, reservation_length)
#one element for each member_id
def get_customer_times(poll_id):
    member_ids = utils.get_poll_customer_members(poll_id)
    times = get_members_times(member_ids)
    lengths = [utils.get_customer_reservation_length(x) for x in member_ids]

    return list(zip(times, member_ids, lengths))


#Modifies existing time preference intervals so that truncates
#partially overlapping intervals and removes completely overlapping intervals
#and then adds the new inteval
#start and end are datetime.datetime
#TODO concatenate subsequent time intervals with the same time grade value
def add_member_time_grading(member_id, start, end, time_grade):
    #fetch a segment inside which the new segment is
    #ooooooo
    # nnnn
    sql = 'SELECT * FROM MemberTimeGrades WHERE member_id=:member_id \
           AND time_beginning < :start AND time_end > :end'

    result = db.session.execute(sql, {'member_id': member_id, 'start': start,
                             'end': end}).fetchone()

    if result is not None:
        sql = 'DELETE FROM MemberTimeGrades WHERE member_id=:member_id \
               AND time_beginning < :start AND time_end > :end'
        db.session.execute(sql, {'member_id': member_id, 'start': start,
                                 'end': end})

        sql = 'INSERT INTO MemberTimeGrades \
               (member_id, time_beginning, time_end, grade) VALUES \
               (:member_id, :time_beginning, :time_end, :grade)'
        db.session.execute(sql, {'member_id': result[0],
                                 'time_beginning': result[1],
                                 'time_end': start,
                                 'grade': result[3]})

        db.session.execute(sql, {'member_id': result[0],
                                 'time_beginning': end,
                                 'time_end': result[2],
                                 'grade': result[3]})


    #right side of the old segment is inside the new segment
    # ooooo
    #  nnnnnnn
    sql = 'UPDATE MemberTimeGrades SET \
           time_end = :start \
           WHERE member_id=:member_id AND time_end >= :start \
           AND time_end <= :end'
    db.session.execute(sql, {'member_id': member_id, 'start': start,
                              'end': end})
    #left side of the old segment is inside the new segment
    #     ooooo
    #  nnnnnnn
    sql = 'UPDATE MemberTimeGrades SET \
           time_beginning = :end \
           WHERE member_id=:member_id AND time_beginning >= :start \
           AND time_beginning <= :end'
    db.session.execute(sql, {'member_id': member_id, 'start': start,
                              'end': end})

    #remove non-positive length segments (in case these were generated by the
    #previous operations)
    sql = 'DELETE FROM MemberTimeGrades WHERE member_id=:member_id \
           AND time_end<=time_beginning'
    db.session.execute(sql, {'member_id': member_id})

    #add new segment
    sql = 'INSERT INTO MemberTimeGrades \
           (member_id, time_beginning, time_end, grade) \
           VALUES \
           (:member_id, :start, :end, :grade)'

    db.session.execute(sql, {'member_id': member_id, 'start': start,
                             'end': end, 'grade': time_grade})

    #TODO think if this function should commit.
    db.session.commit()

def process_new_grading(member_id, start_time, end_time, date,
                           time_grade):
    try:
        start_time = datetime.time.fromisoformat(start_time)
        end_time = datetime.time.fromisoformat(end_time)
        date = datetime.date.fromisoformat(date)
        start_datetime = datetime.datetime.combine(date, start_time)
        end_datetime = datetime.datetime.combine(date, end_time)
    except ValueError:
        return 'Incorrect time format'

    if start_datetime > end_datetime:
        return 'The length of the time segment was negative'

    if start_datetime.minute%5 != 0 or end_datetime.minute%5 != 0:
        return 'All times should be divisible by 5 minutes'

    member_type = utils.get_member_type(member_id)
    if member_type == 'customer':
        if time_grade not in ['0', '1', '2']:
            return 'Invalid time grade value'
    if member_type == 'resource':
        if time_grade not in ['0', '1']:
            return 'Invalid time grade value'

    if member_type is None:
        return 'Invalid member_id'

    print('start_datetime, end_datetime: ', start_datetime, end_datetime)
    #TODO check that user has rights to member_id

    add_member_time_grading(member_id, start_datetime, end_datetime,
                         time_grade)

    return None

