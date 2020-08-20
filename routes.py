from app import app
from flask import render_template
from werkzeug.urls import url_parse
from flask import session, request, redirect, flash

from utils import *
import times
import optimization

@app.route('/')
def index():
    polls = get_user_polls()
    return render_template('index.html', polls=polls)


@app.route('/poll/<int:poll_id>')
def poll(poll_id):
    if 'user_id' not in session:
        return render_template('login.html', need_login_redirect=True)

    #TODO
    #some check that user has any rights to see this poll
    current_poll = get_polls_by_ids([poll_id])
    if len(current_poll) == 0:
        current_poll = None
    else:
        current_poll = current_poll[0]

    is_owner = user_owns_poll(poll_id)

    user_id = session.get('user_id')
    user_customers = get_user_poll_customers(user_id, poll_id)
    user_resources = get_user_poll_resources(user_id, poll_id)

    #do we need this here?
    grade_descriptions = ['ei sovi', 'sopii', 'sopii hyvin']
    return render_template('poll.html', is_owner=is_owner,
                           poll=current_poll,
                           user_customers=user_customers,
                           user_resources=user_resources,
                           grade_descriptions=grade_descriptions)

@app.route('/poll/<int:poll_id>/owner')
def poll_owner(poll_id):
    if 'user_id' not in session:
        return render_template('login.html', need_login_redirect=True)

    #list of (url_id, reservation_length)
    customer_invitations = None
    #list of (url_id, resource_description)
    resource_invitations = None
    #list of (resource_description, resource_id)
    resources = None

    current_poll = get_polls_by_ids([poll_id])
    if len(current_poll) == 0:
        current_poll = None
    else:
        current_poll = current_poll[0]

    is_owner = user_owns_poll(poll_id)

    if not is_owner:
        error = 'Ei oikeuksia katsoa kyselyn omistajan näkymää'
        return render_template('error.html', message=error)

    customer_invitations = get_customer_invitations(poll_id)
    resource_invitations = get_resource_invitations(poll_id)
    print('customer invitations ', customer_invitations)

    customers = get_poll_customers(poll_id)
    resources = get_poll_resources(poll_id)

    optimization_results = optimization.get_optimization_results(poll_id)


    return render_template('poll_owner.html',
                           poll=current_poll,
                           customer_invitations=customer_invitations,
                           resource_invitations=resource_invitations,
                           customers=customers,
                           resources=resources,
                           optimization_results=optimization_results)

@app.route('/poll/<int:poll_id>/results')
def poll_results(poll_id):
    if 'user_id' not in session:
        return render_template('login.html', need_login_redirect=True)

    current_poll = get_polls_by_ids([poll_id])
    if len(current_poll) == 0:
        current_poll = None
    else:
        current_poll = current_poll[0]

    return render_template('poll_results.html',
                           poll=current_poll);
@app.route('/poll/<int:poll_id>/<int:member_id>/times')
def poll_times(poll_id, member_id):
    if 'user_id' not in session:
        return render_template('login.html', need_login_redirect=True)

    user_id = session.get('user_id')
    is_owner = user_owns_parent_poll(member_id)

    if not is_owner and not user_has_access(user_id, member_id):
        error = 'Ei oikeuksia muokata aikoja'
        return render_template('error.html', message=error)

    if not member_in_poll(member_id, poll_id):
        error = 'Tarkista url. Jäsen ei kuulu kyselyyn'
        return render_template('error.html', message=error)

    current_poll = get_polls_by_ids([poll_id])
    if len(current_poll) == 0:
        current_poll = None
    else:
        current_poll = current_poll[0]

    member_type = get_member_type(member_id)
    member_times = times.get_minute_grades(member_id, poll_id)
    member_name = ''
    reservation_length = 0
    if member_type == 'resource':
        member_name = get_resource_name(member_id)
        grade_descriptions = ['Ei käytettävissä', 'Käytettävissä']

    if member_type == 'customer':
        reservation_length = get_customer_reservation_length(member_id)
        grade_descriptions = ['Ei sovi', 'Sopii tarvittaessa', 'Sopii hyvin']


    return render_template('poll_times.html',
                            is_owner=is_owner,
                            poll=current_poll,
                            member_id=member_id,
                            time_grades=member_times,
                            grade_descriptions=grade_descriptions,
                            member_type=member_type,
                            member_name=member_name,
                            reservation_length=reservation_length);



