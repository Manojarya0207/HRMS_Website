import math
import logging
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from routes.extensions import db

logger = logging.getLogger(__name__)

tasks_bp = Blueprint('tasks', __name__)


# ── Admin: Dashboard ──────────────────────────────────────────────────────────

@tasks_bp.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    page           = int(request.args.get('page', 1))
    page_size      = 10
    project_filter = request.args.get('project_filter', '')
    status_filter  = request.args.get('status_filter', '')
    employee_filter = request.args.get('employee_filter', '')

    tasks, total_tasks = db.get_all_tasks_with_details_paginated(
        page, page_size, project_filter, status_filter, employee_filter)
    employees   = db.get_employees()
    projects    = db.get_projects()
    total_pages = math.ceil(total_tasks / page_size)

    return render_template('admin_dashboard.html',
                           tasks=tasks, employees=employees, projects=projects,
                           page=page, page_size=page_size,
                           total_tasks=total_tasks, total_pages=total_pages,
                           project_filter=project_filter,
                           status_filter=status_filter,
                           employee_filter=employee_filter)


# ── Admin: Task Management ────────────────────────────────────────────────────

@tasks_bp.route('/admin/view_tasks')
def view_tasks():
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    page           = int(request.args.get('page', 1))
    page_size      = 10
    project_filter = request.args.get('project_filter', '')
    status_filter  = request.args.get('status_filter', '')
    employee_filter = request.args.get('employee_filter', '')

    tasks, total_tasks = db.get_all_tasks_with_details_paginated(
        page, page_size, project_filter, status_filter, employee_filter)
    employees   = db.get_employees()
    projects    = db.get_projects()
    total_pages = math.ceil(total_tasks / page_size)

    return render_template('view_tasks.html',
                           tasks=tasks, employees=employees, projects=projects,
                           page=page, page_size=page_size,
                           total_tasks=total_tasks, total_pages=total_pages,
                           project_filter=project_filter,
                           status_filter=status_filter,
                           employee_filter=employee_filter)


