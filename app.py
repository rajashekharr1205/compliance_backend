from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
# smtplib and other imports...
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import pymysql
import jwt
import datetime
from functools import wraps
from config import Config

import os
from compliance_model import ComplianceModel

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Base directory for uploads
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTO_FOLDER = os.path.join(BASE_DIR, 'uploads', 'profile_photos')
RECORDINGS_FOLDER = os.path.join(BASE_DIR, 'uploads', 'recordings')

for folder in [PHOTO_FOLDER, RECORDINGS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.config['UPLOAD_FOLDER'] = PHOTO_FOLDER
app.config['RECORDINGS_FOLDER'] = RECORDINGS_FOLDER

# Initialize Compliance Model
DATASET_PATHS = [
    os.path.join(BASE_DIR, 'dental_rule_based_dataset_1000.csv'),
    os.path.join(BASE_DIR, 'dental_compliance_words_3000.csv'),
    os.path.join(BASE_DIR, 'dental_compliance_ai_expanded.csv')
]
compliance_model = ComplianceModel(DATASET_PATHS)

def get_db_connection():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        cursorclass=pymysql.cursors.DictCursor
    )

def send_email(to_email, otp):
    subject = "Verification Code for ComplianceR"
    
    # HTML template based on user requirements for "ComplianceR"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="background-color: #000000; color: #ffffff; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 40px 20px; text-align: center;">
        <div style="max-width: 480px; margin: 0 auto; background-color: #121212; border-radius: 24px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid #222;">
            
            <div style="margin-bottom: 40px;">
                <h1 style="color: #ffffff; font-size: 28px; font-weight: 700; letter-spacing: -0.5px; margin: 0;">ComplianceR</h1>
            </div>

            <p style="color: #888888; font-size: 14px; margin-bottom: 24px;">Your verification code</p>
            
            <div style="background-color: #1A1A1A; border-radius: 16px; padding: 30px 10px; margin-bottom: 32px; border: 1px solid #333;">
                <span style="font-size: 38px; font-weight: 800; letter-spacing: 8px; color: #ffffff; font-family: 'Courier New', monospace; white-space: nowrap; display: inline-block;">{otp}</span>
            </div>

            <div style="margin-bottom: 32px;">
                <p style="color: #FFFFFF; font-size: 16px; line-height: 1.6; margin: 0 0 8px 0;">This code is valid for 5 minutes.</p>
                <p style="color: #FF5252; font-size: 16px; font-weight: 600; margin: 0;">Don't share to anyone else</p>
            </div>

            <p style="color: #555555; font-size: 13px; margin: 0;">
                If you didn't request this, you can safely ignore this email.
            </p>

            <div style="margin-top: 48px; padding-top: 24px; border-top: 1px solid #222;">
                <p style="color: #444444; font-size: 12px; margin: 0;">
                    &copy; 2026 ComplianceR. All rights reserved.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create the root message and set headers
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"ComplianceR <{app.config['MAIL_USERNAME']}>"
    msg['To'] = to_email

    # Plain text version for compatibility
    text_content = f"Your Verification Code is: {otp}. This code is valid for 5 minutes. Don't share to anyone else."
    
    part1 = MIMEText(text_content, 'plain')
    part2 = MIMEText(html_content, 'html')

    msg.attach(part1)
    msg.attach(part2)

    try:
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            if app.config['MAIL_USE_TLS']:
                server.starttls()
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'status': 'success',
        'message': 'Compliance Backend API is running',
        'version': '1.0'
    })

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user_id, *args, **kwargs)
    return decorated

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'message': 'Missing data'}), 400
    
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "INSERT INTO users (name, email, designation, registration_id, password) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (data['name'], data['email'], data.get('designation'), data.get('registration_id'), data['password']))
        conn.commit()
    except pymysql.err.IntegrityError:
        return jsonify({'message': 'User already exists'}), 409
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        conn.close()
    
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing data'}), 400
    
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM users WHERE email = %s"
            cursor.execute(sql, (data['email'],))
            user = cursor.fetchone()
        
        if user and user['password'] == data['password']:
            token = jwt.encode({
                'user_id': user['id'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['JWT_SECRET_KEY'], algorithm="HS256")
            
            return jsonify({
                'token': token,
                'user': {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'designation': user['designation'],
                    'registration_id': user['registration_id'],
                    'profile_photo': user.get('profile_photo')
                }
            })
        
        return jsonify({'message': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/profile', methods=['GET', 'PUT'])
@token_required
def profile(user_id):
    if request.method == 'GET':
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, name, email, designation, registration_id, profile_photo FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
            return jsonify(user)
        finally:
            conn.close()
    
    elif request.method == 'PUT':
        data = request.get_json()
        print(f"DEBUG: Received update request for user {user_id}: {data}") # Debug logging
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                sql = "UPDATE users SET name = %s, designation = %s, registration_id = %s, profile_photo = %s WHERE id = %s"
                cursor.execute(sql, (data.get('name'), data.get('designation'), data.get('registration_id'), data.get('profile_photo'), user_id))
            conn.commit()
            return jsonify({'message': 'Profile updated successfully'})
        except Exception as e:
            print(f"ERROR: Profile update failed for user {user_id}: {str(e)}")
            return jsonify({'message': str(e)}), 500
        finally:
            if 'conn' in locals():
                conn.close()

@app.route('/api/reports', methods=['GET', 'POST', 'DELETE'])
@token_required
def reports(user_id):
    if request.method == 'GET':
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM reports WHERE user_id = %s ORDER BY timestamp DESC", (user_id,))
                reports_list = cursor.fetchall()
            return jsonify(reports_list)
        finally:
            if 'conn' in locals():
                conn.close()
    
    elif request.method == 'POST':
        data = request.get_json()
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                sql = "INSERT INTO reports (user_id, report_name, transcript, score, verdict, duration, recording_url, patient_info, department, date_of_consultation, remarks, folder_name, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (
                    user_id, 
                    data.get('report_name'), 
                    data.get('transcript'), 
                    data.get('score'), 
                    data.get('verdict'), 
                    data.get('duration'),
                    data.get('recording_url'),
                    data.get('patient_info'),
                    data.get('department'),
                    data.get('date_of_consultation'),
                    data.get('remarks'),
                    data.get('folder_name', 'Audits'),
                    data.get('timestamp')
                ))
            conn.commit()
            return jsonify({'message': 'Report saved successfully'}), 201
        finally:
            if 'conn' in locals():
                conn.close()

    elif request.method == 'DELETE':
        timestamp = request.args.get('timestamp')
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                if timestamp:
                    cursor.execute("DELETE FROM reports WHERE user_id = %s AND timestamp = %s", (user_id, timestamp))
                    conn.commit()
                    return jsonify({'message': 'Report deleted successfully'})
                else:
                    cursor.execute("DELETE FROM reports WHERE user_id = %s", (user_id,))
                    conn.commit()
                    return jsonify({'message': 'All reports deleted successfully'})
        except Exception as e:
            return jsonify({'message': str(e)}), 500
        finally:
            if 'conn' in locals():
                conn.close()

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')
    flow = data.get('flow', 'RESET')
    if not email:
        return jsonify({'message': 'Email is required'}), 400
    
    otp = str(random.randint(100000, 999999))
    
    # Store OTP in DB
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check user existence based on flow
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if flow == 'RESET' and not user:
                return jsonify({'message': 'The account is not found'}), 404
            
            if flow == 'REGISTER' and user:
                return jsonify({'message': 'User already exists'}), 409

            # Then clean up old OTPs for this email
            cursor.execute("DELETE FROM otp_codes WHERE email = %s", (email,))
            sql = "INSERT INTO otp_codes (email, otp, created_at) VALUES (%s, %s, %s)"
            cursor.execute(sql, (email, otp, datetime.datetime.utcnow()))
        conn.commit()
    except Exception as e:
        return jsonify({'message': f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

    if send_email(email, otp):
        return jsonify({'message': 'OTP sent successfully'})
    else:
        return jsonify({'message': 'Failed to send OTP via SMTP. Please check credentials.'}), 500

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    
    if not email or not otp:
        return jsonify({'message': 'Email and OTP are required'}), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM otp_codes WHERE email = %s AND otp = %s", (email, otp))
            record = cursor.fetchone()
            
            if record:
                # Check if expired (e.g. 10 minutes)
                created_at = record['created_at']
                if datetime.datetime.utcnow() - created_at < datetime.timedelta(minutes=5):
                    # Success, delete OTP
                    cursor.execute("DELETE FROM otp_codes WHERE email = %s", (email,))
                    conn.commit()
                    return jsonify({'message': 'OTP verified successfully'})
                else:
                    return jsonify({'message': 'OTP has expired'}), 401
            else:
                return jsonify({'message': 'Invalid OTP'}), 401
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/upload-photo', methods=['POST'])
@token_required
def upload_photo(user_id):
    if 'photo' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['photo']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    if file:
        filename = f"user_{user_id}_{int(datetime.datetime.utcnow().timestamp())}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Build the URL to access this photo (Use relative path for flexibility)
        photo_url = f"/uploads/profile_photos/{filename}"
        
        # Update database
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET profile_photo = %s WHERE id = %s", (photo_url, user_id))
            conn.commit()
        finally:
            conn.close()
            
        return jsonify({'message': 'Photo uploaded successfully', 'photo_url': photo_url})


@app.route('/api/analyze-compliance', methods=['POST'])
@token_required
def analyze_compliance(user_id):
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    
    transcript = data.get('transcript', '')
    # Allow empty transcript but log it
    if not transcript:
        print(f"Warning: Empty transcript received for user {user_id}")
    
    print(f"DEBUG: Analyzing compliance for user {user_id}. Transcript: {transcript}")
    result = compliance_model.analyze_conversation(transcript)
    print(f"DEBUG: Analysis result: Score={result['compliance_percentage']}%, Prediction={result['prediction']}")
    return jsonify(result)

@app.route('/uploads/profile_photos/<filename>')
def serve_photo(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/institutional-stats', methods=['GET'])
def institutional_stats():
    """Returns aggregated compliance statistics across all departments for institutional audit."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Calculate average score per department
            # We filter out rows where department is null or empty
            sql = """
                SELECT 
                    department, 
                    ROUND(AVG(score), 1) as average_score,
                    COUNT(*) as report_count
                FROM reports 
                WHERE department IS NOT NULL AND department != ''
                GROUP BY department
                ORDER BY average_score DESC
            """
            cursor.execute(sql)
            stats = cursor.fetchall()
            
        return jsonify({
            'status': 'success',
            'data': stats,
            'total_departments': len(stats)
        })
    except Exception as e:
        print(f"Error fetching institutional stats: {e}")
        return jsonify({'message': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
