"""
Synthetic sample data generator.
All patient data is ENTIRELY FICTIONAL for demonstration purposes only.
"""

import random
import string
from datetime import datetime, timedelta
import bcrypt
from database import get_db
from encryption import encrypt_field


FIRST_NAMES = [
    'Aarav','Priya','Rohan','Sneha','Vikram','Kavitha','Arjun','Meera',
    'Kiran','Divya','Suresh','Lakshmi','Rahul','Anita','Sanjay','Pooja',
    'Ravi','Uma','Arun','Nisha','Deepak','Rekha','Mohan','Swati','Raj',
    'Sunita','Nikhil','Geeta','Amit','Radha','Vijay','Saranya','Ganesh',
    'Hema','Rajesh','Padma','Krishna','Shanti','Venkat','Jyothi'
]
LAST_NAMES = [
    'Kumar','Sharma','Patel','Singh','Reddy','Iyer','Nair','Pillai',
    'Menon','Rao','Verma','Gupta','Joshi','Mehta','Shah','Agarwal',
    'Mishra','Pandey','Sinha','Das','Bose','Chatterjee','Mukherjee',
    'Bhatt','Trivedi','Desai','Malhotra','Kapoor','Chopra','Khanna'
]
BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
GENDERS = ['Male', 'Female']
CITIES = ['Chennai', 'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Pune', 'Kolkata', 'Ahmedabad']
STREETS = ['MG Road', 'Park Street', 'Anna Salai', 'Brigade Road', 'Linking Road', 'FC Road']

DIAGNOSES = [
    'Type 2 Diabetes Mellitus - stable, HbA1c 7.2%',
    'Essential Hypertension - BP controlled at 130/85',
    'Seasonal Allergic Rhinitis - moderate severity',
    'Chronic Lower Back Pain - lumbar disc herniation L4-L5',
    'Mild Persistent Asthma - FEV1 78% predicted',
    'Hypothyroidism - TSH 4.8 mIU/L on thyroxine therapy',
    'Iron Deficiency Anemia - Hb 9.8 g/dL',
    'Gastroesophageal Reflux Disease (GERD) - erosive',
    'Anxiety Disorder - generalized, mild-moderate',
    'Migraine with Aura - episodic, 4-5 per month',
    'Osteoarthritis - bilateral knee, Grade II',
    'Chronic Kidney Disease - Stage 2, eGFR 72',
    'Hyperlipidemia - LDL 148 mg/dL, on statin therapy',
    'Vitamin D Deficiency - 18 ng/mL',
    'Rheumatoid Arthritis - early, seropositive',
]
TREATMENTS = [
    'Dietary modifications, regular aerobic exercise 30 min/day, blood glucose monitoring',
    'Low-sodium diet, daily BP monitoring, lifestyle modifications, stress reduction',
    'Allergen avoidance, nasal saline irrigation, antihistamines as needed',
    'Physiotherapy 3x/week, core strengthening exercises, ergonomic assessment',
    'Metered-dose inhaler technique review, peak flow monitoring, trigger avoidance',
    'Continue thyroxine, annual thyroid function tests, monitor symptoms',
    'Iron-rich diet, oral iron supplementation, repeat CBC in 8 weeks',
    'Head elevation, small frequent meals, avoid spicy/fatty foods, antacids',
    'Cognitive behavioral therapy, mindfulness exercises, sleep hygiene',
    'Trigger diary, prophylactic therapy, abortive medications, regular sleep schedule',
    'Weight management, physical therapy, knee bracing, activity modification',
    'Fluid restriction 1.5L/day, protein diet 0.8g/kg, nephrology follow-up',
    'Mediterranean diet, statins, omega-3 supplementation, quarterly lipid panel',
    'Vitamin D3 60,000 IU weekly x 8 weeks then monthly maintenance',
    'Disease-modifying antirheumatic drugs, rheumatology referral, joint protection',
]
PRESCRIPTIONS = [
    'Metformin 500mg BD, Glimepiride 1mg OD with breakfast',
    'Amlodipine 5mg OD, Losartan 50mg OD, Hydrochlorothiazide 12.5mg OD',
    'Loratadine 10mg OD, Fluticasone nasal spray 2 puffs each nostril BD',
    'Ibuprofen 400mg TDS with food, Pantoprazole 40mg OD, Methocarbamol 750mg TDS',
    'Salbutamol MDI 2 puffs PRN, Budesonide 200mcg BD, Montelukast 10mg OD',
    'Levothyroxine 75mcg OD empty stomach, Calcium 500mg BD',
    'Ferrous sulfate 325mg BD, Vitamin C 500mg BD, Folic acid 5mg OD',
    'Pantoprazole 40mg OD before breakfast, Domperidone 10mg TDS before meals',
    'Escitalopram 10mg OD, Clonazepam 0.5mg SOS, Vitamin B12 1500mcg OD',
    'Sumatriptan 50mg PRN, Propranolol 40mg BD (prophylaxis), Naproxen 500mg PRN',
    'Diclofenac gel topical BD, Calcium + Vitamin D3 supplement, Glucosamine 1500mg OD',
    'Folic acid 5mg OD, Multivitamin OD, Avoid NSAIDs - use Paracetamol 500mg PRN',
    'Atorvastatin 20mg OD at night, Ezetimibe 10mg OD, Aspirin 75mg OD',
    'Cholecalciferol 60,000 IU weekly, Calcium carbonate 500mg BD',
    'Hydroxychloroquine 200mg BD, Methotrexate 7.5mg weekly, Folic acid 5mg (6 days/week)',
]


