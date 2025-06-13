from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

# --- SQLite Setup ---
def get_db_connection():
    conn = sqlite3.connect('medical_maestro.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_sqlite_tables():
    conn = get_db_connection()
    # Users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    # Patients table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            gender TEXT,
            dob TEXT,
            pre_existing_conditions TEXT,
            allergies TEXT,
            current_medications TEXT
        )
    ''')
    # Appointments table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT NOT NULL,
            patient_name TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# --- MongoDB Setup ---
mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["medical_maestro"]
files_collection = mongo_db["patient_files"]

# --- Endpoints ---
@app.route('/')
@app.route('/login')
def login_page():
    return app.send_static_file('medical_login_screen.html')

@app.route('/welcome')
def welcome_page():
    return app.send_static_file('welcome_screen.html')

@app.route('/patient')
def patient_page():
    return app.send_static_file('patient_screen.html')

@app.route('/test-results')
def test_results_page():
    return app.send_static_file('medical_test_results.html')

@app.route('/appointments')
def appointments_page():
    return app.send_static_file('appointments_screen.html')

@app.route('/add-appointment')
def add_appointment_page():
    return app.send_static_file('add_appointment.html')

@app.route('/add-patient')
def add_patient_page():
    return app.send_static_file('add_patient.html')

@app.route('/add-user')
def add_user_page():
    return app.send_static_file('add_user.html')

@app.route('/admin')
def admin_dashboard():
    return app.send_static_file('admin_dashboard.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()
    if user:
        return jsonify({'success': True, 'full_name': user['full_name']})
    else:
        return jsonify({'success': False}), 401

@app.route('/appointments', methods=['GET'])
def get_appointments():
    conn = get_db_connection()
    appointments = conn.execute('SELECT time, patient_name FROM appointments').fetchall()
    conn.close()
    return jsonify([{'time': row['time'], 'patient_name': row['patient_name']} for row in appointments])

# Example endpoint for MongoDB files (expand as needed)
@app.route('/patient_files', methods=['GET'])
def get_patient_files():
    name = request.args.get('name')
    if not name:
        return jsonify({'error': 'Name is required.'}), 400
    files = list(files_collection.find({'name': name}, {'_id': 0}))
    return jsonify(files)

@app.route('/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT full_name, username FROM users').fetchall()
    conn.close()
    return jsonify([{'full_name': row['full_name'], 'username': row['username']} for row in users])

@app.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()
    full_name = data.get('full_name')
    username = data.get('username')
    password = data.get('password')
    if not (full_name and username and password):
        return jsonify({'error': 'All fields are required.'}), 400
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO users (full_name, username, password) VALUES (?, ?, ?)',
                     (full_name, username, password))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists.'}), 400

@app.route('/patients', methods=['GET'])
def get_patients():
    conn = get_db_connection()
    patients = conn.execute('SELECT name, gender, dob, pre_existing_conditions, allergies, current_medications FROM patients').fetchall()
    conn.close()
    return jsonify([
        {
            'name': row['name'],
            'gender': row['gender'],
            'dob': row['dob'],
            'pre_existing_conditions': row['pre_existing_conditions'],
            'allergies': row['allergies'],
            'current_medications': row['current_medications']
        } for row in patients
    ])

@app.route('/patients', methods=['POST'])
def add_patient():
    data = request.get_json()
    name = data.get('name')
    gender = data.get('gender')
    dob = data.get('dob')
    pre_existing_conditions = data.get('pre_existing_conditions')
    allergies = data.get('allergies')
    current_medications = data.get('current_medications')
    if not (name and gender and dob):
        return jsonify({'error': 'Name, Gender, and DOB are required.'}), 400
    conn = get_db_connection()
    conn.execute('INSERT INTO patients (name, gender, dob, pre_existing_conditions, allergies, current_medications) VALUES (?, ?, ?, ?, ?, ?)',
                 (name, gender, dob, pre_existing_conditions, allergies, current_medications))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/appointments', methods=['POST'])
def add_appointment():
    data = request.get_json()
    time = data.get('time')
    patient_name = data.get('patient_name')
    if not (time and patient_name):
        return jsonify({'error': 'Time and patient name are required.'}), 400
    conn = get_db_connection()
    conn.execute('INSERT INTO appointments (time, patient_name) VALUES (?, ?)', (time, patient_name))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/patients/by_name', methods=['GET'])
def get_patient_by_name():
    name = request.args.get('name')
    if not name:
        return jsonify({'error': 'Name is required.'}), 400
    conn = get_db_connection()
    patient = conn.execute('SELECT name, gender, dob, pre_existing_conditions, allergies, current_medications FROM patients WHERE name = ?', (name,)).fetchone()
    conn.close()
    if patient:
        return jsonify({
            'name': patient['name'],
            'gender': patient['gender'],
            'dob': patient['dob'],
            'pre_existing_conditions': patient['pre_existing_conditions'],
            'allergies': patient['allergies'],
            'current_medications': patient['current_medications']
        })
    else:
        return jsonify({'error': 'Patient not found.'}), 404

if __name__ == '__main__':
    init_sqlite_tables()
    app.run(host='0.0.0.0', port=5000, debug=True)