@app.route('/new_poll', methods=['GET', 'POST'])
def new_poll():
    if 'user_id' not in session:
        return render_template('login.html', need_login_redirect=True)

    if request.method == 'GET':
        return render_template('new_poll.html')
    if request.method == 'POST':
        error = process_new_poll(session['user_id'],
                                 request.form.get('poll_name'),
                                 request.form.get('poll_description'),
                                 request.form.get('first_appointment_date'),
                                 request.form.get('last_appointment_date'),
                                 request.form.get('poll_end_date'),
                                 request.form.get('poll_end_time'))
        if error is not None:
            print('not valid poll')
            return render_template('error.html', message=error)

        flash('Kyselyn luonti onnistui')
        return redirect('/')
#TODO
#storing the 'login_redirect' in the session was a very bad idea
#what if the user visits the link, then does something else,
#comes back to the site and logs in
#then they will be redirected to the link site
#how to login and then return to the same page?

#TODO give the message as a GET parameter?
@app.route('/login', methods=['GET', 'POST'])
def login():
    def redirect_to_next(default='/'):
        if 'login_redirect' not in session:
            return redirect(default)

        #if the redirect target is not a valid relative url
        url = session['login_redirect']
        del session['login_redirect']

        if not url or url_parse(url).netloc != '':
            return redirect(default)

        return redirect(url)

    error = 'Unknown error'
    if session.get('user_id', 0):
        return redirect_to_next(default='/');

    if request.method == 'GET':
        return render_template('login.html')

    elif request.method == 'POST':
        print('post request', request.form)
        error = process_login(request.form.get('username'),
                              request.form.get('password'))
        if error is None:
            flash('Kirjautuminen onnistui')
            return redirect_to_next(default='/')

    return render_template('login.html',
                            message='Kirjautuminen epäonnistui: ' + error)

