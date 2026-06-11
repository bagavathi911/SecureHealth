"""
SecureHealth HMS - Healthcare Management System
Demonstrates HIPAA-inspired security practices with synthetic data only
"""

import os
import sqlite3
import csv
import io
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, make_response, g
)
import bcrypt

from encryption import encrypt_field, decrypt_field
from database import init_db, get_db
from audit import log_action
from sample_data import generate_sample_data

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['DATABASE'] = os.path.join(app.instance_path, 'healthcare.db')
os.makedirs(app.instance_path, exist_ok=True)

# ─── Security Headers ────────────────────────────────────────────────────────

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data:;"
    )
    return response

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ─── Auth Decorators ─────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            log_action(None, None, 'UNAUTHORIZED_ACCESS', request.path, request.remote_addr, 'DENIED')
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                log_action(
                    session.get('username'), session.get('role'),
                    'UNAUTHORIZED_ACCESS', request.path,
                    request.remote_addr, 'DENIED'
                )
                flash('Access denied. Insufficient privileges.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator

def validate_password(password):
    """Password complexity validation"""
    errors = []
    if len(password) < 8:
        errors.append("At least 8 characters")
    if not any(c.isupper() for c in password):
        errors.append("At least one uppercase letter")
    if not any(c.islower() for c in password):
        errors.append("At least one lowercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("At least one number")
    return errors

# ─── Auth Routes ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        ip = request.remote_addr

        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('login.html')

        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user and bcrypt.checkpw(password.encode(), user['password_hash']):
            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            log_action(username, user['role'], 'LOGIN', 'auth', ip, 'SUCCESS')
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            log_action(username, 'unknown', 'LOGIN_FAILED', 'auth', ip, 'FAILED')
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    log_action(session.get('username'), session.get('role'), 'LOGOUT', 'auth', request.remote_addr, 'SUCCESS')
    session.clear()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('login'))

# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    role = session['role']
    stats = {}

    if role == 'admin':
        stats['total_users'] = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        stats['total_patients'] = db.execute('SELECT COUNT(*) FROM patients').fetchone()[0]
        stats['login_success'] = db.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE action='LOGIN' AND status='SUCCESS'"
        ).fetchone()[0]
        stats['login_failed'] = db.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE action='LOGIN_FAILED'"
        ).fetchone()[0]
        stats['recent_activities'] = db.execute(
            'SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 10'
        ).fetchall()
        stats['role_counts'] = db.execute(
            'SELECT role, COUNT(*) as count FROM users GROUP BY role'
        ).fetchall()
        stats['daily_logins'] = db.execute(
            """SELECT DATE(timestamp) as day, COUNT(*) as count 
               FROM audit_logs WHERE action='LOGIN' AND status='SUCCESS'
               AND timestamp >= datetime('now', '-7 days')
               GROUP BY DATE(timestamp) ORDER BY day"""
        ).fetchall()

    elif role == 'doctor':
        stats['my_patients'] = db.execute(
            'SELECT COUNT(*) FROM patients WHERE assigned_doctor = ?',
            (session['username'],)
        ).fetchone()[0]
        stats['recent_patients'] = db.execute(
            'SELECT id, patient_id, encrypted_name, age, gender, blood_group, last_visit FROM patients WHERE assigned_doctor = ? ORDER BY last_visit DESC LIMIT 5',
            (session['username'],)
        ).fetchall()
        stats['recent_patients'] = [
            dict(p, encrypted_name=decrypt_field(p['encrypted_name']))
            for p in stats['recent_patients']
        ]

    elif role == 'nurse':
        stats['my_patients'] = db.execute(
            'SELECT COUNT(*) FROM patients WHERE assigned_nurse = ?',
            (session['username'],)
        ).fetchone()[0]
        stats['recent_vitals'] = db.execute(
            """SELECT p.id, p.patient_id, p.encrypted_name, p.age, p.gender, p.blood_group, p.last_visit
               FROM patients p WHERE p.assigned_nurse = ?
               ORDER BY p.last_visit DESC LIMIT 5""",
            (session['username'],)
        ).fetchall()
        stats['recent_vitals'] = [
            dict(p, encrypted_name=decrypt_field(p['encrypted_name']))
            for p in stats['recent_vitals']
        ]

    return render_template('dashboard.html', stats=stats, role=role)

# ─── Patient Management ───────────────────────────────────────────────────────

