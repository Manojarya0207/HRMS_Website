import os
from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash, current_app)
from werkzeug.utils import secure_filename
from routes.extensions import get_db_connection, db

assets_bp = Blueprint('assets', __name__)


# ── Admin: Assets ─────────────────────────────────────────────────────────────

@assets_bp.route('/admin/add_asset', methods=['GET', 'POST'])
def add_asset():
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO TblAssets (ItemName, Model, Price, Descriptions, Status) VALUES (?, ?, ?, ?, ?)',
            (request.form['item_name'], request.form['model'],
             request.form['price'], request.form['descriptions'], request.form['status']))
        conn.commit()
        conn.close()
        flash('Asset added successfully!', 'success')
        return redirect(url_for('assets.view_assets'))
    return render_template('add_asset.html')


@assets_bp.route('/admin/view_assets')
def view_assets():
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))
    conn   = get_db_connection()
    assets = conn.execute('SELECT * FROM TblAssets').fetchall()
    conn.close()
    return render_template('view_assets.html', assets=assets)


@assets_bp.route('/admin/edit_asset/<int:asset_id>', methods=['GET', 'POST'])
def edit_asset(asset_id):
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))
    conn  = get_db_connection()
    asset = conn.execute('SELECT * FROM TblAssets WHERE AssetId = ?', (asset_id,)).fetchone()
    if request.method == 'POST':
        conn.execute(
            'UPDATE TblAssets SET ItemName=?, Model=?, Price=?, Descriptions=?, Status=? WHERE AssetId=?',
            (request.form['item_name'], request.form['model'],
             request.form['price'], request.form['descriptions'],
             request.form['status'], asset_id))
        conn.commit()
        conn.close()
        flash('Asset updated successfully!', 'success')
        return redirect(url_for('assets.view_assets'))
    conn.close()
    return render_template('edit_asset.html', asset=asset)


@assets_bp.route('/admin/delete_asset/<int:asset_id>')
def delete_asset(asset_id):
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM TblAssets WHERE AssetId = ?', (asset_id,))
    conn.commit()
    conn.close()
    flash('Asset deleted successfully!', 'success')
    return redirect(url_for('assets.view_assets'))


# ── Admin: Allocation ─────────────────────────────────────────────────────────

@assets_bp.route('/admin/allocate_asset', methods=['GET', 'POST'])
def allocate_asset():
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    conn      = get_db_connection()
    assets    = conn.execute("SELECT * FROM TblAssets WHERE Status = 'Available'").fetchall()
    employees = conn.execute(
        "SELECT emp_id, first_name, last_name FROM tbl_employee WHERE status = 'active'").fetchall()
    selected_asset_id = request.args.get('asset_id', type=int)

    if request.method == 'POST':
        conn.execute('''
            INSERT INTO TblAllocateAssets (AssetId, EmployeeId, AllocateDate, Status, AllocatedBy, Description)
            VALUES (?, ?, DATE('now'), 'Allocated', ?, ?)
        ''', (request.form['asset_id'], request.form['employee_id'],
              request.form['allocated_by'], request.form['description']))
        conn.execute("UPDATE TblAssets SET Status = 'Allocated' WHERE AssetId = ?",
                     (request.form['asset_id'],))
        conn.commit()
        conn.close()
        flash('Asset allocated successfully', 'success')
        return redirect(url_for('assets.manage_allocation'))

    conn.close()
    return render_template('allocate_asset.html',
                           assets=assets,
                           employees=employees,
                           selected_asset_id=selected_asset_id)