def random_name():
    return random.choice(FIRST_NAMES) + ' ' + random.choice(LAST_NAMES)

def random_phone():
    return '9' + ''.join(random.choices(string.digits, k=9))

def random_address():
    return f'{random.randint(1,999)}, {random.choice(STREETS)}, {random.choice(CITIES)}'

def random_date(days_back=365):
    delta = timedelta(days=random.randint(0, days_back))
    return (datetime.now() - delta).strftime('%Y-%m-%d')

def random_patient_id():
    return 'PID-' + ''.join(random.choices(string.digits, k=8))


def generate_sample_data():
    db = get_db()
    existing = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    if existing > 0:
        return  # Already seeded

    print("Generating synthetic sample data...")

    # ── Accounts ──────────────────────────────────────────────────────────────
    accounts = [
        ('admin',         'Admin@1234!',   'admin'),
        ('dr.mehta',      'Doctor@1234!',  'doctor'),
        ('dr.iyer',       'Doctor@1234!',  'doctor'),
        ('dr.pillai',     'Doctor@1234!',  'doctor'),
    ]
    for i in range(1, 11):
        accounts.append((f'nurse{i:02d}', 'Nurse@1234!', 'nurse'))

    usernames_by_role = {'doctor': [], 'nurse': []}
    for uname, pwd, role in accounts:
        pw_hash = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt(rounds=12))
        db.execute(
            'INSERT INTO users (username, password_hash, role, created_at) VALUES (?,?,?,?)',
            (uname, pw_hash, role, datetime.now().isoformat())
        )
        if role in usernames_by_role:
            usernames_by_role[role].append(uname)

    db.commit()
    print(f"  Created {len(accounts)} user accounts")

    # ── 50 Synthetic Patients ─────────────────────────────────────────────────
    doctors = usernames_by_role['doctor']
    nurses  = usernames_by_role['nurse']
    used_pids = set()

    for i in range(50):
        pid = random_patient_id()
        while pid in used_pids:
            pid = random_patient_id()
        used_pids.add(pid)

        idx = i % len(DIAGNOSES)
        name       = random_name()
        age        = random.randint(18, 80)
        gender     = random.choice(GENDERS)
        blood      = random.choice(BLOOD_GROUPS)
        contact    = random_phone()
        address    = random_address()
        diagnosis  = DIAGNOSES[idx]
        treatment  = TREATMENTS[idx]
        prescriptions = PRESCRIPTIONS[idx]
        last_visit = random_date(180)
        doctor     = random.choice(doctors)
        nurse      = random.choice(nurses)

        db.execute(
            '''INSERT INTO patients
               (patient_id, encrypted_name, encrypted_address, encrypted_diagnosis,
                encrypted_treatment, encrypted_prescriptions,
                age, gender, blood_group, contact, last_visit, assigned_doctor, assigned_nurse)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (
                pid,
                encrypt_field(name),
                encrypt_field(address),
                encrypt_field(diagnosis),
                encrypt_field(treatment),
                encrypt_field(prescriptions),
                age, gender, blood, contact,
                last_visit, doctor, nurse
            )
        )

    db.commit()
    print("  Created 50 synthetic patient records (all data is fictional)")

    # ── Seed some audit log entries ───────────────────────────────────────────
    sample_actions = [
        ('dr.mehta',  'doctor', 'LOGIN',         'auth',    '127.0.0.1', 'SUCCESS'),
        ('dr.iyer',   'doctor', 'LOGIN',          'auth',    '127.0.0.1', 'SUCCESS'),
        ('nurse01',   'nurse',  'LOGIN',          'auth',    '127.0.0.1', 'SUCCESS'),
        ('unknown',   'unknown','LOGIN_FAILED',   'auth',    '10.0.0.5',  'FAILED'),
        ('dr.mehta',  'doctor', 'VIEW_PATIENT',   'patient', '127.0.0.1', 'SUCCESS'),
        ('nurse02',   'nurse',  'UPDATE_VITALS',  'patient', '127.0.0.1', 'SUCCESS'),
        ('admin',     'admin',  'VIEW_AUDIT_LOGS','audit',   '127.0.0.1', 'SUCCESS'),
        ('hacker',    'unknown','UNAUTHORIZED_ACCESS','patients','10.0.0.99','DENIED'),
    ]
    for row in sample_actions:
        ts = (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(timespec='seconds')
        db.execute(
            'INSERT INTO audit_logs (username, role, action, resource, ip_address, status, timestamp) VALUES (?,?,?,?,?,?,?)',
            (*row, ts)
        )
    db.commit()
    print("  Seeded audit log entries")
    print("Sample data generation complete.\n")
    print("  Login credentials:")
    print("    Admin    : admin / Admin@1234!")
    print("    Doctors  : dr.mehta / Doctor@1234!")
    print("    Nurses   : nurse01 / Nurse@1234!")
