from collections import namedtuple
import utils
import datetime
import copy
import numpy as np
import signal
import times
from db import db
### Optimization related functions ###
#everything is handled as 5 minute intervals

#resources = [(member_id, time_preferences)]
#customers = [(member_id, reservation_length, time_preferences)]

Assignment = namedtuple('Assignment', ['customer_member_id',
                                       'resource_member_id',
                                       'time'])

class TimelimitError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

def process_optimize_poll(poll_id):
    if poll_id is None:
        return "No poll_id was given"
    if not utils.user_owns_poll(poll_id):
        return "Current user does not own the poll"
    optimize_poll(poll_id)
    """
    def handler(signum, frame):
        print("optimization timeout!")
        raise TimelimitError();
    signal.signal(signal.SIGALRM, handler)
    try:
        signal.alarm(5)
        optimize_poll_2(poll_id)
        signal.alarm(0)
    except TimelimitError:
        return "Timelimit exceeded in optimization"
    except:
        return "Unkown error in optimization"
    """

    return None

def optimize_poll(poll_id):
    resources = times.get_resource_times(poll_id)
    print(resources)
    resource_times, resource_ids= zip(*resources)
    customers = times.get_customer_times(poll_id)
    customer_times, customer_ids, reservation_lengths = zip(*customers)
    
    if len(customers) == 0:
        return ([], 0)

    
    #TODO use get poll range
    print(customer_times)
    print("customer times", customer_times[0])
    start = customer_times[0][0].start
    end = customer_times[0][-1].end
    #convert time to discrete 5 min intervals
    resource_times = [intervals_to_array(x, start, end) for x in resource_times]
    customer_times = [intervals_to_array(x, start, end) for x in customer_times]
    reservation_lengths = [timedelta_to_index(x) for x in reservation_lengths]
    resources = list(zip(resource_ids, resource_times))
    customers = list(zip(customer_ids, reservation_lengths, customer_times))

    assignments, satisfaction = random_restarts(greedy_1, 100, resources,
                                                customers)
    #5min blocks --> datetime
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
    #print(start, end, end-start, (end-start).seconds)

    length_minutes = (end-start).days*24*60 + (end-start).seconds//60
    #print('length_minutes', length_minutes)
    arr = [0 for x in range(length_minutes//5)]
    for x in time_intervals:
        a = to_index(x.start, start)
        b = to_index(x.end, start)
       # print('a, b', a, b)
        i = a
        while i < b:
            #     print(i)
            arr[i] = x.satisfaction
            i += 1
    return arr
    

#returns an array v
#v[i] is the satisfaction of user if the booking start
#i*5 minutes after the beginning of the first poll day

#v[i] is always 0 if there is zero in v[i...i+res_length-1]
def calculate_satisfaction_sum(arr, res_length):
    v = [0 for i in range(len(arr))]
    for i in range(len(arr)-res_length+1):
        ok_start = True
        mean_satisfaction = 0
        for j in range(i, i+res_length):
            if arr[j] == 0:
                ok_start = 0
            mean_satisfaction += arr[j]/res_length
        if ok_start == 0:
            v[i] = 0
        else:
            v[i] = mean_satisfaction
    return v
    
#simple greedy algoritm
#goes through the customers one by one and assigns them to
# 1. best time for that customer
# 2. to a time starting as early as possible
# 3. to the first free resource#

#the algorithm can be run multiple times with different resource/customer
#permutations
def greedy_1(resources, customers):
    def find_assignment(customer_sum, resource_sums):
        #-satisfaction, starting time, resource_index
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


    #print("resources \n", resources)
    #print('\n')
    resources = copy.deepcopy(resources)
    customers = copy.deepcopy(customers)

    resource_m_ids, resource_times = zip(*resources)
    customer_m_ids, reservation_lengths, customer_times = zip(*customers)
    #print(resource_m_ids, resource_times)
    #print(customer_m_ids, reservation_lengths, customer_times)


    customer_sums = [calculate_satisfaction_sum(x, y) 
                    for x, y in zip(customer_times, reservation_lengths)]

    #print(customer_sums)

    assignments = []

    total_satisfaction = 0

    for i in range(len(customer_times)):
        length = reservation_lengths[i]
        resource_sums = [calculate_satisfaction_sum(x, length)
                         for x in resource_times]

        #print("resource_sums, ", resource_sums)
        best = find_assignment(customer_sums[i], resource_sums)
        #print("best ", best)
        if best == (0, 0, 0):
            continue
        
        for j in range(best[1], best[1]+length):
            resource_times[best[2]][j] = 0

        total_satisfaction += best[0]
        #print("best ", best)
        #print(customer_m_ids,i)
        #print(customer_m_ids[i])
        #print(resource_m_ids[best[2]])
        #print(best[1])
        assignments.append(Assignment(customer_m_ids[i],
                                       resource_m_ids[best[2]],
                                       best[1]))

    return assignments, total_satisfaction

def random_restarts(f, n, resources, customers):
    best_assignment = ([], 0)
    for i in range(n):
        r_permutation = list(np.random.permutation(len(resources)))
        c_permutation = list(np.random.permutation(len(customers)))
        resources = [resources[x] for x in r_permutation]
        customers = [customers[x] for x in c_permutation]
        tmp = f(resources, customers)
        if tmp[1] > best_assignment[1]:
            best_assignment = tmp
    return best_assignment

def save_optimization(assignments, poll_id):
    print("saving: ", assignments)
    sql = "DELETE FROM OptimizationResults WHERE poll_id=:poll_id"
    db.session.execute(sql, {'poll_id': poll_id})
    sql = "INSERT INTO OptimizationResults \
           (poll_id, customer_member_id, resource_member_id, appointment_start) \
           VALUES (:poll_id, :customer_member_id, :resource_member_id, :appointment_start)"
    for x in assignments:
        db.session.execute(sql, {'poll_id': poll_id,
                                 'customer_member_id': x.customer_member_id,
                                 'resource_member_id': x.resource_member_id,
                                 'appointment_start': x.time})
    db.session.commit()


OptimizationResult = namedtuple('OptimizationResult', ['username', 
                                                      'resource_description',
                                                      'time'])
def get_optimization_results(poll_id):
    sql = "SELECT U.username, R.resource_description, O.appointment_start \
           FROM PollMembers P1, PollMembers P2, UsersPollMembers M, Users U, \
           Resources R, OptimizationResults O \
           WHERE P1.id=O.customer_member_id AND P2.id=O.resource_member_id \
           AND P1.id=M.member_id AND M.user_id=U.user_id \
           AND P2.id=R.member_id AND P1.poll_id=:poll_id"

    results = db.session.execute(sql, {'poll_id': poll_id}).fetchall()
    if results is None:
        return []

    return [OptimizationResult(*x) for x in results]
           
