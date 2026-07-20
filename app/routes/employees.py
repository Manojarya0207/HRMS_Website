"""Dashboard, employee CRUD, registration-request, profile and quick-delete
routes (moved verbatim from app.py)."""
import math
from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from app.extensions import db

employees_bp = Blueprint('employees', __name__)


@employees_bp.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    # Pagination parameters
    page = int(request.args.get('page', 1))
    page_size = 10
    project_filter = request.args.get('project_filter', '')
    status_filter = request.args.get('status_filter', '')
    employee_filter = request.args.get('employee_filter', '')

    # Get paginated tasks and total task count
    tasks, total_tasks = db.get_all_tasks_with_details_paginated(page, page_size, project_filter, status_filter, employee_filter)
    employees = db.get_employees()
    projects = db.get_projects()

    # Calculate total pages
    total_pages = math.ceil(total_tasks / page_size)

    return render_template('dashboard/admin_dashboard.html',
                         tasks=tasks,
                         employees=employees,
                         projects=projects,
                         page=page,
                         page_size=page_size,
                         total_tasks=total_tasks,
                         total_pages=total_pages,
                         project_filter=project_filter,
                         status_filter=status_filter,
                         employee_filter=employee_filter)

@employees_bp.route('/admin/registration_requests')
def registration_requests():
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    status_filter = request.args.get('status', 'pending')
    reqs = db.get_registration_requests(status=status_filter)
    return render_template('employees/registration_requests.html', requests=reqs, status_filter=status_filter)

@employees_bp.route('/admin/reject_registration/<int:req_id>')
def reject_registration(req_id):
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    try:
        db.update_registration_status(req_id, 'rejected')
        flash('Registration request rejected successfully.', 'success')
    except Exception as e:
        flash(f'Error rejecting request: {e}', 'error')

    return redirect(url_for('employees.registration_requests'))

@employees_bp.route('/admin/reaccept_registration/<int:req_id>')
def reaccept_registration(req_id):
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    try:
        db.update_registration_status(req_id, 'pending')
        flash('Registration request reaccepted/restored to pending.', 'success')
    except Exception as e:
        flash(f'Error reaccepting request: {e}', 'error')

    return redirect(url_for('employees.registration_requests', status='pending'))

@employees_bp.route('/admin/view_employees')
def view_employees():
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    status_filter = request.args.get('status_filter', 'all')
    employees = db.get_employees(status_filter=status_filter)

    return render_template('employees/view_employees.html', employees=employees, status_filter=status_filter)

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
            'last_name': request.form['last_name'],
            'gender': request.form['gender'],
            'dob': request.form['dob'],
            'address': request.form['address'],
            'phone_no': request.form['phone_no'],
            'email': request.form['email'],
            'password': request.form['password'],
            'status': request.form['status'],
            'emp_type': request.form['emp_type']
        }

        try:
            db.update_employee(emp_id, employee_data)
            flash('Employee updated successfully!', 'success')
            return redirect(url_for('employees.view_employees'))
        except Exception as e:
            flash('Error updating employee. Email might already exist.', 'error')

    employee_statuses = db.get_employee_statuses()
    return render_template('employees/edit_employee.html', employee=employee, employee_statuses=employee_statuses)

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

    req_id = request.args.get('req_id') or request.form.get('req_id')
    prefill = {}

    if req_id:
        req_data = db.get_registration_request(req_id)
        if req_data:
            # req_data: request_id, first_name, last_name, gender, dob, address, phone_no, email, password, department, status, inserted_date
            prefill = {
                'first_name': req_data[1],
                'last_name': req_data[2],
                'gender': req_data[3],
                'dob': req_data[4],
                'address': req_data[5],
                'phone_no': req_data[6],
                'email': req_data[7],
                'password': req_data[8],
                'department': req_data[9]
            }

        email_val = request.form.get('email', '').strip()
        if not email_val:
            from app.utils import generate_login_id
            email_val = generate_login_id(request.form['first_name'], request.form['last_name'], request.form['phone_no'])

        employee_data = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'gender': request.form['gender'],
            'dob': request.form['dob'],
            'address': request.form['address'],
            'phone_no': request.form['phone_no'],
            'email': email_val,
            'password': request.form['password'],
            'status': request.form['status'],
            'emp_type': request.form['emp_type'],
            'department': request.form.get('department')
        }

        try:
            emp_id = db.add_employee(employee_data)
            if req_id:
                db.update_registration_status(req_id, 'approved')
            flash('Employee added successfully!', 'success')
            return redirect(url_for('employees.manage_profile', emp_id=emp_id))
        except Exception as e:
            flash('Error adding employee. Login ID might already exist.', 'error')
            prefill = employee_data

    employee_statuses = db.get_employee_statuses()
    return render_template('employees/add_employee.html', prefill=prefill, req_id=req_id, employee_statuses=employee_statuses)

