from app import app
from flask import render_template
from werkzeug.urls import url_parse
from flask import session, request, redirect, flash, url_for

import auth
import poll
import member
import link
import times
import optimization

@app.route('/')
def index():
    polls = poll.get_user_polls()
    return render_template('index.html', polls=polls)

@app.route('/poll/<int:poll_id>')
# naming this to 'poll' would clash with the poll module
def route_poll(poll_id):
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    current_poll = poll.process_get_poll(poll_id)
    if current_poll is None:
        message = 'Kyselyä ei löytynyt tai käyttäjällä ei ole oikeuksia kyselyyn'
        flash('Virhe! ' + message)
        return redirect(url_for('index'))

    is_owner = poll.user_owns_poll(poll_id)

    user_id = session.get('user_id')
    user_customers = poll.get_user_poll_customers(user_id, poll_id)
    user_resources = poll.get_user_poll_resources(user_id, poll_id)

    # do we need this here?
    grade_descriptions = ['ei sovi', 'sopii', 'sopii hyvin']

    return render_template('poll.html', is_owner=is_owner,
                           poll=current_poll,
                           user_customers=user_customers,
                           user_resources=user_resources,
                           grade_descriptions=grade_descriptions)


@app.route('/poll/<int:poll_id>/customers')
def poll_customers(poll_id):
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    # list of (url_id, reservation_length)
    customer_invitations = None

    is_owner = poll.user_owns_poll(poll_id)
    if not is_owner:
        flash('Virhe! Ei oikeuksia katsoa kyselyn omistajan näkymää')
        return redirect(url_for('route_poll', poll_id=poll_id))

    current_poll = poll.get_polls_by_ids([poll_id])[0]

    # note that we already know that poll_id is an integer
    new_customer_links = poll.get_new_customer_links(poll_id)
    customer_access_links = poll.get_customer_access_links(poll_id)
    customers = poll.get_poll_customers(poll_id)
    return render_template('poll_customers.html',
                           is_owner=True,
                           poll=current_poll,
                           new_customer_links=new_customer_links,
                           customer_access_links=customer_access_links,
                           customers=customers)

@app.route('/poll/<int:poll_id>/resources')
def poll_resources(poll_id):
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    # list of (url_id, resource_description)
    resource_invitations = None
    # list of (resource_description, resource_id)
    resources = None

    is_owner = poll.user_owns_poll(poll_id)
    if not is_owner:
        flash('Virhe! Ei oikeuksia katsoa kyselyn omistajan näkymää')
        return redirect(url_for('route_poll', poll_id=poll_id))

    current_poll = poll.get_polls_by_ids([poll_id])[0]

    # note that we already know that poll_id is an integer
    resource_access_links = poll.get_resource_access_links(poll_id)
    resources = poll.get_poll_resources(poll_id)

    return render_template('poll_resources.html',
                           is_owner=True,
                           poll=current_poll,
                           resource_access_links=resource_access_links,
                           resources=resources)

@app.route('/poll/<int:poll_id>/optimization')
def poll_optimization(poll_id):
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    is_owner = poll.user_owns_poll(poll_id)
    if not is_owner:
        flash('Virhe! Ei oikeuksia katsoa kyselyn omistajan näkymää')
        return redirect(url_for('route_poll', poll_id=poll_id))

    current_poll = poll.get_polls_by_ids([poll_id])[0]

    optimization_results = optimization.get_owner_optimization_results(poll_id)

    return render_template('poll_optimization.html',
                           is_owner=True,
                           poll=current_poll,
                           optimization_results=optimization_results)

@app.route('/poll/<int:poll_id>/results')
def poll_results(poll_id):
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    current_poll = poll.process_get_poll(poll_id)
    if current_poll is None:
        flash('Virhe! Kyselyä ei löytynyt tai käyttäjällä ei ole oikeuksia kyselyyn')
        return redirect(url_for('index'))

    is_owner = poll.user_owns_poll(poll_id)
    results = []
    if current_poll.phase == 2:
        if is_owner:
            results = optimization.get_owner_optimization_results(poll_id)
        else:
            results = optimization.get_normal_user_optimization_results(poll_id)
    return render_template('poll_results.html',
                           is_owner=is_owner,
                           optimization_results=results,
                           poll=current_poll)