@app.route('/logout')
def logout():
    process_logout()
    return render_template('logout.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        print('register: ', request.form)
        error = process_registration(request.form.get('username'),
                                      request.form.get('password'))
        #after successful registration, automatically log the user in
        #and redirect to login
        if error is None:
            process_login(request.form.get('username'),
                          request.form.get('password'))

            flash('Rekisteröityminen onnistui')
            return redirect('/login')

    message = 'Käyttäjätunnuksen luonti epäonnistui: ' + error
    return render_template('register.html',
                           message=message)

@app.route('/invite/<url_id>', methods=['POST', 'GET'])
def invite(url_id):
    print('type of url_id', type(url_id))
    if not session.get('user_id', 0):
        session['login_redirect'] = '/invite/' + url_id
        #TODO rename 'need_login_redirect' to 'login_needed_error'
        return render_template('login.html', need_login_redirect=True)

    invitation_type = get_invitation_type(url_id)
    #check if url_id is in database
    if invitation_type is None:
        return render_template('invalid_invitation.html')

    if request.method == 'GET':
        if invitation_type == 'poll_customer':
            #TODO think if the url_id should be in 'details'
            return render_template('confirm_poll_invitation.html',
                                   details=customer_type_details_by_url_id(url_id),
                                   url_id=url_id)

        if invitation_type == 'resource_owner':
            return render_template('confirm_resource_invitation.html',
                                   details=resource_details_by_url_id(url_id),
                                   url_id=url_id)
    if request.method == 'POST':
        print('user response: ', request.form['user_response'])
        if request.form.get('user_response') == 'yes':
            print('invitation type: ', invitation_type)
            if invitation_type == 'poll_customer':
                error = apply_new_customer_invitation(url_id)
            if invitation_type == 'resource_owner':
                error = apply_resource_invitation(url_id)
            if error is not None:
                message = 'Kutsumisen hyväksyminen epäonnistui: ' + error
                return render_template('error.html', message=message)

            flash('Kutsun hyväksyminen onnistui')
            poll_id = request.form.get('poll_id')
            if poll_id is None:
                message = 'Uudelleenohjaus epäonnistui'
                return render_template('error.html', message=message)

            return redirect('/poll/' + poll_id)
        else:
            print('invitation failed')
            return redirect('/')



#TODO
#all error messages that require the user to return some poll could
#be handled with one html page
#do we even need any other error page redirections than a poll?
#if not, then one error.html should be enough
@app.route('/new_invitation', methods=['POST', 'GET'])
def new_invitation():
    if 'user_id' not in session:
        return render_template('login.html', need_login_redirect=True)

    error = process_new_invitation(request.form.get('invitation_type'),
                                   request.form.get('poll_id'),
                                   request.form.get('member_id'),
                                   request.form.get('reservation_length'))

    print('new invitation request', request.form)
    print('error? ', error)
    if error is None:
        flash('Uuden kutsun luonti onnistui')
        return redirect('/poll/'+request.form.get('poll_id')+'/owner')
    else:
        return render_template('new_invitation_failed.html',
                               error_message=error,
                               poll_id=request.form.get('poll_id'))

@app.route('/modify_customer', methods=['POST'])
def modity_customer():
    if 'user_id' not in session:
        return render_template('login.html', need_login_redirect=True)

    error = process_modify_customer(request.form.get('member_id'),
                                    request.form.get('reservation_length'));

    if error is None:
        flash('Varaustoiveen pituuden muutos onnistui')
        poll_id = request.form.get('poll_id', 0)
        member_id = request.form.get('member_id', 0)
        return redirect('/poll/' + poll_id + '/' + member_id + '/times')
    else:
        return render_template('error.html', message=error)


@app.route('/new_resource', methods=['POST'])
def new_resource():
    if 'user_id' not in session:
        return render_template('login.html', need_login_redirect=True)

    print('new resource, post: ', request.form)
    error = process_new_resource(request.form.get('poll_id'),
                              request.form.get('resource_name'))
    if error is None:
        flash('Uuden resurssin luonti onnistui')
        return redirect('/poll/'+request.form.get('poll_id')+'/owner')
    else:
        print('creation of new resource failed')
        return render_template('new_resource_failed.html',
                               error_message=error,
                               poll_id=request.form.get('poll_id'))

@app.route('/new_time_preference', methods=['POST'])
def new_time_preference():
    if 'user_id' not in session:
        return render_template('login.html', need_login_redirect=True)

    #if the post request was generated by javascript
    #this if this could be done in a better way
    if request.form.get('data') is not None:
        error = times.process_grading_list(request.form.get('member_id'),
                                           request.form.get('data'));
    else:
        #used if no js is available
        error = times.process_grading_fallback(request.form.get('member_id'),
                                               request.form.get('start'),
                                               request.form.get('end'),
                                               request.form.get('date'),
                                               request.form.get('satisfaction'))

    if error is None:
        poll_id = request.form.get('poll_id')
        member_id = request.form.get('member_id')
        flash('Aikavalintojen tallennus onnistui');
        if poll_id is None or member_id is None:
            message = 'Uudelleenohjaus epäonnistui'
            return render_template('error.html', message=message)

        return redirect('/poll/'+poll_id+'/'+member_id+'/times')
    else:
        print('creating new time preference failed')
        return render_template('error.html', message=error)

@app.route('/optimize_poll', methods=['POST'])
def optimize_poll():
    if 'user_id' not in session:
        return render_template('login.html', need_login_redirect=True)

    error = optimization.process_optimize_poll(request.form.get('poll_id'))
    if error is None:
        flash('Ajanvarauksien optimointi onnistui');
        return redirect('/poll/'+request.form.get('poll_id', 0)+'/owner')

    return render_template('error.html', message=error)

#TODO make one .html for failed poll actions