@employees_bp.route('/employee/dashboard')
def employee_dashboard():
    if 'user_id' not in session or session['emp_type'] != 'emp':
        return redirect(url_for('auth.login'))

    profile = db.get_employee_profile(session['user_id'])

    # 🔐 Restrict sidebar if:
    # - EmgContact is blank
    # - OR employee never updated it
    emg_missing = (
        not profile
        or not profile.get('EmgContact')
        or profile.get('EmgUpdatedByEmp') == 0
    )

    session['emg_missing'] = False  # Ensure sidebar links are never disabled

    status_filter = request.args.get('status_filter', 'all')
    tasks = db.get_tasks_by_employee(session['user_id'], status_filter=status_filter)
    today = date.today()  # Get current date
    return render_template('dashboard/employee_dashboard.html', tasks=tasks, emg_missing=emg_missing, status_filter=status_filter, today=today)

@employees_bp.route('/employee/my_profile', methods=['GET', 'POST'])
def employee_profile_view():
    if 'user_id' not in session or session['emp_type'] != 'emp':
        return redirect(url_for('auth.login'))

    emp_id = session['user_id']
    employee = db.get_employee(emp_id)
    profile = db.get_employee_profile(emp_id)
    alert_msg = None  # This will be passed as a flash or query param

    if request.method == 'POST':
        new_password = request.form.get('password', '').strip()
        new_emg = request.form.get('EmgContact', '').strip()

        alert_msg = db.update_employee_password_and_emgcontact(emp_id, new_password, new_emg)
        # if new_password:
        #     db.update_employee_password(emp_id, new_password)
        #     alert_msg = 'Password updated successfully.'

        # if profile:
        #     current_emg = profile.get('EmgContact', '')
        #     already_updated = profile.get('EmgUpdatedByEmp', 0)

        #     if new_emg:
        #         if already_updated:
        #             alert_msg = 'You have already updated your emergency contact once.'
        #         if not new_emg.isdigit() or len(new_emg) != 10:
        #             alert_msg = 'Emergency contact must be a 10-digit number.'
        #         elif new_emg == employee[6]:  # assuming employee[6] is mobile number
        #             alert_msg = 'Emergency contact cannot be the same as your mobile number.'
        #         else:
        #             updated = db.update_employee_emg_contact_once(emp_id, new_emg)
        #             if updated:
        #                 alert_msg = 'Emergency contact updated successfully.'
        #             else:
        #                 alert_msg = 'Update failed. Please contact admin.'
        #     else:
        #         alert_msg = 'Emergency contact cannot be blank.'

        # Flash message or pass via query string for dashboard
        flash(alert_msg)  # Requires flash setup in app
        return redirect(url_for('employees.employee_dashboard'))

    return render_template('employees/my_profile.html', employee=employee, profile=profile, alert_msg=alert_msg)

@employees_bp.route('/admin/employee_profile/<int:emp_id>', methods=['GET', 'POST'])
def manage_profile(emp_id):
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    employee = db.get_employee(emp_id)
    if not employee:
        flash("Employee not found", "error")
        return redirect(url_for('employees.view_employees'))

    profile = db.get_employee_profile(emp_id)

    if request.method == 'POST':
        data = {
            'EmployeeId': emp_id,
            'UANNo': request.form['UANNo'],
            'PANNO': request.form['PANNO'],
            'AadharNo': request.form['AadharNo'],
            'BankName': request.form['BankName'],
            'BranchName': request.form['BranchName'],
            'ACNo': request.form['ACNo'],
            'IFSCode': request.form['IFSCode'],
            'Designation': request.form['Designation'],
            'EmgContact': request.form['EmgContact'],
            'ReportingMng': request.form['ReportingMng'],
            'DOJ': request.form['DOJ'],
            'PrgLng': request.form['PrgLng'],
            'FrmWrk': request.form['FrmWrk']
        }
        if profile:
            db.update_employee_profile(emp_id, data)
        else:
            db.add_employee_profile(data)
        flash("Profile saved", "success")
        return redirect(url_for('employees.view_employees'))


    return render_template('employees/employee_profile.html', employee=employee, profile=profile)

@employees_bp.route('/admin/quick_delete', methods=['GET'])
def admin_quick_delete():
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    category = request.args.get('category')
    data = []

    if category == 'employee':
        data = db.get_employees()
    elif category == 'task':
        data, _ = db.get_all_tasks_with_details_paginated(1, 9999)
    elif category == 'leave_type':
        data = db.get_leave_types()
    elif category == 'expense_type':
        data = db.get_expense_types()
    elif category == 'sub_expense_type':
        data = db.get_sub_expense_types()


    return render_template('admin/admin_quick_delete.html', category=category, data=data)

@employees_bp.route('/admin/delete_all/<category>', methods=['POST'])
def delete_all_category(category):
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    try:
        if category == 'employee':
            db.delete_all_employees()
        elif category == 'task':
            db.delete_all_tasks()
        elif category == 'leave_type':
            db.delete_all_leave_types()
        elif category == 'expense_type':
            db.delete_all_expense_types()
        elif category == 'sub_expense_type':
            db.delete_all_sub_expense_types()
        flash(f'All {category.replace("_", " ")}s deleted.', 'success')
    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('employees.admin_quick_delete', category=category))