@app.route('/poll/<int:poll_id>/<int:member_id>/times')
def poll_times(poll_id, member_id):
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    current_poll = poll.process_get_poll(poll_id)
    if current_poll is None:
        flash('Virhe! Kyselyä ei löytynyt tai käyttäjällä ei ole oikeuksia kyselyyn')
        return redirect(url_for('index'))

    user_id = session.get('user_id')
    is_owner = member.user_owns_parent_poll(member_id)

    if not is_owner and not member.user_has_access(user_id, member_id):
        flash('Virhe! Ei oikeuksia muokata aikoja')
        return redirect(url_for('route_poll', poll_id=poll_id))

    if not poll.member_in_poll(member_id, poll_id):
        flash('Virhe! Jäsen ei kuulu kyselyyn. Tarkista url.')
        return redirect(url_for('route_poll', poll_id=poll_id))

    member_type = member.get_member_type(member_id)
    member_times = times.get_minute_grades(member_id, poll_id)
    member_name = member.get_member_name(member_id)
    reservation_length = 0
    if member_type == 'resource':
        grade_descriptions = ['Ei käytettävissä', 'Käytettävissä']

    if member_type == 'customer':
        reservation_length = member.get_customer_reservation_length(member_id)
        grade_descriptions = ['Ei sovi', 'Sopii tarvittaessa', 'Sopii hyvin']

    view_only = 0
    if current_poll.phase >= 1 and not is_owner:
        view_only = 1;
    if current_poll.phase == 2:
        view_only = 1;

    return render_template('poll_times.html',
                            is_owner=is_owner,
                            poll=current_poll,
                            member_id=member_id,
                            time_grades=member_times,
                            grade_descriptions=grade_descriptions,
                            member_type=member_type,
                            member_name=member_name,
                            reservation_length=reservation_length,
                            selected_day=request.args.get('selected_day', 0),
                            view_only=view_only)

@app.route('/new_poll', methods=['GET', 'POST'])
def new_poll():
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template('new_poll.html')
    if request.method == 'POST':
        auth.check_csrf_token(request.form.get('csrf_token'))
        error = poll.process_new_poll(session['user_id'],
                                      request.form.get('poll_name'),
                                      request.form.get('poll_description'),
                                      request.form.get('first_appointment_date'),
                                      request.form.get('last_appointment_date'),
                                      request.form.get('poll_end_date'),
                                      request.form.get('poll_end_time'))
        if error is not None:
            flash('Virhe! Uuden kyselyn luominen epäonnistui: ' + error)
            return redirect(url_for('new_poll'))

        flash('Kyselyn luominen onnistui')
        return redirect(url_for('index'))

@app.route('/modify_poll', methods=['POST'])
def modify_poll():
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    auth.check_csrf_token(request.form.get('csrf_token'))
    error = poll.process_modify_poll(request.form.get('poll_id'),
                                     request.form.get('poll_end_date'),
                                     request.form.get('poll_end_time'),
                                     request.form.get('end_now'))
    if error is None:
        flash('Kyselyn tiedot päivitetty onnistuneesti')
    else:
        flash('Virhe! Kyselyn tietojen päivittäminen epäonnistui: ' + error)

    return redirect(url_for('route_poll',
                            poll_id=request.form.get('poll_id', 0)))

