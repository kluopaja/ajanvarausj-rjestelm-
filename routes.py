from app import app
from flask import render_template
from werkzeug.urls import url_parse
from flask import session, request, redirect

from utils import process_login, process_registration, process_logout
from utils import check_poll_validity, process_new_poll
from utils import Poll

@app.route('/')
def index():
    polls = [(str(i), f'kysely {i}') for i in range(4)]
    return render_template("index.html", polls=polls)


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

