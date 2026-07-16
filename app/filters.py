"""Jinja2 template filters and context processors (moved verbatim from app.py)."""
from datetime import datetime, timedelta

from flask import get_flashed_messages


def format_ist(dt_val):
    if not dt_val:
        return ""
    if isinstance(dt_val, str):
        try:
            dt = datetime.strptime(dt_val, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                dt = datetime.strptime(dt_val, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                return dt_val
    elif isinstance(dt_val, datetime):
        dt = dt_val
    else:
        return str(dt_val)

    ist_dt = dt + timedelta(hours=5, minutes=30)
    return ist_dt.strftime("%Y-%m-%d | %I:%M:%S %p")


def override_flash():
    already_called = {}
    original_get_flashed_messages = get_flashed_messages

    def custom_get_flashed_messages(*args, **kwargs):
        if already_called.get('called', False):
            return []
        already_called['called'] = True
        return original_get_flashed_messages(*args, **kwargs)

    return dict(get_flashed_messages=custom_get_flashed_messages)


def todate(value):
    """
    Jinja2 filter: given a datetime-string or datetime, return its date.
    Handles both 'YYYY-MM-DD HH:MM:SS' and 'YYYY-MM-DD'.
    """
    if not value:
        return ''
    # If it's already a datetime
    if isinstance(value, datetime):
        return value.date()

    s = str(value).strip()
    # Try full-timestamp first
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    # Fallback: just take first 10 chars as date
    try:
        return datetime.strptime(s[:10], '%Y-%m-%d').date()
    except Exception:
        return s  # give up, return raw


def is_editable(inserted_date_val):
    if not inserted_date_val:
        return False
    if isinstance(inserted_date_val, str):
        try:
            dt = datetime.strptime(inserted_date_val, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                dt = datetime.strptime(inserted_date_val, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                return False
    elif isinstance(inserted_date_val, datetime):
        dt = inserted_date_val
    else:
        return False

    # Check if task was submitted on the same calendar date (IST) as today
    task_ist_date = (dt + timedelta(hours=5, minutes=30)).date()
    current_ist_date = (datetime.utcnow() + timedelta(hours=5, minutes=30)).date()
    return task_ist_date == current_ist_date


def time_remaining_for_edit(inserted_date_val):
    if not is_editable(inserted_date_val):
        return "Expired"
    return "Editable Today Only"


def register_filters(app):
    """Attach all template filters and context processors to the app."""
    app.add_template_filter(format_ist, 'format_ist')
    app.add_template_filter(todate, 'todate')
    app.add_template_filter(is_editable, 'is_editable')
    app.add_template_filter(time_remaining_for_edit, 'time_remaining_for_edit')
    app.context_processor(override_flash)
