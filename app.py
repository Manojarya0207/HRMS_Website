import os
import logging
from datetime import datetime, date
import pytz

from flask import Flask

from routes.extensions import UPLOAD_FOLDER, INVOICE_FOLDER, WIKI_CAT_FOLDER

# ── App factory ───────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# ── Folder config ─────────────────────────────────────────────────────────────

app.config['UPLOAD_FOLDER']   = UPLOAD_FOLDER
app.config['INVOICE_FOLDER']  = INVOICE_FOLDER
app.config['WIKI_CAT_FOLDER'] = WIKI_CAT_FOLDER

for folder in (UPLOAD_FOLDER, INVOICE_FOLDER, WIKI_CAT_FOLDER):
    os.makedirs(folder, exist_ok=True)

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.DEBUG)

# ── Template filters ──────────────────────────────────────────────────────────

@app.template_filter('todate')
def todate(value):
    """Jinja2 filter: convert datetime-string or datetime to its date."""
    if not value:
        return ''
    if isinstance(value, datetime):
        return value.date()
    s = str(value).strip()
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.strptime(s[:10], '%Y-%m-%d').date()
    except Exception:
        return s

@app.template_filter('istime')
def istime(value):
    """Jinja2 filter: convert UTC datetime-string to IST time."""
    if not value:
        return ''
    # If it's already a datetime object, assume it's UTC
    if isinstance(value, datetime):
        utc_dt = value
    else:
        s = str(value).strip()
        # Try parsing with microseconds
        try:
            utc_dt = datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            try:
                utc_dt = datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # If parsing fails, return original
                return s
    # Assume UTC and convert to IST
    utc_zone = pytz.UTC
    ist_zone = pytz.timezone('Asia/Kolkata')
    utc_dt = utc_zone.localize(utc_dt) if utc_dt.tzinfo is None else utc_dt
    ist_dt = utc_dt.astimezone(ist_zone)
    # Format as time only or datetime? We'll show date and time
    return ist_dt.strftime('%Y-%m-%d %I:%M:%S %p')

# ── Register Blueprints ───────────────────────────────────────────────────────

from routes.auth      import auth_bp
from routes.employees import employees_bp
from routes.projects  import projects_bp
from routes.tasks     import tasks_bp
from routes.leave     import leave_bp
from routes.expenses  import expenses_bp
from routes.assets    import assets_bp
from routes.careers   import careers_bp
from routes.wiki      import wiki_bp

app.register_blueprint(auth_bp)
app.register_blueprint(employees_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(leave_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(assets_bp)
app.register_blueprint(careers_bp)
app.register_blueprint(wiki_bp)

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)