@app.route('/login', methods=['GET', 'POST'])
def login():
    def redirect_to_next():
        next_url = request.args.get('next_url', 0)
        if next_url:
            return redirect(next_url)
        return redirect(url_for('index'))

    error = 'Unknown error'
    if session.get('user_id', 0):
        flash('Olet jo kirjautunut sisään')
        return redirect_to_next()

    if request.method == 'GET':
        auth.set_csrf_token()
        return render_template('login.html',
                               next_url=request.args.get('next_url'))

    elif request.method == 'POST':
        auth.check_csrf_token(request.form.get('csrf_token'))
        error = auth.process_login(request.form.get('username'),
                                   request.form.get('password'))
        if error is None:
            flash('Kirjautuminen onnistui')
            return redirect_to_next()

    flash('Virhe! Kirjautuminen epäonnistui')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    auth.process_logout()
    return render_template('logout.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        auth.set_csrf_token()
        return render_template('register.html')
    if request.method == 'POST':
        auth.check_csrf_token(request.form.get('csrf_token'))
        error = auth.process_registration(request.form.get('username'),
                                          request.form.get('password'))
        # after successful registration, automatically log the user in
        # and redirect to login
        if error is None:
            auth.process_login(request.form.get('username'),
                               request.form.get('password'))

            flash('Rekisteröityminen onnistui')
            return redirect(url_for('login'))

    flash('Virhe! Käyttäjätunnuksen luominen epäonnistui: ' + error)
    return redirect(url_for('register'))

# create a new customer with a link
@app.route('/new_customer/<url_id>', methods=['POST', 'GET'])
def new_customer(url_id):
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        redirect_url = url_for('new_customer', url_id=url_id)
        return redirect(url_for('login', next_url=redirect_url))

    if request.method == 'GET':
        # TODO think if the url_id should be in 'details'
        return render_template('confirm_poll_invitation.html',
                               details=link.customer_type_details_by_url_id(url_id),
                               url_id=url_id)
    if request.method == 'POST':
        auth.check_csrf_token(request.form.get('csrf_token'))
        # TODO this should return the member id of the new customer
        error = link.process_new_customer_url(url_id,
                                              request.form.get('reservation_length'),
                                              request.form.get('customer_name'))
        if error is None:
            flash('Uusi asiakas luotu onnistuneesti')
            poll_id = request.form.get('poll_id')
            return redirect(url_for('route_poll', poll_id=poll_id))

        flash('Virhe! Uuden asiakkaan luominen epäonnistui: ' + error)
        return redirect(url_for('index'))

# cannot use /new_customer for this
@app.route('/add_customer', methods=['POST'])
def add_customer():
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    auth.check_csrf_token(request.form.get('csrf_token'))
    error = poll.process_add_customer(request.form.get('poll_id'),
                                      request.form.get('reservation_length'),
                                      request.form.get('customer_name'))
    if error is None:
        flash('Uusi asiakas luotu onnistuneesti')
    else:
        flash('Virhe! Uuden asiakkaan luominen epäonnistui: '+ error)

    return redirect(url_for('poll_customers',
                            poll_id=request.form.get('poll_id', 0)))

@app.route('/access/<url_id>', methods=['POST', 'GET'])
def access(url_id):
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        redirect_url = url_for('access', url_id=url_id)
        return redirect(url_for('login', next_url=redirect_url))

    if request.method == 'GET':
        return render_template('confirm_member_access_link.html',
                               details=link.member_details_by_url_id(url_id),
                               url_id=url_id)
    if request.method == 'POST':
        auth.check_csrf_token(request.form.get('csrf_token'))
        error = link.process_access(url_id)
        if error is not None:
            flash('Virhe! Kutsumisen hyväksyminen epäonnistui: ' + error)
            return redirect(url_for('index'))

        flash('Muokkausoikeus hyväksytty')
        return redirect(url_for('poll_times',
                                poll_id=request.form.get('poll_id', 0),
                                member_id=request.form.get('member_id', 0)))

@app.route('/new_new_customer_link', methods=['POST'])
def new_new_customer_link():
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    auth.check_csrf_token(request.form.get('csrf_token'))
    error = link.process_new_new_customer_link(request.form.get('poll_id'))
    if error is None:
        flash('Uuden kutsun luominen onnistui')
    else:
        flash('Virhe! Kutsun luominen epäonnistui: ' + error)

    return redirect(url_for('poll_customers',
                            poll_id=request.form.get('poll_id', 0)))

@app.route('/new_member_access_link', methods=['POST'])
def new_member_access_link():
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    auth.check_csrf_token(request.form.get('csrf_token'))
    error = link.process_new_member_access_link(request.form.get('member_id'))
    if error is None:
        flash('Uuden oikeuslinkin luominen onnistui')
    else:
        flash('Virhe! Uuden oikeuslinkin luominen epäonnistui: ' + error)

    if request.form.get('member_type') == 'customer':
        redirect_route = 'poll_customers'
    else:
        redirect_route = 'poll_resources'

    return redirect(url_for(redirect_route,
                            poll_id=request.form.get('poll_id', 0)))

@app.route('/modify_customer', methods=['POST'])
def modify_customer():
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    auth.check_csrf_token(request.form.get('csrf_token'))
    error = member.process_modify_customer(request.form.get('member_id'),
                                           request.form.get('reservation_length'))
    if error is None:
        flash('Varaustoiveen pituuden muuttaminen onnistui')
    else:
        flash('Virhe! Varaustoiveen pituuden muuttaminen epäonnistui' + error)

    return redirect(url_for('poll_times',
                            poll_id=request.form.get('poll_id', 0),
                            member_id=request.form.get('member_id', 0)))

@app.route('/new_resource', methods=['POST'])
def new_resource():
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    auth.check_csrf_token(request.form.get('csrf_token'))
    error = poll.process_new_resource(request.form.get('poll_id'),
                                      request.form.get('resource_name'))
    if error is None:
        flash('Uuden resurssin luominen onnistui')
    else:
        flash('Virhe! Uuden resurssin luominen epäonnistui' + error)

    return redirect(url_for('poll_resources',
                            poll_id=request.form.get('poll_id', 0)))

@app.route('/delete_member', methods=['POST'])
def delete_member():
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    auth.check_csrf_token(request.form.get('csrf_token'))
    error = member.process_delete_member(request.form.get('member_id'))
    if error is None:
        flash('Jäsenen poistaminen onnistui')
    else:
        flash('Virhe! Jäsenen poistaminen epäonnistui: ' + error)

    if request.form.get('member_type') == 'customer':
        redirect_route = 'poll_customers'
    else:
        redirect_route = 'poll_resources'

    return redirect(url_for(redirect_route,
                            poll_id=request.form.get('poll_id', 0)))

@app.route('/delete_new_customer_link', methods=['POST'])
def delete_new_customer_link():
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    auth.check_csrf_token(request.form.get('csrf_token'))
    error = link.process_delete_new_customer_link(request.form.get('url_id'))
    if error is None:
        flash('Linkin poistaminen onnistui')
    else:
        flash('Virhe! Linkin poistaminen epäonnistui: ' + error)

    return redirect(url_for('poll_customers',
                            poll_id=request.form.get('poll_id', 0)))

@app.route('/delete_member_access_link', methods=['POST'])
def delete_member_access_link():
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    auth.check_csrf_token(request.form.get('csrf_token'))
    error = link.process_delete_member_access_link(request.form.get('url_id'))
    if error is None:
        flash('Linkin poistaminen onnistui')
    else:
        flash('Virhe! Linkin poistaminen epäonnistui: ' + error)

    if request.form.get('member_type') == 'customer':
        redirect_route = 'poll_customers'
    else:
        redirect_route = 'poll_resources'

    return redirect(url_for(redirect_route,
                            poll_id=request.form.get('poll_id', 0)))

@app.route('/new_time_preference', methods=['POST'])
def new_time_preference():
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    auth.check_csrf_token(request.form.get('csrf_token'))

    # request was generated by javascript
    if request.form.get('data') is not None:
        error = times.process_grading_list(request.form.get('member_id'),
                                           request.form.get('data'))
    # if no js was available
    else:
        error = times.process_grading_fallback(request.form.get('member_id'),
                                               request.form.get('start'),
                                               request.form.get('end'),
                                               request.form.get('date'),
                                               request.form.get('satisfaction'))
    if error is None:
        flash('Aikavalintojen tallentaminen onnistui')
    else:
        flash('Virhe! Aikavalintojen tallentaminen epäonnistui: ' + error)

    return redirect(url_for('poll_times',
                            poll_id=request.form.get('poll_id', 0),
                            member_id=request.form.get('member_id', 0),
                            selected_day=request.form.get('selected_day', 0)))

@app.route('/optimize_poll', methods=['POST'])
def optimize_poll():
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    auth.check_csrf_token(request.form.get('csrf_token'))
    error = optimization.process_optimize_poll(request.form.get('poll_id'))
    if error is None:
        flash('Ajanvarauksien optimoiminen onnistui')
    else:
        flash('Virhe! Ajanvarauksien optimoiminen epäonnistui: ' + error)

    return redirect(url_for('poll_optimization',
                            poll_id=request.form.get('poll_id', 0)))

@app.route('/set_results_final', methods=['POST'])
def set_results_final():
    if 'user_id' not in session:
        flash('Virhe! Kirjaudu ensin sisään')
        return redirect(url_for('login'))

    auth.check_csrf_token(request.form.get('csrf_token'))
    error = poll.process_set_results_final(request.form.get('poll_id'))
    if error is None:
        flash('Kyselyn tulokset julkaistu')
    else:
        flash('Virhe! Kyselyn tulosten julkaiseminen epäonnistui: ' + error)

    return redirect(url_for('poll_optimization',
                            poll_id=request.form.get('poll_id', 0)))
