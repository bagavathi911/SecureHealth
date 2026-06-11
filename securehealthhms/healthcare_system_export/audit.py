"""
Audit logging - records every action for HIPAA compliance
"""

from datetime import datetime
from flask import g, current_app
import sqlite3


def log_action(username, role, action, resource, ip_address, status):
    """Log every action to the audit_logs table."""
    try:
        db = g.get('db')
        if db is None:
            db = sqlite3.connect(current_app.config['DATABASE'])
            db.row_factory = sqlite3.Row
            own_conn = True
        else:
            own_conn = False

        db.execute(
            '''INSERT INTO audit_logs (username, role, action, resource, ip_address, status, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                username or 'anonymous',
                role or 'unknown',
                action,
                resource,
                ip_address,
                status,
                datetime.now().isoformat(timespec='seconds')
            )
        )
        db.commit()

        if own_conn:
            db.close()
    except Exception as e:
        # Never let audit logging break the application
        print(f"[AUDIT ERROR] {e}")
