from collections import namedtuple
import poll
import datetime
import copy
import numpy as np
import times
import time
from db import db
from flask import session
### Optimization related functions ###
# everything is handled as 5 minute intervals

# resources = [(member_id, time_preferences)]
# customers = [(member_id, reservation_length, time_preferences)]

Assignment = namedtuple('Assignment', ['customer_member_id',
                                       'resource_member_id',
                                       'time'])

def process_optimize_poll(poll_id):
    if poll_id is None:
        return 'No poll_id was given'
    if not poll.user_owns_poll(poll_id):
        return 'Current user does not own the poll'
    if poll.get_poll_phase(poll_id) == 2:
        return 'Poll in the final results phase'

    optimize_poll(poll_id)

    return None

def optimize_poll(poll_id):
    resources = times.get_resource_times(poll_id)
    if len(resources) == 0:
        return ([], 0)
    resource_times, resource_ids = zip(*resources)
    customers = times.get_customer_times(poll_id)
    if len(customers) == 0:
        return ([], 0)
    customer_times, customer_ids, reservation_lengths = zip(*customers)



    start, end = poll.get_poll_datetime_range(poll_id)

    # convert time to discrete 5 min intervals
    resource_times = [intervals_to_array(x, start, end) for x in resource_times]
    customer_times = [intervals_to_array(x, start, end) for x in customer_times]
    reservation_lengths = [timedelta_to_index(x) for x in reservation_lengths]
    resources = list(zip(resource_ids, resource_times))
    customers = list(zip(customer_ids, reservation_lengths, customer_times))

    #optimize for ~2 seconds
    best_optimization = ([], 0)
    start_time = time.perf_counter()
    best_optimization = random_restart(greedy_1, resources, customers,
                                       best_optimization)
    one_round_length = time.perf_counter()-start_time
    cnt = 1;
    while (time.perf_counter() - start_time + one_round_length < 2):
        best_optimization = random_restart(greedy_1, resources, customers,
                                           best_optimization)
        cnt += 1

    assignments, satisfaction = best_optimization

    # 5min blocks --> datetime
    assignments = [assignment_to_datetime(x, start) for x in assignments]

    save_optimization(assignments, poll_id)

def discrete_to_datetime(x, start):
    return start + datetime.timedelta(minutes=5*x)

def assignment_to_datetime(a, start):
    return Assignment(a.customer_member_id, a.resource_member_id,
                      discrete_to_datetime(a.time, start))

def timedelta_to_index(td):
    return td.days*24*12 + td.seconds//60//5
def to_index(time, start):
    return timedelta_to_index(time-start)

