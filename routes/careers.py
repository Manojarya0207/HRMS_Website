import os
from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash, current_app)
from werkzeug.utils import secure_filename
from routes.extensions import get_db_connection, UPLOAD_FOLDER

careers_bp = Blueprint('careers', __name__)


@careers_bp.route('/admin/add_job', methods=['GET', 'POST'])
def add_job():
    if request.method == 'POST':
        jobtitle = request.form['jobtitle']
        exp      = request.form['exp']
        sal      = request.form['sal']
        location = request.form['location']
        desc     = request.form['desc']
        file     = request.files['banner']
        filename = ''

        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO TblCareers (JobTitle, Exp, Sal, Location, Description, BannerImg) VALUES (?, ?, ?, ?, ?, ?)',
            (jobtitle, exp, sal, location, desc, filename))
        conn.commit()
        conn.close()
        return redirect(url_for('careers.view_jobs'))

    return render_template('add_job.html')


@careers_bp.route('/admin/view_jobs')
def view_jobs():
    conn = get_db_connection()
    jobs = conn.execute('SELECT * FROM TblCareers').fetchall()
    conn.close()
    return render_template('view_jobs.html', jobs=jobs)


@careers_bp.route('/admin/delete_job/<int:id>')
def delete_job(id):
    conn = get_db_connection()
    job  = conn.execute('SELECT BannerImg FROM TblCareers WHERE CareerId = ?', (id,)).fetchone()

    if job and job['BannerImg']:
        img_path = os.path.join(current_app.root_path, 'static', 'bngImg', job['BannerImg'])
        if os.path.exists(img_path):
            os.remove(img_path)

    conn.execute('DELETE FROM TblCareers WHERE CareerId = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('careers.view_jobs'))


@careers_bp.route('/admin/edit_job/<int:id>', methods=['GET', 'POST'])
def edit_job(id):
    conn = get_db_connection()
    job  = conn.execute('SELECT * FROM TblCareers WHERE CareerId = ?', (id,)).fetchone()

    if request.method == 'POST':
        jobtitle = request.form['jobtitle']
        exp      = request.form['exp']
        sal      = request.form['sal']
        location = request.form['location']
        desc     = request.form['desc']
        file     = request.files['banner']
        filename = job['BannerImg']

        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))

        conn.execute(
            'UPDATE TblCareers SET JobTitle=?, Exp=?, Sal=?, Location=?, Description=?, BannerImg=? WHERE CareerId=?',
            (jobtitle, exp, sal, location, desc, filename, id))
        conn.commit()
        conn.close()
        return redirect(url_for('careers.view_jobs'))

    conn.close()
    return render_template('edit_job.html', job=job)


@careers_bp.route('/employee/careers')
def employee_careers():
    conn = get_db_connection()
    jobs = conn.execute('SELECT * FROM TblCareers').fetchall()
    conn.close()
    return render_template('employee_careers.html', jobs=jobs)
