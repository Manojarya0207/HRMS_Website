"""
Shared state imported by all blueprints.
Import `db` and `get_db_connection` from here to avoid circular imports.
"""
import sqlite3
from database import Database

# Single Database instance shared across the app
db = Database()

# Folder constants (kept here so blueprints don't hard-code paths)
UPLOAD_FOLDER  = 'static/bngImg'
INVOICE_FOLDER = 'static/invoices'
WIKI_CAT_FOLDER = 'static/wikiCatImg'


def get_db_connection():
    """Return a raw sqlite3 connection with Row factory (for legacy queries)."""
    conn = sqlite3.connect('project_tracking.db')
    conn.row_factory = sqlite3.Row
    return conn