def intervals_to_array(time_intervals, start, end):

    length_minutes = (end-start).days*24*60 + (end-start).seconds//60
    arr = [0 for x in range(length_minutes//5)]
    for x in time_intervals:
        a = to_index(x.start, start)
        b = to_index(x.end, start)
        i = max(0, a)
        while i < min(len(arr), b):
            arr[i] = x.grade
            i += 1
    return arr


# returns an array v
# v[i] is the satisfaction of user if the booking start
# i*5 minutes after the beginning of the first poll day

# v[i] is always 0 if there is zero in v[i...i+res_length-1]
def calculate_satisfaction_sum(arr, res_length):
    zero_cnt = 0
    array_sum = 0
    for i in range(res_length-1):
        if arr[i] == 0:
            zero_cnt += 1
        array_sum += arr[i]

    v = [0 for i in range(len(arr))]
    for i in range(res_length-1, len(arr)):
        array_sum += arr[i]
        if arr[i] == 0:
            zero_cnt += 1
        if zero_cnt > 0:
            v[i-res_length+1] = 0
        else:
            v[i-res_length+1] = array_sum/res_length
        array_sum -= arr[i-res_length+1]
        if arr[i-res_length+1] == 0:
            zero_cnt -= 1

    return v

# simple greedy algoritm
# goes through the customers one by one and assigns them to
#  1. best time for that customer
#  2. to a time starting as early as possible
#  3. to the first free resource# 

# the algorithm can be run multiple times with different resource/customer
# permutations
def greedy_1(resources, customers):
    def find_assignment(customer_sum, resource_sums):
        # -satisfaction, starting time, resource_index
        best_assignment = (0, 0, 0)
        for i in range(len(customer_sum)):
            if customer_sum[i] < best_assignment[0]:
                continue
            for j in range(len(resource_sums)):
                if resource_sums[j][i] > 0:
                    if customer_sum[i] > best_assignment[0]:
                        best_assignment = (customer_sum[i], i, j)
                    if customer_sum[i] == best_assignment[0] \
                         and i < best_assignment[1]:
                        best_assignment = (customer_sum[i], i, j)
                    if customer_sum[i] == best_assignment[0]\
                       and i == best_assignment[1] and j < best_assignment[2]:
                        best_assignment = (customer_sum[i], i, j)
        return best_assignment


    resources = copy.deepcopy(resources)
    customers = copy.deepcopy(customers)

    resource_m_ids, resource_times = zip(*resources)
    customer_m_ids, reservation_lengths, customer_times = zip(*customers)


    customer_sums = [calculate_satisfaction_sum(x, y)
                    for x, y in zip(customer_times, reservation_lengths)]

    assignments = []

    total_satisfaction = 0

    for i in range(len(customer_times)):
        length = reservation_lengths[i]
        resource_sums = [calculate_satisfaction_sum(x, length)
                         for x in resource_times]

        best = find_assignment(customer_sums[i], resource_sums)
        if best == (0, 0, 0):
            continue

        for j in range(best[1], best[1]+length):
            resource_times[best[2]][j] = 0

        total_satisfaction += best[0]
        assignments.append(Assignment(customer_m_ids[i],
                                       resource_m_ids[best[2]],
                                       best[1]))

    return assignments, total_satisfaction

def random_restart(f, resources, customers, best):
    r_permutation = list(np.random.permutation(len(resources)))
    c_permutation = list(np.random.permutation(len(customers)))
    resources = [resources[x] for x in r_permutation]
    customers = [customers[x] for x in c_permutation]
    result = f(resources, customers)
    if result[1] > best[1]:
        return result
    return best

def save_optimization(assignments, poll_id):
    sql = 'DELETE FROM OptimizationResults O WHERE O.customer_member_id IN \
            (SELECT P.id FROM PollMembers P WHERE P.poll_id=:poll_id)'

    db.session.execute(sql, {'poll_id': poll_id})
    sql = 'INSERT INTO OptimizationResults \
           (customer_member_id, resource_member_id, time_start) \
           VALUES (:customer_member_id, :resource_member_id, :time_start)'
    for x in assignments:
        db.session.execute(sql, {'customer_member_id': x.customer_member_id,
                                 'resource_member_id': x.resource_member_id,
                                 'time_start': x.time})
    db.session.commit()


OptimizationResult = namedtuple('OptimizationResult',
                                ['customer_member_id',
                                 'customer_member_name',
                                 'resource_member_id',
                                 'resource_member_name',
                                 'time'])

def get_owner_optimization_results(poll_id):
    try:
        int(poll_id)
    except ValueError:
        return 'Poll id not an integer'
    sql = 'SELECT P1.id, P1.name, P2.id, P2.name, O.time_start \
           FROM PollMembers P1, PollMembers P2, OptimizationResults O \
           WHERE P1.id=O.customer_member_id AND P2.id=O.resource_member_id \
           AND P1.poll_id=:poll_id'

    results = db.session.execute(sql, {'poll_id': poll_id}).fetchall()
    return [OptimizationResult(*x) for x in results]

# assumes poll_id is an integer or None
# retrieves results from poll poll_id
# only members to which user has access through the UsersPollmembers
def get_normal_user_optimization_results(poll_id):
    try:
        int(poll_id)
    except ValueError:
        return 'Poll id not an integer'
    user_id = session.get('user_id')
    sql = 'SELECT P1.id, P1.name, P2.id, P2.name, O.time_start \
           FROM PollMembers P1, PollMembers P2, OptimizationResults O, \
           UsersPollMembers M \
           WHERE P1.id=O.customer_member_id AND P2.id=O.resource_member_id \
           AND (P1.id=M.member_id OR P2.id=M.member_id) \
           AND P1.poll_id=:poll_id AND M.user_id=:user_id'
    results = db.session.execute(sql, {'poll_id': poll_id,
                                       'user_id': user_id}).fetchall()
    return [OptimizationResult(*x) for x in results]