@assets_bp.route('/admin/manage_allocation')
def manage_allocation():
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT aa.*, a.ItemName, a.Model, e.first_name, e.last_name,
            (
                SELECT GROUP_CONCAT(IssueId || '##' || IssueText, '||')
                FROM TblAssetIssues
                WHERE AssetId = aa.AssetId AND EmployeeId = aa.EmployeeId AND Status = 'Open'
            ) AS Issues
        FROM TblAllocateAssets aa
        JOIN TblAssets a ON aa.AssetId = a.AssetId
        JOIN tbl_employee e ON aa.EmployeeId = e.emp_id
        ORDER BY aa.AllocateDate DESC
    ''').fetchall()
    conn.close()
    return render_template('manage_allocation.html', allocations=rows)


@assets_bp.route('/admin/edit_allocation/<int:alloc_id>', methods=['GET', 'POST'])
def edit_allocation(alloc_id):
    conn       = get_db_connection()
    allocation = conn.execute('''
        SELECT aa.*, a.ItemName, a.Model, e.first_name, e.last_name
        FROM TblAllocateAssets aa
        JOIN TblAssets a ON aa.AssetId = a.AssetId
        JOIN tbl_employee e ON aa.EmployeeId = e.emp_id
        WHERE aa.AllocatedId = ?
    ''', (alloc_id,)).fetchone()

    if request.method == 'POST':
        conn.execute("UPDATE TblAllocateAssets SET Status = 'Returned' WHERE AllocatedId = ?",
                     (alloc_id,))
        conn.execute("UPDATE TblAssets SET Status = 'Available' WHERE AssetId = ?",
                     (allocation['AssetId'],))
        conn.commit()
        conn.close()
        flash('Asset returned', 'success')
        return redirect(url_for('assets.manage_allocation'))

    conn.close()
    return render_template('edit_allocation.html', allocation=allocation)


@assets_bp.route('/admin/asset_history', methods=['GET'])
def asset_history():
    selected_emp_id = request.args.get('employee_id', type=int)
    conn      = get_db_connection()
    employees = conn.execute(
        "SELECT emp_id, first_name, last_name FROM tbl_employee WHERE Status = 'active'").fetchall()
    history = []
    if selected_emp_id:
        history = conn.execute('''
            SELECT aa.*, a.ItemName, a.Model FROM TblAllocateAssets aa
            JOIN TblAssets a ON aa.AssetId = a.AssetId
            WHERE aa.EmployeeId = ?
            ORDER BY aa.AllocateDate DESC
        ''', (selected_emp_id,)).fetchall()
    conn.close()
    return render_template('asset_history.html',
                           employees=employees,
                           history=history,
                           selected_emp_id=selected_emp_id)


# ── Employee: Assets & Issues ─────────────────────────────────────────────────

@assets_bp.route('/employee/assets')
def employee_assets():
    if 'user_id' not in session or session['emp_type'] != 'emp':
        return redirect(url_for('auth.login'))

    conn   = get_db_connection()
    assets = conn.execute('''
        SELECT aa.*, a.ItemName, a.Model
        FROM TblAllocateAssets aa
        JOIN TblAssets a ON aa.AssetId = a.AssetId
        WHERE aa.EmployeeId = ? AND aa.Status = 'Allocated'
        ORDER BY aa.AllocateDate DESC
    ''', (session['user_id'],)).fetchall()

    issues = conn.execute('''
        SELECT * FROM TblAssetIssues
        WHERE EmployeeId = ?
        ORDER BY ReportedDate DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()

    open_issues_by_asset     = {}
    resolved_issues_by_asset = {}
    for i in issues:
        if i['Status'] == 'Resolved':
            resolved_issues_by_asset.setdefault(i['AssetId'], []).append(i)
        else:
            open_issues_by_asset.setdefault(i['AssetId'], []).append(i)

    return render_template('employee_assets.html',
                           assets=assets,
                           open_issues_by_asset=open_issues_by_asset,
                           resolved_issues_by_asset=resolved_issues_by_asset)


@assets_bp.route('/employee/report_issue/<int:asset_id>', methods=['POST'])
def report_asset_issue(asset_id):
    if 'user_id' not in session or session['emp_type'] != 'emp':
        return redirect(url_for('auth.login'))

    issue_text = request.form['issue_text'].strip()
    if issue_text:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO TblAssetIssues (AssetId, EmployeeId, IssueText) VALUES (?, ?, ?)',
            (asset_id, session['user_id'], issue_text))
        conn.commit()
        conn.close()
        flash('Issue reported successfully', 'success')
    else:
        flash('Issue text cannot be empty.', 'error')

    return redirect(url_for('assets.employee_assets'))


@assets_bp.route('/admin/resolve_issue/<int:issue_id>', methods=['POST'])
def resolve_issue(issue_id):
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    comment = request.form.get('resolved_comment', '').strip()
    if not comment:
        flash('Resolution comment is required.', 'error')
        return redirect(url_for('assets.manage_allocation'))

    conn = get_db_connection()
    conn.execute('''
        UPDATE TblAssetIssues
        SET Status = 'Resolved',
            ResolvedComment = ?,
            ResolvedDate = DATE('now')
        WHERE IssueId = ?
    ''', (comment, issue_id))
    conn.commit()
    conn.close()
    flash('Issue marked as resolved.', 'success')
    return redirect(url_for('assets.manage_allocation'))