@tasks_bp.route('/admin/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    task = db.get_task(task_id)
    if not task:
        flash('Task not found.', 'error')
        return redirect(url_for('tasks.view_tasks'))

    if request.method == 'POST':
        task_data = {
            'project_id': request.form['project_id'],
            'emp_id':     request.form['emp_id'],
            'task_desc':  request.form['task_desc'],
            'priority':   request.form['priority'],
            'status':     request.form['status'],
            'start_date': request.form['start_date'],
            'end_date':   request.form['end_date'],
        }
        try:
            db.update_task(task_id, task_data)
            flash('Task updated successfully!', 'success')
            return redirect(url_for('tasks.view_tasks'))
        except Exception:
            flash('Error updating task.', 'error')

    projects  = db.get_projects()
    employees = db.get_employees()
    return render_template('edit_task.html', task=task, projects=projects, employees=employees)


@tasks_bp.route('/admin/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    try:
        db.delete_task(task_id)
        flash('Task deleted successfully!', 'success')
    except Exception:
        flash('Error deleting task.', 'error')

    return redirect(url_for('tasks.view_tasks'))


@tasks_bp.route('/admin/add_task', methods=['GET', 'POST'])
def add_task():
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        task_data = {
            'project_id': request.form['project_id'],
            'emp_id':     request.form['emp_id'],
            'task_desc':  request.form['task_desc'],
            'priority':   request.form['priority'],
            'status':     request.form['status'],
            'start_date': request.form['start_date'],
            'end_date':   request.form['end_date'],
        }
        try:
            db.add_task(task_data)
            flash('Task added successfully!', 'success')
            return redirect(url_for('tasks.view_tasks'))
        except Exception:
            flash('Error adding task.', 'error')

    projects  = db.get_projects()
    employees = db.get_employees()
    today     = date.today().isoformat()
    return render_template('add_task.html', projects=projects, employees=employees, today=today)


@tasks_bp.route('/admin/show_task_details/<int:task_id>')
def show_task_details(task_id):
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    task = db.get_task(task_id)
    if not task:
        flash('Task not found.', 'error')
        return redirect(url_for('tasks.admin_dashboard'))

    project      = db.get_project(task[2])
    employee     = db.get_employee(task[3])
    task_details = db.get_task_details(task_id)

    return render_template('show_task_details.html',
                           task=task, project=project,
                           employee=employee, task_details=task_details)


# ── Admin: Quick Delete ───────────────────────────────────────────────────────

@tasks_bp.route('/admin/quick_delete', methods=['GET'])
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

    return render_template('admin_quick_delete.html', category=category, data=data)


@tasks_bp.route('/admin/delete_all/<category>', methods=['POST'])
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

    return redirect(url_for('tasks.admin_quick_delete', category=category))


# ── Employee: Dashboard & Tasks ───────────────────────────────────────────────

@tasks_bp.route('/employee/dashboard')
def employee_dashboard():
    if 'user_id' not in session or session['emp_type'] != 'emp':
        return redirect(url_for('auth.login'))

    profile = db.get_employee_profile(session['user_id'])

    emg_missing = (
        not profile
        or not profile.get('EmgContact')
        or profile.get('EmgUpdatedByEmp') == 0
    )
    session['emg_missing'] = emg_missing

    status_filter = request.args.get('status_filter', 'all')
    tasks = db.get_tasks_by_employee(session['user_id'], status_filter=status_filter)
    today = date.today()

    return render_template('employee_dashboard.html',
                           tasks=tasks, emg_missing=emg_missing,
                           status_filter=status_filter, today=today)


@tasks_bp.route('/employee/add_task_detail', methods=['POST'])
def add_task_detail():
    if 'user_id' not in session or session['emp_type'] != 'emp':
        return redirect(url_for('auth.login'))

    task_id = request.form['task_id']
    desc    = request.form['desc']
    status  = request.form['status']

    try:
        db.add_task_detail(task_id, desc, status, session['user_id'])
        flash('Task update added successfully!', 'success')
    except Exception:
        flash('Error adding task update.', 'error')

    return redirect(url_for('tasks.view_task_details', task_id=task_id))


@tasks_bp.route('/employee/view_task_details/<int:task_id>')
def view_task_details(task_id):
    if 'user_id' not in session or session['emp_type'] != 'emp':
        return redirect(url_for('auth.login'))

    task = db.get_task(task_id)
    if not task or task[3] != session['user_id']:
        flash('Task not found or you do not have permission to view it.', 'error')
        return redirect(url_for('tasks.employee_dashboard'))

    details = db.get_task_details_by_employee(task_id, session['user_id'])
    project = db.get_project(task[2])
    return render_template('view_task_details.html', task=task, details=details, project=project)


@tasks_bp.route('/employee/edit_task_detail/<int:detail_id>', methods=['GET', 'POST'])
def edit_task_detail(detail_id):
    if 'user_id' not in session or session['emp_type'] != 'emp':
        return redirect(url_for('auth.login'))

    detail = db.get_task_detail(detail_id)
    if not detail or not db.verify_task_detail_owner(detail_id, session['user_id']):
        flash('Task update not found or you do not have permission to edit it.', 'error')
        return redirect(url_for('tasks.employee_dashboard'))

    if request.method == 'POST':
        desc   = request.form['desc']
        status = request.form['status']
        try:
            db.update_task_detail(detail_id, desc, status)
            flash('Task update edited successfully!', 'success')
            return redirect(url_for('tasks.view_task_details', task_id=detail[1]))
        except Exception:
            flash('Error editing task update.', 'error')

    return render_template('edit_task_detail.html', detail=detail, task_id=detail[1])


# ── API ───────────────────────────────────────────────────────────────────────

@tasks_bp.route('/api/update_task_status', methods=['POST'])
def update_task_status():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    task_id = data.get('task_id')
    new_status = data.get('status')
    
    if not task_id or not new_status:
        return jsonify({'error': 'Bad request'}), 400
        
    try:
        db.update_task_status_only(task_id, new_status)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Reports & Kanban ──────────────────────────────────────────────────────────

@tasks_bp.route('/admin/reports')
def admin_reports():
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))
        
    project_filter = request.args.get('project_filter', '')
    status_filter = request.args.get('status_filter', '')
    employee_filter = request.args.get('employee_filter', '')
    search_query = request.args.get('search_query', '')
    page = int(request.args.get('page', 1))
        
    status_counts = db.get_admin_task_status_counts(project_filter, employee_filter, search_query)
    project_counts = db.get_admin_project_task_counts(status_filter, employee_filter, search_query)
    employee_counts = db.get_admin_employee_task_counts(project_filter, status_filter, search_query)
    recent_activities = db.get_recent_task_activities(limit=20, project_filter=project_filter, status_filter=status_filter, employee_filter=employee_filter, search_query=search_query)
    tasks, total_tasks = db.get_all_tasks_with_details_paginated(page, 20, project_filter=project_filter, status_filter=status_filter, employee_filter=employee_filter, search_query=search_query)
    
    employees = db.get_employees()
    projects = db.get_projects()
    total_pages = math.ceil(total_tasks / 20)
    
    return render_template('admin_reports.html',
                           status_counts=status_counts,
                           project_counts=project_counts,
                           employee_counts=employee_counts,
                           recent_activities=recent_activities,
                           tasks=tasks,
                           total_tasks=total_tasks,
                           total_pages=total_pages,
                           page=page,
                           employees=employees,
                           projects=projects,
                           project_filter=project_filter,
                           status_filter=status_filter,
                           employee_filter=employee_filter,
                           search_query=search_query)

