from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes.extensions import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if 'user_id' in session:
        if session['emp_type'] == 'admin':
            return redirect(url_for('tasks.admin_dashboard'))
        else:
            return redirect(url_for('tasks.employee_dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = db.verify_user(email, password)

        if user:
            session['user_id'] = user[0]
            session['first_name'] = user[1]
            session['last_name'] = user[2]
            session['emp_type'] = user[3]

            if user[3] == 'admin':
                return redirect(url_for('tasks.admin_dashboard'))
            else:
                return redirect(url_for('employees.employee_profile_view'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('login.html')


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