@app.route('/patients')
@login_required
def patients():
    db = get_db()
    role = session['role']
    search = request.args.get('search', '').strip()

    if role == 'admin':
        query = 'SELECT * FROM patients ORDER BY id DESC'
        rows = db.execute(query).fetchall()
    elif role == 'doctor':
        rows = db.execute(
            'SELECT * FROM patients WHERE assigned_doctor = ? ORDER BY last_visit DESC',
            (session['username'],)
        ).fetchall()
    elif role == 'nurse':
        rows = db.execute(
            'SELECT * FROM patients WHERE assigned_nurse = ? ORDER BY last_visit DESC',
            (session['username'],)
        ).fetchall()
    else:
        rows = []

    patient_list = []
    for p in rows:
        name = decrypt_field(p['encrypted_name'])
        if search and search.lower() not in name.lower() and search.lower() not in p['patient_id'].lower():
            continue
        patient_list.append({
            'id': p['id'],
            'patient_id': p['patient_id'],
            'name': name,
            'age': p['age'],
            'gender': p['gender'],
            'blood_group': p['blood_group'],
            'last_visit': p['last_visit'],
            'assigned_doctor': p['assigned_doctor'],
        })

    log_action(session['username'], role, 'VIEW_PATIENTS_LIST', 'patients', request.remote_addr, 'SUCCESS')
    return render_template('patients.html', patients=patient_list, search=search)

