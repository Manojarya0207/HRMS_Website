from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes.extensions import db

employees_bp = Blueprint('employees', __name__)


# ── Admin: Employee Management ────────────────────────────────────────────────

@employees_bp.route('/admin/view_employees')
def view_employees():
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    status_filter = request.args.get('status_filter', 'all')
    employees = db.get_employees(status_filter=status_filter)

    return render_template('view_employees.html', employees=employees, status_filter=status_filter)


@employees_bp.route('/admin/edit_employee/<int:emp_id>', methods=['GET', 'POST'])
def edit_employee(emp_id):
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    employee = db.get_employee(emp_id)
    if not employee:
        flash('Employee not found.', 'error')
        return redirect(url_for('employees.view_employees'))

    if request.method == 'POST':
        employee_data = {
            'first_name': request.form['first_name'],
            'last_name':  request.form['last_name'],
            'gender':     request.form['gender'],
            'dob':        request.form['dob'],
            'address':    request.form['address'],
            'phone_no':   request.form['phone_no'],
            'email':      request.form['email'],
            'password':   request.form['password'],
            'status':     request.form['status'],
            'emp_type':   request.form['emp_type'],
        }
        try:
            db.update_employee(emp_id, employee_data)
            flash('Employee updated successfully!', 'success')
            return redirect(url_for('employees.view_employees'))
        except Exception:
            flash('Error updating employee. Email might already exist.', 'error')

    return render_template('edit_employee.html', employee=employee)


@employees_bp.route('/admin/delete_employee/<int:emp_id>')
def delete_employee(emp_id):
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    try:
        db.delete_employee(emp_id)
        flash('Employee deleted successfully!', 'success')
    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('employees.view_employees'))


@employees_bp.route('/admin/add_employee', methods=['GET', 'POST'])
def add_employee():
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        employee_data = {
            'first_name': request.form['first_name'],
            'last_name':  request.form['last_name'],
            'gender':     request.form['gender'],
            'dob':        request.form['dob'],
            'address':    request.form['address'],
            'phone_no':   request.form['phone_no'],
            'email':      request.form['email'],
            'password':   request.form['password'],
            'status':     request.form['status'],
            'emp_type':   request.form['emp_type'],
        }
        try:
            emp_id = db.add_employee(employee_data)
            flash('Employee added successfully!', 'success')
            return redirect(url_for('employees.manage_profile', emp_id=emp_id))
        except Exception:
            flash('Error adding employee. Email might already exist.', 'error')

    return render_template('add_employee.html')


@employees_bp.route('/admin/employee_profile/<int:emp_id>', methods=['GET', 'POST'])
def manage_profile(emp_id):
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    employee = db.get_employee(emp_id)
    if not employee:
        flash('Employee not found', 'error')
        return redirect(url_for('employees.view_employees'))

    profile = db.get_employee_profile(emp_id)

    if request.method == 'POST':
        data = {
            'EmployeeId':  emp_id,
            'UANNo':       request.form['UANNo'],
            'PANNO':       request.form['PANNO'],
            'AadharNo':    request.form['AadharNo'],
            'BankName':    request.form['BankName'],
            'BranchName':  request.form['BranchName'],
            'ACNo':        request.form['ACNo'],
            'IFSCode':     request.form['IFSCode'],
            'Designation': request.form['Designation'],
            'EmgContact':  request.form['EmgContact'],
            'ReportingMng': request.form['ReportingMng'],
            'DOJ':         request.form['DOJ'],
            'PrgLng':      request.form['PrgLng'],
            'FrmWrk':      request.form['FrmWrk'],
        }
        if profile:
            db.update_employee_profile(emp_id, data)
        else:
            db.add_employee_profile(data)
        flash('Profile saved', 'success')
        return redirect(url_for('employees.view_employees'))

    return render_template('employee_profile.html', employee=employee, profile=profile)


# ── Employee: Self-service Profile ───────────────────────────────────────────

@employees_bp.route('/employee/my_profile', methods=['GET', 'POST'])
def employee_profile_view():
    if 'user_id' not in session or session['emp_type'] != 'emp':
        return redirect(url_for('auth.login'))

    emp_id   = session['user_id']
    employee = db.get_employee(emp_id)
    profile  = db.get_employee_profile(emp_id)
    alert_msg = None

    if request.method == 'POST':
        new_password = request.form.get('password', '').strip()
        new_emg      = request.form.get('EmgContact', '').strip()
        alert_msg    = db.update_employee_password_and_emgcontact(emp_id, new_password, new_emg)
        flash(alert_msg)
        return redirect(url_for('tasks.employee_dashboard'))

    return render_template('my_profile.html', employee=employee, profile=profile, alert_msg=alert_msg)
