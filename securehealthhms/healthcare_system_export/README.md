# SecureHealth HMS

A secure, HIPAA-inspired Healthcare Management System built with Python Flask.

> **All patient data is entirely synthetic and fictional. For demonstration purposes only.**

## Quick Start

```bash
pip install -r requirements.txt
python run.py
```

Then open http://127.0.0.1:5000

## Demo Credentials

| Role   | Username  | Password     |
|--------|-----------|--------------|
| Admin  | admin     | Admin@1234!  |
| Doctor | dr.mehta  | Doctor@1234! |
| Doctor | dr.iyer   | Doctor@1234! |
| Doctor | dr.pillai | Doctor@1234! |
| Nurse  | nurse01   | Nurse@1234!  |

## Features

- **AES-256 Encryption** — Diagnosis, Treatment, Prescriptions, Address encrypted at rest
- **bcrypt Hashing** — Passwords hashed with cost factor 12
- **RBAC** — Admin / Doctor / Nurse access tiers
- **Full Audit Trail** — Every action logged with timestamp & IP
- **Dark Mode** — Toggle in sidebar
- **CSV Export** — Export audit logs
- **Charts** — Login analytics, role distribution, action stats
- **50 Synthetic Patients** — Realistic fictional data

## Security Stack

| Feature            | Implementation              |
|--------------------|-----------------------------|
| Encryption         | AES-256-CBC (PyCryptodome)  |
| Password Hashing   | bcrypt (rounds=12)          |
| Session Security   | Flask sessions, HttpOnly    |
| SQL Injection      | Parameterized queries       |
| XSS Protection     | Input sanitization + CSP    |
| Security Headers   | X-Frame-Options, CSP, etc.  |
| Audit Logging      | SQLite, every action logged |

## Tech Stack

Python 3.10+ · Flask · SQLite · Bootstrap 5 · Chart.js · PyCryptodome · bcrypt
