"""Central configuration for the HRMS application.

All filesystem paths are anchored to the project root (BASE_DIR) so the
application behaves identically regardless of the current working directory.
"""
import os

# Project root (one level above the app/ package)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Flask
SECRET_KEY = 'your-secret-key-change-this-in-production'

# Template / static locations (kept at project root)
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# SQLite database
DB_PATH = os.path.join(BASE_DIR, 'project_tracking.db')

# Upload folders
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'bngImg')
INVOICE_FOLDER = os.path.join(BASE_DIR, 'static', 'invoices')
WIKI_CAT_FOLDER = os.path.join(BASE_DIR, 'static', 'wikiCatImg')

# Excel template used for expense reports
EXPENSE_TEMPLATE_PATH = os.path.join(BASE_DIR, 'Expense-Details.xlsx')
