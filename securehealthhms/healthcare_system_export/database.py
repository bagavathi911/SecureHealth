"""
Database initialization and connection management
"""

import sqlite3
import os
from flask import g, current_app


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA journal_mode=WAL')
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db


def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL UNIQUE,
            password_hash BLOB    NOT NULL,
            role          TEXT    NOT NULL CHECK(role IN ('admin','doctor','nurse')),
            created_at    TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS patients (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id              TEXT NOT NULL UNIQUE,
            encrypted_name          TEXT NOT NULL,
            encrypted_address       TEXT,
            encrypted_diagnosis     TEXT,
            encrypted_treatment     TEXT,
            encrypted_prescriptions TEXT,
            age                     INTEGER,
            gender                  TEXT,
            blood_group             TEXT,
            contact                 TEXT,
            last_visit              TEXT,
            assigned_doctor         TEXT,
            assigned_nurse          TEXT,
            created_at              TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT,
            role       TEXT,
            action     TEXT    NOT NULL,
            resource   TEXT,
            ip_address TEXT,
            status     TEXT    NOT NULL,
            timestamp  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_audit_username  ON audit_logs(username);
        CREATE INDEX IF NOT EXISTS idx_audit_action    ON audit_logs(action);
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_patients_doctor ON patients(assigned_doctor);
        CREATE INDEX IF NOT EXISTS idx_patients_nurse  ON patients(assigned_nurse);
    ''')
    db.commit()
