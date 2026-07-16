"""Shared application singletons.

The Database instance and the raw sqlite3 connection helper live here so
that route modules can import them without circular imports.
"""
import sqlite3

from app.config import DB_PATH
from app.models import Database

# Single shared Database instance (created once at import time)
db = Database(DB_PATH)


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