@app.route('/patients/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'doctor')
def new_patient():
    db = get_db()
    doctors = db.execute("SELECT username FROM users WHERE role='doctor'").fetchall()

    if request.method == 'POST':
        import re
        name = request.form.get('name', '').strip()
        age = request.form.get('age', '')
        gender = request.form.get('gender', '')
        blood_group = request.form.get('blood_group', '')
        contact = request.form.get('contact', '').strip()
        address = request.form.get('address', '').strip()
        diagnosis = request.form.get('diagnosis', '').strip()
        treatment = request.form.get('treatment', '').strip()
        prescriptions = request.form.get('prescriptions', '').strip()
        last_visit = request.form.get('last_visit', '')
        assigned_doctor = request.form.get('assigned_doctor', session['username'])
        assigned_nurse = request.form.get('assigned_nurse', '')

        if not all([name, age, gender, blood_group]):
            flash('Required fields are missing.', 'danger')
            return render_template('patient_form.html', doctors=doctors)

        # XSS prevention - sanitize inputs
        name = re.sub(r'[<>"\']', '', name)
        address = re.sub(r'[<>"\']', '', address)

        import random, string
        patient_id = 'PID-' + ''.join(random.choices(string.digits, k=8))

        db.execute(
            '''INSERT INTO patients
               (patient_id, encrypted_name, encrypted_address, encrypted_diagnosis,
                encrypted_treatment, encrypted_prescriptions,
                age, gender, blood_group, contact, last_visit, assigned_doctor, assigned_nurse)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (
                patient_id,
                encrypt_field(name),
                encrypt_field(address),
                encrypt_field(diagnosis),
                encrypt_field(treatment),
                encrypt_field(prescriptions),
                int(age), gender, blood_group, contact,
                last_visit, assigned_doctor, assigned_nurse
            )
        )
        db.commit()
        log_action(session['username'], session['role'], 'CREATE_PATIENT', f'patient:{patient_id}', request.remote_addr, 'SUCCESS')
        flash(f'Patient {patient_id} created successfully.', 'success')
        return redirect(url_for('patients'))

    nurses = db.execute("SELECT username FROM users WHERE role='nurse'").fetchall()
    return render_template('patient_form.html', doctors=doctors, nurses=nurses, mode='create')

@app.route('/patients/<int:pid>')
@login_required
def view_patient(pid):
    db = get_db()
    role = session['role']
    p = db.execute('SELECT * FROM patients WHERE id = ?', (pid,)).fetchone()

    if not p:
        flash('Patient not found.', 'danger')
        return redirect(url_for('patients'))

    # Access control
    if role == 'doctor' and p['assigned_doctor'] != session['username']:
        log_action(session['username'], role, 'UNAUTHORIZED_PATIENT_ACCESS', f'patient:{pid}', request.remote_addr, 'DENIED')
        flash('Access denied to this patient record.', 'danger')
        return redirect(url_for('patients'))

    if role == 'nurse' and p['assigned_nurse'] != session['username']:
        log_action(session['username'], role, 'UNAUTHORIZED_PATIENT_ACCESS', f'patient:{pid}', request.remote_addr, 'DENIED')
        flash('Access denied to this patient record.', 'danger')
        return redirect(url_for('patients'))

    patient = dict(p)
    patient['name'] = decrypt_field(p['encrypted_name'])
    patient['address'] = decrypt_field(p['encrypted_address']) if role in ['admin', 'doctor'] else '*** RESTRICTED ***'
    patient['diagnosis'] = decrypt_field(p['encrypted_diagnosis']) if role in ['admin', 'doctor'] else '*** RESTRICTED ***'
    patient['treatment'] = decrypt_field(p['encrypted_treatment']) if role in ['admin', 'doctor'] else '*** RESTRICTED ***'
    patient['prescriptions'] = decrypt_field(p['encrypted_prescriptions']) if role in ['admin', 'doctor'] else '*** RESTRICTED ***'

    log_action(session['username'], role, 'VIEW_PATIENT', f'patient:{p["patient_id"]}', request.remote_addr, 'SUCCESS')
    return render_template('patient_detail.html', patient=patient)

@app.route('/patients/<int:pid>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'doctor')
def edit_patient(pid):
    import re
    db = get_db()
    p = db.execute('SELECT * FROM patients WHERE id = ?', (pid,)).fetchone()

    if not p:
        flash('Patient not found.', 'danger')
        return redirect(url_for('patients'))

    if session['role'] == 'doctor' and p['assigned_doctor'] != session['username']:
        flash('Access denied.', 'danger')
        return redirect(url_for('patients'))

    if request.method == 'POST':
        diagnosis = re.sub(r'[<>]', '', request.form.get('diagnosis', ''))
        treatment = re.sub(r'[<>]', '', request.form.get('treatment', ''))
        prescriptions = re.sub(r'[<>]', '', request.form.get('prescriptions', ''))
        last_visit = request.form.get('last_visit', '')

        db.execute(
            '''UPDATE patients SET encrypted_diagnosis=?, encrypted_treatment=?,
               encrypted_prescriptions=?, last_visit=? WHERE id=?''',
            (encrypt_field(diagnosis), encrypt_field(treatment), encrypt_field(prescriptions), last_visit, pid)
        )
        db.commit()
        log_action(session['username'], session['role'], 'UPDATE_PATIENT', f'patient:{p["patient_id"]}', request.remote_addr, 'SUCCESS')
        flash('Patient record updated successfully.', 'success')
        return redirect(url_for('view_patient', pid=pid))

    patient = dict(p)
    patient['name'] = decrypt_field(p['encrypted_name'])
    patient['diagnosis'] = decrypt_field(p['encrypted_diagnosis'])
    patient['treatment'] = decrypt_field(p['encrypted_treatment'])
    patient['prescriptions'] = decrypt_field(p['encrypted_prescriptions'])

    doctors = db.execute("SELECT username FROM users WHERE role='doctor'").fetchall()
    nurses = db.execute("SELECT username FROM users WHERE role='nurse'").fetchall()
    return render_template('patient_form.html', patient=patient, doctors=doctors, nurses=nurses, mode='edit')

@app.route('/patients/<int:pid>/vitals', methods=['POST'])
@login_required
@role_required('nurse', 'admin')
def update_vitals(pid):
    db = get_db()
    p = db.execute('SELECT * FROM patients WHERE id = ?', (pid,)).fetchone()

    if not p:
        return jsonify({'error': 'Not found'}), 404

    if session['role'] == 'nurse' and p['assigned_nurse'] != session['username']:
        log_action(session['username'], 'nurse', 'UNAUTHORIZED_VITALS_UPDATE', f'patient:{pid}', request.remote_addr, 'DENIED')
        return jsonify({'error': 'Access denied'}), 403

    last_visit = request.form.get('last_visit', datetime.now().strftime('%Y-%m-%d'))
    db.execute('UPDATE patients SET last_visit=? WHERE id=?', (last_visit, pid))
    db.commit()
    log_action(session['username'], session['role'], 'UPDATE_VITALS', f'patient:{p["patient_id"]}', request.remote_addr, 'SUCCESS')
    flash('Vitals updated successfully.', 'success')
    return redirect(url_for('view_patient', pid=pid))

# ─── User Management ──────────────────────────────────────────────────────────

@app.route('/users')
@login_required
@role_required('admin')
def users():
    db = get_db()
    all_users = db.execute('SELECT id, username, role, created_at FROM users ORDER BY created_at DESC').fetchall()
    log_action(session['username'], 'admin', 'VIEW_USERS', 'users', request.remote_addr, 'SUCCESS')
    return render_template('users.html', users=all_users)

@app.route('/users/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def new_user():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', '')

        if not all([username, password, role]):
            flash('All fields are required.', 'danger')
            return render_template('user_form.html')

        errors = validate_password(password)
        if errors:
            flash('Password requirements: ' + ', '.join(errors), 'danger')
            return render_template('user_form.html')

        db = get_db()
        existing = db.execute('SELECT id FROM users WHERE username=?', (username,)).fetchone()
        if existing:
            flash('Username already exists.', 'danger')
            return render_template('user_form.html')

        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
        db.execute(
            'INSERT INTO users (username, password_hash, role, created_at) VALUES (?,?,?,?)',
            (username, pw_hash, role, datetime.now().isoformat())
        )
        db.commit()
        log_action(session['username'], 'admin', 'CREATE_USER', f'user:{username}', request.remote_addr, 'SUCCESS')
        flash(f'User {username} created successfully.', 'success')
        return redirect(url_for('users'))

    return render_template('user_form.html', mode='create')

@app.route('/users/<int:uid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(uid):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('users'))
    if user['id'] == session['user_id']:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('users'))
    db.execute('DELETE FROM users WHERE id=?', (uid,))
    db.commit()
    log_action(session['username'], 'admin', 'DELETE_USER', f'user:{user["username"]}', request.remote_addr, 'SUCCESS')
    flash(f'User {user["username"]} deleted.', 'success')
    return redirect(url_for('users'))

# ─── Audit Logs ───────────────────────────────────────────────────────────────

@app.route('/audit')
@login_required
@role_required('admin')
def audit_logs():
    db = get_db()
    page = int(request.args.get('page', 1))
    per_page = 25
    offset = (page - 1) * per_page
    action_filter = request.args.get('action', '')
    status_filter = request.args.get('status', '')

    query = 'SELECT * FROM audit_logs WHERE 1=1'
    params = []
    if action_filter:
        query += ' AND action = ?'
        params.append(action_filter)
    if status_filter:
        query += ' AND status = ?'
        params.append(status_filter)

    total = db.execute(query.replace('SELECT *', 'SELECT COUNT(*)'), params).fetchone()[0]
    logs = db.execute(query + f' ORDER BY timestamp DESC LIMIT {per_page} OFFSET {offset}', params).fetchall()
    actions = db.execute('SELECT DISTINCT action FROM audit_logs').fetchall()

    log_action(session['username'], 'admin', 'VIEW_AUDIT_LOGS', 'audit', request.remote_addr, 'SUCCESS')
    return render_template('audit.html',
        logs=logs, page=page,
        total_pages=(total + per_page - 1) // per_page,
        actions=actions, action_filter=action_filter,
        status_filter=status_filter, total=total
    )

@app.route('/audit/export')
@login_required
@role_required('admin')
def export_audit():
    db = get_db()
    logs = db.execute('SELECT * FROM audit_logs ORDER BY timestamp DESC').fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Username', 'Role', 'Action', 'Resource', 'IP Address', 'Status', 'Timestamp'])
    for log in logs:
        writer.writerow([log['id'], log['username'], log['role'], log['action'],
                         log['resource'], log['ip_address'], log['status'], log['timestamp']])
    log_action(session['username'], 'admin', 'EXPORT_AUDIT_LOGS', 'audit', request.remote_addr, 'SUCCESS')
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=audit_logs.csv'
    return response

# ─── API Endpoints (for charts) ───────────────────────────────────────────────

@app.route('/api/stats/logins')
@login_required
@role_required('admin')
def api_login_stats():
    db = get_db()
    data = db.execute(
        """SELECT DATE(timestamp) as day, 
           SUM(CASE WHEN status='SUCCESS' THEN 1 ELSE 0 END) as success,
           SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END) as failed
           FROM audit_logs WHERE action IN ('LOGIN','LOGIN_FAILED')
           AND timestamp >= datetime('now', '-14 days')
           GROUP BY DATE(timestamp) ORDER BY day"""
    ).fetchall()
    return jsonify([dict(row) for row in data])

@app.route('/api/stats/roles')
@login_required
@role_required('admin')
def api_role_stats():
    db = get_db()
    data = db.execute('SELECT role, COUNT(*) as count FROM users GROUP BY role').fetchall()
    return jsonify([dict(row) for row in data])

@app.route('/api/stats/actions')
@login_required
@role_required('admin')
def api_action_stats():
    db = get_db()
    data = db.execute(
        'SELECT action, COUNT(*) as count FROM audit_logs GROUP BY action ORDER BY count DESC LIMIT 8'
    ).fetchall()
    return jsonify([dict(row) for row in data])

# ─── Init & Run ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        init_db()
        generate_sample_data()
    app.run(debug=False, host='0.0.0.0', port=5000)
