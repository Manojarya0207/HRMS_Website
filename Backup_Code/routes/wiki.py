import os
from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash, current_app)
from werkzeug.utils import secure_filename
from routes.extensions import db

wiki_bp = Blueprint('wiki', __name__)


# ── Admin: Wiki Categories ────────────────────────────────────────────────────

@wiki_bp.route('/admin/wiki_categories', methods=['GET', 'POST'])
def admin_wiki_categories():
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        category    = request.form['category'].strip()
        img_file    = request.files.get('cat_img')
        img_filename = None
        if img_file and img_file.filename:
            filename     = secure_filename(img_file.filename)
            wiki_folder  = current_app.config['WIKI_CAT_FOLDER']
            img_file.save(os.path.join(wiki_folder, filename))
            img_filename = filename
        db.add_wiki_category(category, img_filename)
        flash(f'Wiki category "{category}" added.', 'success')
        return redirect(url_for('wiki.admin_wiki_categories', msg=f'"{category}" saved'))

    cats = db.get_wiki_categories()
    msg  = request.args.get('msg')
    return render_template('admin_wiki_category.html', cats=cats, msg=msg)


@wiki_bp.route('/admin/edit_wiki_category/<int:cat_id>', methods=['POST'])
def edit_wiki_category(cat_id):
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    new_cat      = request.form['new_category'].strip()
    img_file     = request.files.get('new_cat_img')
    img_filename = None
    if img_file and img_file.filename:
        filename     = secure_filename(img_file.filename)
        wiki_folder  = current_app.config['WIKI_CAT_FOLDER']
        img_file.save(os.path.join(wiki_folder, filename))
        img_filename = filename
    db.update_wiki_category(cat_id, new_cat, img_filename)
    flash(f'Category updated to "{new_cat}"', 'success')
    return redirect(url_for('wiki.admin_wiki_categories'))


@wiki_bp.route('/admin/delete_wiki_category/<int:cat_id>')
def delete_wiki_category(cat_id):
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))
    db.delete_wiki_category(cat_id)
    flash('Wiki category deleted', 'success')
    return redirect(url_for('wiki.admin_wiki_categories'))


# ── Admin: Wiki Pages ─────────────────────────────────────────────────────────

@wiki_bp.route('/admin/add_wiki', methods=['GET', 'POST'])
def add_wiki():
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        category_id = request.form['category_id']
        title       = request.form['title'].strip()
        descr       = request.form['descr']
        db.add_wiki_page(category_id, title, descr)
        flash(f'Wiki "{title}" added.', 'success')
        return redirect(url_for('wiki.view_wikis'))

    categories = db.get_wiki_categories()
    return render_template('add_wiki.html', categories=categories)


@wiki_bp.route('/admin/view_wikis')
def view_wikis():
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))
    wikis = db.get_wiki_pages()
    return render_template('view_wikis.html', wikis=wikis)


@wiki_bp.route('/admin/edit_wiki/<int:wiki_id>', methods=['GET', 'POST'])
def edit_wiki(wiki_id):
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    page = db.get_wiki_page(wiki_id)
    if not page:
        flash('Wiki not found.', 'error')
        return redirect(url_for('wiki.view_wikis'))

    if request.method == 'POST':
        category_id = request.form['category_id']
        title       = request.form['title'].strip()
        descr       = request.form['descr']
        db.update_wiki_page(wiki_id, category_id, title, descr)
        flash(f'Wiki "{title}" updated.', 'success')
        return redirect(url_for('wiki.view_wikis'))

    categories = db.get_wiki_categories()
    return render_template('edit_wiki.html', page=page, categories=categories)


@wiki_bp.route('/admin/delete_wiki/<int:wiki_id>')
def delete_wiki(wiki_id):
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))
    db.soft_delete_wiki_page(wiki_id)
    flash('Wiki deleted', 'success')
    return redirect(url_for('wiki.view_wikis'))


# ── Admin: Wiki Views ─────────────────────────────────────────────────────────

@wiki_bp.route('/admin/wiki_views')
def admin_wiki_views():
    if 'user_id' not in session or session['emp_type'] != 'admin':
        return redirect(url_for('auth.login'))

    start  = request.args.get('start_date', default=None)
    end    = request.args.get('end_date',   default=None)
    wiki   = request.args.get('wiki_id',    type=int)

    counts = db.get_wiki_view_counts(start, end)
    views  = db.get_wiki_views_filtered(start, end, wiki)
    pages  = db.get_wiki_pages()

    return render_template('view_wiki_views.html',
                           counts=counts,
                           views=views,
                           pages=pages,
                           filter_start=start,
                           filter_end=end,
                           filter_wiki=wiki)


# ── Employee: Wiki ────────────────────────────────────────────────────────────

@wiki_bp.route('/employee/wiki')
def employee_wiki_list():
    if 'user_id' not in session or session['emp_type'] != 'emp':
        return redirect(url_for('auth.login'))
    wikis = db.get_wiki_pages()
    return render_template('wiki_list.html', wikis=wikis)


@wiki_bp.route('/employee/wiki/<int:wiki_id>')
def wiki_detail(wiki_id):
    if 'user_id' not in session or session['emp_type'] != 'emp':
        return redirect(url_for('auth.login'))

    page = db.get_wiki_page(wiki_id)
    if not page:
        flash('Wiki not found.', 'error')
        return redirect(url_for('wiki.employee_wiki_list'))

    db.add_wiki_view(wiki_id, session['user_id'])
    return render_template('wiki_detail.html', page=page)
