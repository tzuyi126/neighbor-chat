import functools, re, psycopg

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from flaskr.db import execute, fetch_all, fetch_one
from flaskr.geolocate import find_coord

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']

        addr_street = request.form['addr_street']
        addr_city = request.form['addr_city']
        addr_state = request.form['addr_state']
        addr_zip = request.form['addr_zip']

        profile = request.form['profile']

        error = None

        if not firstname:
            error = 'First name is required.'
        elif not lastname:
            error = 'Last name is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif not is_valid_email(email):
            error = 'Please provide valid email address.'
        elif not is_valid_password(password):
            error = 'Password requires at least 8 and at most 16 characters.'
        elif not addr_street:
            error = 'Address is required.'
        elif not addr_city:
            error = 'City is required.'
        elif not addr_state:
            error = 'State is required.'
        elif not addr_zip:
            error = 'Zip Code is required.'
        
        try:
            lat, lon = find_coord(addr_street, addr_city, addr_state, addr_zip)
        except:
            error = 'Please provide valid address.'

        if error is None:
            try:
                execute(
                    'INSERT INTO users (password, first_name, last_name, profile, email, phone_number, '
                    'addr_street, addr_city, addr_state, addr_zip, ulatitude, ulongitude) '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (password, firstname, lastname, profile, email, phone, 
                     addr_street, addr_city, addr_state, addr_zip, lat, lon),
                )

            except psycopg.IntegrityError:
                error = f"This email '{email}' has already registered."
            except psycopg.Error as e:
                error = e
            else:
                flash("Registered successfully!")
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        error = None
        
        user = fetch_one(
            'SELECT * FROM users WHERE email = %s', (email,)
        )

        if user is None:
            error = 'Incorrect email.'
        elif user['password'] != password:
            error = f'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['uid']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = fetch_one(
            'SELECT * FROM users WHERE uid = %s', (user_id,)
        )

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@bp.route('/update', methods=('GET', 'POST'))
def update():
    if request.method == 'POST':
        uid = g.user['uid']

        firstname = request.form['firstname'].strip()
        lastname = request.form['lastname'].strip()
        password = request.form['password'].strip()
        phone = request.form['phone'].strip()

        addr_street = request.form['addr_street'].strip()
        addr_city = request.form['addr_city'].strip()
        addr_state = request.form['addr_state'].strip()
        addr_zip = request.form['addr_zip'].strip()

        profile = request.form['profile'].strip()

        error = None

        if not firstname:
            error = 'First name is required.'
        elif not lastname:
            error = 'Last name is required.'
        elif not password:
            password = g.user['password']
        elif not is_valid_password(password):
            error = 'Password requires at least 8 and at most 16 characters.'
        elif not addr_street:
            error = 'Address is required.'
        elif not addr_city:
            error = 'City is required.'
        elif not addr_state:
            error = 'State is required.'
        elif not addr_zip:
            error = 'Zip Code is required.'
        
        try:
            lat, lon = find_coord(addr_street, addr_city, addr_state, addr_zip)
        except:
            error = 'Please provide valid address.'

        if error is None:
            try:
                execute(
                    'UPDATE users SET password = %s, first_name = %s, last_name = %s, profile = %s, phone_number = %s, '
                    'addr_street = %s, addr_city = %s, addr_state = %s, addr_zip = %s, ulatitude = %s, ulongitude = %s '
                    'WHERE uid = %s',
                    (password, firstname, lastname, profile, phone, 
                     addr_street, addr_city, addr_state, addr_zip, lat, lon, uid),
                )

            except psycopg.Error as e:
                error = e
            else:
                flash("Updated successfully!")
                return redirect(url_for('auth.update'))

        flash(error)

    return render_template('auth/update.html')

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

def is_valid_email(email):
    """Check if the email is a valid format."""

    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$'

    if re.match(regex, email):
        return True
    else:
        return False
    
def is_valid_password(password):
    if len(password) < 8:
        return False
    elif len(password) > 16:
        return False
    else:
        return True
