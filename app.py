from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sqlite3
import datetime
import hashlib

app = Flask(_name_)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS xray_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            patient_name TEXT DEFAULT 'Unknown',
            result TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_pneumonia_simulation(filename):
    hash_value = int(hashlib.md5(filename.encode()).hexdigest(), 16) % 100
    if hash_value < 30:
        return "Positive for Pneumonia"
    return "Negative - Not Infected"

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'xray' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['xray']
    patient_name = request.form.get('patient_name', 'Unknown')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        result = detect_pneumonia_simulation(filename)
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO xray_results (filename, patient_name, result)
            VALUES (?, ?, ?)
        ''', (filename, patient_name, result))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'filename': filename,
            'patient_name': patient_name,
            'result': result
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/recentresults')
def get_recent_results():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT patient_name, filename, result, upload_date
        FROM xray_results ORDER BY upload_date DESC LIMIT 10
    ''')
    results = cursor.fetchall()
    conn.close()
    
    formatted_results = []
    for row in results:
        formatted_results.append({
            'patient_name': row[0],
            'filename': row[1],
            'result': row[2],
            'upload_date': str(row[3])
        })
    return jsonify(formatted_results)

if _name_ == '_main_':
    init_db()
    app.run()
