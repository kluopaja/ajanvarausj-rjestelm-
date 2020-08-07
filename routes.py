from app import app
from flask import render_template
from werkzeug.urls import url_parse
from flask import session, request, redirect

from utils import *
import times

@app.route('/')
def index():
    polls = get_user_polls()
    print("index: ", polls)
    return render_template("index.html", polls=polls)


@app.route('/poll/<poll_id>')
def poll(poll_id):
    if 'user_id' not in session:
        return render_template('login.html', need_login_redirect=True)

    #TODO
    #some check that user has any rights to see this poll

    #list of (url_id, reservation_length)
    participant_invitations = None
    #list of (url_id, resource_description)
    resource_invitations = None
    #list of (resource_description, resource_id)
    resources = None
    
    current_poll = get_polls_by_ids([poll_id])[0]

    is_owner = user_owns_poll(poll_id)
    if is_owner:
        participant_invitations = get_participant_invitations(poll_id)
        resource_invitations = get_resource_invitations(poll_id)
        resources = get_poll_resources(poll_id)

    user_id = session.get('user_id')
    consumer_times = times.get_poll_user_consumer_times(user_id, poll_id)
    resource_times = times.get_poll_user_resource_times(user_id, poll_id)
    return render_template("poll.html", is_owner=is_owner,
                           poll=current_poll,
                           participant_invitations=participant_invitations,
                           resource_invitations=resource_invitations,
                           resources=resources,
                           participant_times=consumer_times,
                           resource_times=resource_times)
 

@app.route('/new_poll', methods=['GET', 'POST'])
def new_poll():
    if 'user_id' not in session:
        return render_template('login.html', need_login_redirect=True)

    if request.method == 'GET':
        return render_template("new_poll.html")
    if request.method == 'POST':
        error = process_new_poll(session['user_id'],
                                 request.form.get('poll_name'),
                                 request.form.get('poll_description'),
                                 request.form.get('first_appointment_date'),
                                 request.form.get('last_appointment_date'),
                                 request.form.get('poll_end_date'),
                                 request.form.get('poll_end_time'))
        if error is not None:
            print("not valid poll")
            return render_template("new_poll")

        print(poll)
        process_new_poll(poll)
        return redirect("/")
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

    if session.get('user_id', 0):
        return redirect_to_next(default='/');

    if request.method == 'GET':
        return render_template("login.html")

    elif request.method == 'POST':
        print("post request", request.form)

        if process_login(request.form['username'], request.form['password']):
            return redirect_to_next(default='/')

    return render_template('login.html',
                           message='Kirjautuminen epäonnistui,yritä uudelleen')


@app.route('/logout')
def logout():
    process_logout()

    return render_template("logout.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    if request.method == 'POST':
        print("register: ", request.form)
        is_ok = process_registration(request.form['username'],
                                      request.form['password'])
        #after successful registration, automatically log the user in
        #and redirect to login
        if is_ok:
            process_login(request.form['username'],
                          request.form['password'])
            return redirect('/login')

    return render_template("register.html",
                           message='Käyttäjätunnuksen luonti epäonnistui,yritä uudelleen')

@app.route('/invite/<url_id>', methods=['POST', 'GET'])
def invite(url_id):
    print('type of url_id', type(url_id))
    if not session.get('user_id', 0):
        session['login_redirect'] = "/invite/" + url_id
        return render_template('login.html', need_login_redirect=True)

    invitation_type = get_invitation_type(url_id)
    #check if url_id is in database
    if invitation_type is None:
        return render_template('invalid_invitation.html')

    if request.method == 'GET':
        if invitation_type == 'poll_participant':
            #TODO think if the url_id should be in 'details'
            return render_template("confirm_poll_invitation.html",
                                   details=participant_invitation_by_url_id(url_id),
                                   url_id=url_id)

        if invitation_type == 'resource_owner':
            return render_template("confirm_resource_invitation.html",
                                   details=resource_invitation_by_url_id(url_id),
                                   url_id=url_id)
    if request.method == 'POST':
        print("user response: ", request.form['user_response'])
        if request.form["user_response"] == "yes":
            if invitation_type == 'poll_participant':
                apply_poll_invitation(url_id)
            if invitation_type == 'resource_owner':
                apply_resource_invitation(url_id)
            #TODO add message
            return redirect('/')
        else:
            print("invitation failed")
            return redirect('/')


@app.route('/new_invitation', methods=['POST', 'GET'])
def new_invitation():
    if 'user_id' not in session:
        return render_template('login.html', need_login_redirect=True)

    ok = process_new_invitation(request.form.get('invitation_type'),
                                request.form.get('poll_id'),
                                request.form.get('resource_id'),
                                request.form.get('reservation_length'))

    print("new invitation request", request.form)
    print("ok? ", ok)
    if ok:
        return redirect('/poll/'+request.form.get('poll_id'))
    else:
        return render_template("new_invitation_failed.html",
                               error_message="Tuntematon virhe",
                               poll_id=request.form.get('poll_id'))

@app.route('/new_resource', methods=['POST'])
def new_resource():
    if 'user_id' not in session:
        return render_template('login.html', need_login_redirect=True)

    print("new resource, post: ", request.form)
    ok = process_new_resource(request.form.get('poll_id'),
                              request.form.get('resource_description'))
    if ok:
        return redirect('/poll/'+request.form.get('poll_id'))
    else:
        print("creation of new resource failed")
        return render_template("new_resource_failed.html",
                               error_message="Tuntematon virhe",
                               poll_id=request.form.get('poll_id'))

@app.route('/new_time_preference', methods=['POST'])
def new_time_preference():
    if 'user_id' not in session:
        return render_template('login.html', need_login_redirect=True)

    #TODO check that user has rights to member_id

    start_time = request.form.get('start')
    end_time = request.form.get('end')
    date = request.form.get('date')
    satisfaction = request.form.get('satisfaction')
    poll_id = request.form.get('poll_id')
    process_new_time_preference(poll_id, start_time, end_time, date,
                                satisfaction)
    print(start_time, end_time, date, satisfaction, poll_id)
    return redirect("/poll/"+poll_id)

#TODO make one .html for failed poll actions