@tasks_bp.route('/employee/reports')
def employee_reports():
    if 'user_id' not in session or session['emp_type'] != 'emp':
        return redirect(url_for('auth.login'))
        
    project_filter = request.args.get('project_filter', '')
    status_filter = request.args.get('status_filter', '')
    search_query = request.args.get('search_query', '')
        
    status_counts = db.get_employee_task_status_counts(session['user_id'], project_filter, search_query)
    recent_activities = db.get_recent_task_activities(limit=20, emp_id=session['user_id'], project_filter=project_filter, status_filter=status_filter, search_query=search_query)
    tasks = db.get_tasks_by_employee(session['user_id'], status_filter=status_filter, project_filter=project_filter, search_query=search_query)
    
    projects = db.get_projects()
    
    return render_template('employee_reports.html',
                           status_counts=status_counts,
                           recent_activities=recent_activities,
                           tasks=tasks,
                           projects=projects,
                           project_filter=project_filter,
                           status_filter=status_filter,
                           search_query=search_query)

@tasks_bp.route('/employee/kanban')
def employee_kanban():
    if 'user_id' not in session or session['emp_type'] != 'emp':
        return redirect(url_for('auth.login'))
        
    tasks = db.get_tasks_by_employee(session['user_id'])
    return render_template('kanban_board.html', tasks=tasks, is_admin=False)


# ── Existing APIs ──────────────────────────────────────────────────────────────

@tasks_bp.route('/api/task_details/<int:task_id>')
def get_task_details(task_id):
    try:
        if 'user_id' not in session:
            logger.warning(f'Unauthorized access attempt to task details for task_id {task_id}')
            return jsonify({'error': 'Unauthorized'}), 401

        task = db.get_task(task_id)
        if not task:
            logger.warning(f'Task not found for task_id {task_id}')
            return jsonify({'error': 'Task not found'}), 404

        details = db.get_task_details(task_id)
        details_list = [
            {
                'detail_id':     d[0],
                'desc':          d[1],
                'inserted_date': d[2] if d[2] else None,
                'status':        d[3],
            }
            for d in details
        ]
        logger.debug(f'Successfully fetched {len(details_list)} task details for task_id {task_id}')
        return jsonify(details_list)

    except Exception as e:
        logger.error(f'Error in get_task_details for task_id {task_id}: {str(e)}', exc_info=True)
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@tasks_bp.route('/api/task_detail/<int:detail_id>')
def api_get_task_detail(detail_id):
    if 'user_id' not in session or session['emp_type'] != 'emp':
        return jsonify({'error': 'Unauthorized'}), 401

    detail = db.get_task_detail(detail_id)
    if not detail or not db.verify_task_detail_owner(detail_id, session['user_id']):
        return jsonify({'error': 'Not found'}), 404

    task = db.get_task(detail[1])
    return jsonify({
        'detail_id': detail[0],
        'task_id':   detail[1],
        'desc':      detail[2],
        'status':    detail[4],
        'task_name': task[1] if task else '',
    })
