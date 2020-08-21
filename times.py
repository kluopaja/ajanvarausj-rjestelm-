import datetime
from collections import namedtuple
from db import db
from flask import session
import utils
import optimization
import json

### Time preference related functions ###

#TODO think if I should store both ends of the interval or just the beginning
#TODO think if I need to modify the content of these
TimeInterval = namedtuple('TimeInterval', ['start', 'end', 'grade'])

#time preferences for one day (date)
GradesInDate = namedtuple('GradesInDate', ['date', 'intervals'])

#type(day) = datetime.date
#get an ordered list of time intervals that overlap with 'day'
def get_minute_grades_for_day(member_id, day):
    def to_minutes(t):
        return t.hour*60 + t.minute;

    sql = 'SELECT CAST(GREATEST(time_beginning, :day) as time),\
           CAST(LEAST(time_end, :day + \'1 day\'::interval) \
           as time), grade FROM \
           MemberTimeGrades WHERE member_id=:member_id \
           AND time_end > :day AND time_beginning < (:day + \'1 day\'::interval)\
           ORDER BY time_beginning'

    result = db.session.execute(sql, {'member_id': member_id,
                                      'day':day}).fetchall()
    #print('result: ', result)
    if result is None:
        return []

    out = []
    for x in result:
        mins_0 = to_minutes(x[0])
        mins_1 = to_minutes(x[1])
        #note that time period can never end at the beginning of the
        #current day
        if mins_1 == 0:
            mins_1 = 24*60;
        out.append(TimeInterval(mins_0, mins_1, x[2]))
    return out


#TODO think if this should return a named tuple
def get_minute_grades_for_days_range(member_id, first_date, last_date):
    result = []
    i = first_date
    while i <= last_date:
        tmp = get_minute_grades_for_day(member_id, i)
        result.append(GradesInDate(i.isoformat(), tmp))
        i += datetime.timedelta(days=1)

    return result

#returns a list of GradesInDate
#time intervals are minutes from the beginning of the day
#dates in isoformat
def get_minute_grades(member_id, poll_id):
    first_date, last_date = utils.get_poll_date_range(poll_id)
    return get_minute_grades_for_days_range(member_id, first_date, last_date)



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


#start and end are minutes from the beginning of the day
def process_new_grading(member_id, start, end, date, time_grade):
    try:
        date = datetime.datetime.fromisoformat(date)
        start_datetime = date + datetime.timedelta(seconds=start*60)
        end_datetime = date + datetime.timedelta(seconds=end*60)
    except ValueError:
        return 'Incorrect time format'
    except TypeError:
        return 'Time values missing'
    except:
        return 'Unknown error with times'

    try:
        time_grade = int(time_grade)
    except:
        return 'Time grade not an integer'

    try:
        member_id = int(member_id)
    except:
        return 'Member id not an interger'

    if start_datetime > end_datetime:
        return 'The length of the time segment was negative'

    if start_datetime.minute%5 != 0 or end_datetime.minute%5 != 0:
        return 'All times should be divisible by 5 minutes'
    print('fallback ', member_id, start, end, time_grade);

    user_id = session.get('user_id')
    #check user rights
    print('user owns ... ', utils.user_owns_parent_poll(member_id))
    if not utils.user_owns_parent_poll(member_id) and \
       not utils.user_has_access(user_id, member_id):
        return 'User has no rights to add new time grades'

    print('member_id ', member_id)
    print('time grade', time_grade)
    member_type = utils.get_member_type(member_id)
    if member_type == 'customer':
        if time_grade not in [0, 1, 2]:
            return 'Invalid time grade value'
    if member_type == 'resource':
        if time_grade not in [0, 1]:
            return 'Invalid time grade value'

    if member_type is None:
        return 'Invalid member_id'

    print('start_datetime, end_datetime: ', start_datetime, end_datetime)
    #TODO check that user has rights to member_id
    #TODO.fcheck that the start_datetime and end_datetime are within the
    #allowed poll range!
    add_member_time_grading(member_id, start_datetime, end_datetime,
                         time_grade)
    db.session.commit()
    return None

def process_grading_list(member_id, data):
    try:
        data = json.loads(data)
    except:
        return 'Invalid data json string'

    try:
        error = None
        for day in data:
            print(day);
            for interval in day[1]:
                print(interval)
                error = process_new_grading(member_id, interval[0], interval[1],
                                            day[0], interval[2]);
        if error is not None:
            return error
        db.session.commit()
    except Exception as e:
        print(e);
        return 'Error when parsing the the grading json' + str(data);

def process_grading_fallback(member_id, start_time, end_time, date, time_grade):
    try:
        start_time = datetime.time.fromisoformat(start_time)
        end_time = datetime.time.fromisoformat(end_time)
        start = int(start_time.hour*60 + start_time.second/60)
        end = int(end_time.hour*60 + end_time.second/60)
    except:
        return 'Incorrect time format'



    error = process_new_grading(member_id, start, end, date, time_grade);
    if error is None:
        db.session.commit();

    return error;
