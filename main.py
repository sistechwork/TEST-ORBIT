import os
import secrets
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mail import Mail, Message
from database import db
from werkzeug.utils import secure_filename
from encryption_service import encryption_service
from activity_logger import log_activity, get_recent_activities
import models

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or secrets.token_hex(32)

database_url = os.environ.get("DATABASE_URL")
if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///exam_portal.db"
    print("WARNING: Using SQLite database. For production, set DATABASE_URL environment variable to use PostgreSQL.")

app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "True") == "True"
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")

db.init_app(app)
mail = Mail(app)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

with app.app_context():
    import models
    db.create_all()

def load_smtp_settings_from_db():
    try:
        from encryption_service import encryption_service
        import models
        
        server = models.AdminSecret.query.filter_by(secret_key='MAIL_SERVER').first()
        port = models.AdminSecret.query.filter_by(secret_key='MAIL_PORT').first()
        username = models.AdminSecret.query.filter_by(secret_key='MAIL_USERNAME').first()
        password = models.AdminSecret.query.filter_by(secret_key='MAIL_PASSWORD').first()
        use_tls = models.AdminSecret.query.filter_by(secret_key='MAIL_USE_TLS').first()
        
        if server:
            decrypted_server = encryption_service.decrypt(server.encrypted_value)
            if decrypted_server:
                app.config["MAIL_SERVER"] = decrypted_server
        
        if port:
            decrypted_port = encryption_service.decrypt(port.encrypted_value)
            if decrypted_port and decrypted_port.isdigit():
                app.config["MAIL_PORT"] = int(decrypted_port)
        
        if username:
            decrypted_username = encryption_service.decrypt(username.encrypted_value)
            if decrypted_username:
                app.config["MAIL_USERNAME"] = decrypted_username
        
        if password:
            decrypted_password = encryption_service.decrypt(password.encrypted_value)
            if decrypted_password:
                app.config["MAIL_PASSWORD"] = decrypted_password
        
        if use_tls:
            decrypted_tls = encryption_service.decrypt(use_tls.encrypted_value)
            if decrypted_tls:
                app.config["MAIL_USE_TLS"] = decrypted_tls.lower() in ['true', '1', 'yes']
        
        mail.init_app(app)
    except Exception as e:
        print(f"Error loading SMTP settings: {e}")

with app.app_context():
    load_smtp_settings_from_db()

def generate_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def send_credentials_email(email, password):
    try:
        if not app.config["MAIL_USERNAME"] or not app.config["MAIL_PASSWORD"]:
            print("Email credentials not configured. Set MAIL_USERNAME and MAIL_PASSWORD environment variables.")
            return False
        
        msg = Message(
            subject="Your Exam Portal Credentials",
            sender=app.config["MAIL_USERNAME"],
            recipients=[email]
        )
        msg.body = f"""
Hello,

Your account has been created for the exam portal.

Email (Username): {email}
Password: {password}

Please use your email address to login.

Best regards,
Exam Portal Team
"""
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email to {email}: {e}")
        return False

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('exam'))
    if 'admin' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('index.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin@vcodez' and password == 'admin@123':
            session['admin'] = True
            log_activity(
                user_id=None,
                activity_type='admin_login',
                description='Admin logged in successfully'
            )
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'error')
    
    return render_template('admin_login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = models.User.query.filter_by(email=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.email
            session['proctoring_verified'] = user.verification_photo is not None
            log_activity(
                user_id=user.id,
                activity_type='user_login',
                description=f'User {username} logged in successfully'
            )
            if user.verification_photo:
                return redirect(url_for('exam'))
            else:
                return redirect(url_for('verification'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        name = request.form.get('name', '').strip()
        
        if not email:
            flash('Email is required', 'error')
            return render_template('register.html')
        
        if not password or len(password) < 6:
            flash('Password is required and must be at least 6 characters', 'error')
            return render_template('register.html')
        
        if models.User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('register.html')
        
        username = email.split('@')[0] if '@' in email else email
        
        user = models.User(username=username)
        user.set_password(password)
        user.email = email
        user.name = name
        db.session.add(user)
        db.session.commit()
        
        email_sent = send_credentials_email(email, password)
        if email_sent:
            flash('Registration successful! Credentials have been sent to your email. Please login.', 'success')
        else:
            flash(f'Registration successful! Email delivery failed. Your password is: {password}. Please save it and login.', 'warning')
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/verification')
def verification():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = models.User.query.get(session['user_id'])
    if user and user.verification_photo:
        session['verification_photo_saved'] = True
    
    return render_template('verification.html')

@app.route('/save_verification_photo', methods=['POST'])
def save_verification_photo():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    if not data or 'photo' not in data:
        return jsonify({'success': False, 'message': 'No photo data provided'}), 400
    
    photo_data = data['photo']
    if not photo_data.startswith('data:image'):
        return jsonify({'success': False, 'message': 'Invalid photo format'}), 400
    
    user = models.User.query.get(session['user_id'])
    if user:
        user.verification_photo = photo_data
        db.session.commit()
        session['verification_photo_saved'] = True
        return jsonify({'success': True, 'message': 'Verification photo saved successfully'})
    
    return jsonify({'success': False, 'message': 'User not found'}), 404

@app.route('/get_verification_photo')
def get_verification_photo():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    user = models.User.query.get(session['user_id'])
    if user and user.verification_photo:
        return jsonify({'success': True, 'photo': user.verification_photo})
    
    return jsonify({'success': False, 'message': 'No verification photo found'}), 404

@app.route('/verify_proctoring_setup', methods=['POST'])
def verify_proctoring_setup():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No verification data provided'}), 400
    
    camera_working = data.get('camera_working', False)
    audio_working = data.get('audio_working', False)
    face_detected = data.get('face_detected', False)
    
    user = models.User.query.get(session['user_id'])
    photo_captured = user and user.verification_photo is not None
    
    if not isinstance(camera_working, bool) or not isinstance(audio_working, bool) or not isinstance(face_detected, bool):
        return jsonify({'success': False, 'message': 'Invalid verification data format'}), 400
    
    if camera_working and audio_working and face_detected and photo_captured:
        session['proctoring_verified'] = True
        return jsonify({'success': True, 'message': 'Proctoring setup verified successfully'})
    
    missing = []
    if not camera_working:
        missing.append('camera access')
    if not audio_working:
        missing.append('microphone access')
    if not face_detected:
        missing.append('face detection')
    if not photo_captured:
        missing.append('verification photo')
    
    return jsonify({
        'success': False, 
        'message': f'Verification incomplete. Missing: {", ".join(missing)}'
    }), 400

@app.route('/proctor/events', methods=['POST'])
def log_proctor_event():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request'}), 400
    
    allowed_event_types = ['no_face_detected', 'multiple_faces', 'high_noise_level']
    event_type = data.get('event_type', '')
    if event_type not in allowed_event_types:
        return jsonify({'success': False, 'message': 'Invalid event type'}), 400
    
    allowed_severities = ['info', 'warning', 'error']
    severity = data.get('severity', 'warning')
    if severity not in allowed_severities:
        severity = 'warning'
    
    from datetime import datetime, timedelta
    recent_events = models.ProctorEvent.query.filter_by(
        user_id=session['user_id'],
        event_type=event_type
    ).filter(
        models.ProctorEvent.created_at > datetime.utcnow() - timedelta(seconds=10)
    ).count()
    
    if recent_events >= 3:
        return jsonify({'success': True, 'message': 'Rate limited'}), 429
    
    event = models.ProctorEvent(
        user_id=session['user_id'],
        event_type=event_type,
        event_details=data.get('event_details', '')[:500],
        severity=severity
    )
    db.session.add(event)
    db.session.commit()
    
    return jsonify({'success': True, 'event_id': event.id})

@app.route('/exam')
def exam():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if not session.get('proctoring_verified', False):
        return redirect(url_for('verification'))
    
    user_id = session['user_id']
    existing_responses = models.ExamResponse.query.filter_by(user_id=user_id).first()
    
    if existing_responses:
        flash('You have already completed the exam', 'info')
        return redirect(url_for('exam_completed'))
    
    questions = models.Question.query.all()
    
    duration_setting = models.AdminSettings.query.filter_by(setting_key='exam_duration').first()
    try:
        duration = int(duration_setting.setting_value) if duration_setting else 60
        if duration < 1:
            duration = 60
    except (ValueError, TypeError):
        duration = 60
    
    return render_template('exam.html', questions=questions, duration=duration)

@app.route('/submit_exam', methods=['POST'])
def submit_exam():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    questions = models.Question.query.all()
    
    for question in questions:
        if question.question_type == 'MCQ':
            user_answer = request.form.get(f'question_{question.id}')
            user_answer_text = None
            is_correct = user_answer == question.correct_answer if user_answer else False
            points = question.points if is_correct else 0
        else:
            user_answer = None
            user_answer_text = request.form.get(f'question_{question.id}')
            is_correct = False
            points = 0
        
        response = models.ExamResponse(
            user_id=user_id,
            question_id=question.id,
            user_answer=user_answer,
            user_answer_text=user_answer_text,
            is_correct=is_correct,
            points_earned=points
        )
        db.session.add(response)
    
    db.session.commit()
    flash('Exam submitted successfully!', 'success')
    return redirect(url_for('exam_completed'))

@app.route('/exam_completed')
def exam_completed():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('exam_completed.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    users = models.User.query.all()
    questions = models.Question.query.all()
    
    user_data = []
    for user in users:
        responses = models.ExamResponse.query.filter_by(user_id=user.id).all()
        total_questions = len(responses)
        correct_answers = sum(1 for r in responses if r.is_correct)
        score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        proctor_events = models.ProctorEvent.query.filter_by(user_id=user.id).all()
        violation_counts = {
            'no_face': sum(1 for e in proctor_events if e.event_type == 'no_face_detected'),
            'multiple_faces': sum(1 for e in proctor_events if e.event_type == 'multiple_faces'),
            'high_noise': sum(1 for e in proctor_events if e.event_type == 'high_noise_level'),
            'total': len(proctor_events)
        }
        
        user_data.append({
            'user': user,
            'responses': responses,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'score': score,
            'proctor_events': proctor_events,
            'violation_counts': violation_counts
        })
    
    block_password_setting = models.AdminSettings.query.filter_by(setting_key='block_password').first()
    block_password = block_password_setting.setting_value if block_password_setting else ''
    
    duration_setting = models.AdminSettings.query.filter_by(setting_key='exam_duration').first()
    exam_duration = duration_setting.setting_value if duration_setting else '60'
    
    return render_template('admin_dashboard.html', user_data=user_data, all_users=users, questions=questions, block_password=block_password, exam_duration=exam_duration, mail_username=app.config.get('MAIL_USERNAME', ''))

@app.route('/admin/set_block_password', methods=['POST'])
def set_block_password():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    new_password = request.form.get('block_password')
    setting = models.AdminSettings.query.filter_by(setting_key='block_password').first()
    
    if setting:
        setting.setting_value = new_password
    else:
        setting = models.AdminSettings(setting_key='block_password', setting_value=new_password)
        db.session.add(setting)
    
    db.session.commit()
    flash('Block password updated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/set_exam_duration', methods=['POST'])
def set_exam_duration():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    try:
        new_duration = int(request.form.get('exam_duration', 60))
        if new_duration < 1 or new_duration > 300:
            flash('Duration must be between 1 and 300 minutes!', 'error')
            return redirect(url_for('admin_dashboard'))
    except (ValueError, TypeError):
        flash('Invalid duration value! Please enter a valid number.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    setting = models.AdminSettings.query.filter_by(setting_key='exam_duration').first()
    
    if setting:
        setting.setting_value = str(new_duration)
    else:
        setting = models.AdminSettings(setting_key='exam_duration', setting_value=str(new_duration))
        db.session.add(setting)
    
    db.session.commit()
    flash('Exam duration updated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/create_question', methods=['POST'])
def create_question():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    question_type = request.form.get('question_type')
    question_text = request.form.get('question_text')
    points = int(request.form.get('points', 1))
    
    if question_type == 'MCQ':
        option_a = request.form.get('option_a')
        option_b = request.form.get('option_b')
        option_c = request.form.get('option_c')
        option_d = request.form.get('option_d')
        correct_answer = request.form.get('correct_answer')
        
        question = models.Question(
            question_type='MCQ',
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer,
            points=points
        )
    elif question_type == 'SHORT_ANSWER':
        correct_answer_text = request.form.get('correct_answer_text', '')
        
        question = models.Question(
            question_type='SHORT_ANSWER',
            question_text=question_text,
            correct_answer_text=correct_answer_text,
            points=points
        )
    elif question_type == 'PARAGRAPH':
        correct_answer_text = request.form.get('correct_answer_text', '')
        
        question = models.Question(
            question_type='PARAGRAPH',
            question_text=question_text,
            correct_answer_text=correct_answer_text,
            points=points
        )
    
    db.session.add(question)
    db.session.commit()
    log_activity(
        user_id=None,
        activity_type='question_create',
        description=f'Admin created {question_type} question: {question_text[:50]}...'
    )
    flash(f'{question_type} question created successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    question = models.Question.query.get_or_404(question_id)
    question_text = question.question_text[:50]
    db.session.delete(question)
    db.session.commit()
    log_activity(
        user_id=None,
        activity_type='question_delete',
        description=f'Admin deleted question: {question_text}... (ID: {question_id})'
    )
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/verify_block_password', methods=['POST'])
def verify_block_password():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    entered_password = data.get('password', '')
    
    block_password_setting = models.AdminSettings.query.filter_by(setting_key='block_password').first()
    correct_password = block_password_setting.setting_value if block_password_setting else 'exam2024'
    
    if entered_password == correct_password:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Incorrect password'})

@app.route('/admin/bulk_import', methods=['POST'])
def bulk_import():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    try:
        try:
            import pandas as pd
        except ImportError:
            flash('Error: pandas/openpyxl libraries not installed. Cannot process bulk imports. Please install required dependencies.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        if 'bulk_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('admin_dashboard'))
        
        file = request.files['bulk_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('admin_dashboard'))
        
        filename = secure_filename(file.filename)
        
        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(file)
        else:
            flash('Invalid file format. Please upload CSV or Excel file.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        required_columns = ['Name', 'Email Id']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            flash(f'Missing required columns: {", ".join(missing_columns)}. Required: Name, Email Id.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        success_count = 0
        error_count = 0
        email_failures = []
        
        for index, row in df.iterrows():
            try:
                email = str(row.get('Email Id', '')).strip()
                name = str(row.get('Name', '')).strip()
                
                if not email:
                    error_count += 1
                    continue
                
                username = email.split('@')[0] if '@' in email else name.replace(' ', '_').lower()
                
                existing_user = models.User.query.filter_by(username=username).first()
                if existing_user:
                    error_count += 1
                    continue
                
                password = generate_password()
                
                user = models.User(username=username)
                user.set_password(password)
                user.name = name
                user.email = email
                user.contact_number = str(row.get('Contact Number', '')).strip()
                user.location = str(row.get('Location', '')).strip()
                user.institute_name = str(row.get('Institute Name', '')).strip()
                user.college_name = str(row.get('College Name', '')).strip()
                user.degree = str(row.get('Degree', '')).strip()
                user.year_of_passing = str(row.get('Year of Passing', '')).strip()
                user.resume_url = str(row.get('Resume', '')).strip()
                
                db.session.add(user)
                db.session.commit()
                
                email_sent = send_credentials_email(email, password)
                if not email_sent:
                    email_failures.append({'email': email, 'password': password, 'name': name})
                
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"Error processing row {index + 2}: {e}")
                continue
        
        if success_count > 0:
            log_activity(
                user_id=None,
                activity_type='bulk_import',
                description=f'Bulk import: {success_count} users created successfully'
            )
            flash(f'Bulk import completed! {success_count} users created successfully.', 'success')
        if len(email_failures) > 0:
            failure_details = []
            for failure in email_failures[:5]:
                failure_details.append(f"{failure['name']} ({failure['email']}): {failure['password']}")
            more_text = f" and {len(email_failures) - 5} more..." if len(email_failures) > 5 else ""
            flash(f'Warning: {len(email_failures)} credential emails failed to send. Passwords for failed deliveries: {" | ".join(failure_details)}{more_text}', 'warning')
        if error_count > 0:
            flash(f'{error_count} rows skipped due to errors (duplicate usernames or missing required fields).', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    except Exception as e:
        flash(f'Error during bulk import: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_user', methods=['POST'])
def add_user():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    try:
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        name = request.form.get('name', '').strip()
        
        if not username:
            flash('Username is required', 'error')
            return redirect(url_for('admin_dashboard'))
        
        existing_user = models.User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
            return redirect(url_for('admin_dashboard'))
        
        password = generate_password()
        
        user = models.User(username=username)
        user.set_password(password)
        user.name = name
        user.email = email
        user.contact_number = request.form.get('contact_number', '').strip()
        user.location = request.form.get('location', '').strip()
        user.institute_name = request.form.get('institute_name', '').strip()
        user.college_name = request.form.get('college_name', '').strip()
        user.degree = request.form.get('degree', '').strip()
        user.year_of_passing = request.form.get('year_of_passing', '').strip()
        user.resume_url = request.form.get('resume_url', '').strip()
        
        db.session.add(user)
        db.session.commit()
        
        log_activity(
            user_id=user.id,
            activity_type='user_create',
            description=f'Admin created user: {username}'
        )
        
        if email:
            email_sent = send_credentials_email(email, password)
            if email_sent:
                flash(f'User {username} created and credentials emailed successfully!', 'success')
            else:
                flash(f'User {username} created but email delivery failed. Password: {password}. Please share with user.', 'warning')
        else:
            flash(f'User {username} created successfully! Password: {password}. Please share with user.', 'warning')
        
        return redirect(url_for('admin_dashboard'))
    
    except Exception as e:
        flash(f'Error creating user: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_user/<int:user_id>', methods=['POST'])
def update_user(user_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    try:
        user = models.User.query.get_or_404(user_id)
        
        user.name = request.form.get('name', '').strip()
        user.email = request.form.get('email', '').strip()
        user.contact_number = request.form.get('contact_number', '').strip()
        user.location = request.form.get('location', '').strip()
        user.institute_name = request.form.get('institute_name', '').strip()
        user.college_name = request.form.get('college_name', '').strip()
        user.degree = request.form.get('degree', '').strip()
        user.year_of_passing = request.form.get('year_of_passing', '').strip()
        user.resume_url = request.form.get('resume_url', '').strip()
        
        db.session.commit()
        flash(f'User {user.username} updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    except Exception as e:
        flash(f'Error updating user: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    try:
        user = models.User.query.get_or_404(user_id)
        username = user.username
        db.session.delete(user)
        db.session.commit()
        log_activity(
            user_id=None,
            activity_type='user_delete',
            description=f'Admin deleted user: {username} (ID: {user_id})'
        )
        flash(f'User {username} deleted successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/generate_password/<int:user_id>', methods=['POST'])
def generate_new_password(user_id):
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        user = models.User.query.get_or_404(user_id)
        new_password = generate_password()
        user.set_password(new_password)
        db.session.commit()
        
        log_activity(
            user_id=user.id,
            activity_type='password_reset',
            description=f'Admin generated new password for user: {user.username}'
        )
        
        return jsonify({
            'success': True,
            'password': new_password,
            'message': 'Password generated successfully'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/send_credentials/<int:user_id>', methods=['POST'])
def send_user_credentials(user_id):
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        user = models.User.query.get_or_404(user_id)
        
        if not user.email:
            return jsonify({'success': False, 'message': 'User has no email address'}), 400
        
        data = request.get_json()
        password = data.get('password', '')
        
        if not password:
            return jsonify({'success': False, 'message': 'No password provided'}), 400
        
        email_sent = send_credentials_email(user.email, password)
        
        if email_sent:
            log_activity(
                user_id=user.id,
                activity_type='credentials_sent',
                description=f'Admin sent credentials to user: {user.username}'
            )
            return jsonify({'success': True, 'message': f'Credentials sent to {user.email}'})
        else:
            return jsonify({'success': False, 'message': 'Email delivery failed. Check SMTP settings.'}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/update_question/<int:question_id>', methods=['POST'])
def update_question(question_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    try:
        question = models.Question.query.get_or_404(question_id)
        
        question.question_text = request.form.get('question_text', '').strip()
        question.points = int(request.form.get('points', 1))
        
        if question.question_type == 'MCQ':
            question.option_a = request.form.get('option_a', '').strip()
            question.option_b = request.form.get('option_b', '').strip()
            question.option_c = request.form.get('option_c', '').strip()
            question.option_d = request.form.get('option_d', '').strip()
            question.correct_answer = request.form.get('correct_answer', '').strip()
        else:
            question.correct_answer_text = request.form.get('correct_answer_text', '').strip()
        
        db.session.commit()
        flash(f'Question updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    except Exception as e:
        flash(f'Error updating question: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/user/profile')
def user_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = models.User.query.get_or_404(session['user_id'])
    
    responses = models.ExamResponse.query.filter_by(user_id=user.id).all()
    total_questions = len(responses)
    correct_answers = sum(1 for r in responses if r.is_correct)
    score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    submission_date = responses[0].submitted_at.strftime('%B %d, %Y at %I:%M %p') if responses else None
    
    return render_template('profile.html',
        user=user,
        exam_completed=total_questions > 0,
        score=score,
        total_questions=total_questions,
        correct_answers=correct_answers,
        submission_date=submission_date
    )

@app.route('/admin/download_sample_template')
def download_sample_template():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    try:
        import pandas as pd
        import io
        from flask import send_file
        
        sample_data = pd.DataFrame({
            'Name': ['John Doe', 'Jane Smith'],
            'Email Id': ['john@example.com', 'jane@example.com'],
            'Contact Number': ['1234567890', '0987654321'],
            'Location': ['New York', 'Los Angeles'],
            'Institute Name': ['Tech Institute', 'Science Academy'],
            'College Name': ['Engineering College', 'Arts College'],
            'Degree': ['B.Tech', 'B.Sc'],
            'Year of Passing': ['2024', '2025'],
            'Resume': ['https://example.com/resume1.pdf', 'https://example.com/resume2.pdf']
        })
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            sample_data.to_excel(writer, index=False, sheet_name='Users')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='sample_users_template.xlsx'
        )
    except ImportError:
        flash('Error: pandas/openpyxl libraries not installed. Cannot generate sample template.', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/smtp_settings', methods=['GET', 'POST'])
def smtp_settings():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            mail_server = request.form.get('mail_server', '').strip()
            mail_port = request.form.get('mail_port', '').strip()
            mail_use_tls = request.form.get('mail_use_tls') == 'on'
            mail_username = request.form.get('mail_username', '').strip()
            mail_password = request.form.get('mail_password', '').strip()
            
            def save_or_update_secret(key, value):
                secret = models.AdminSecret.query.filter_by(secret_key=key).first()
                encrypted_value = encryption_service.encrypt(value)
                
                if secret:
                    secret.encrypted_value = encrypted_value
                else:
                    secret = models.AdminSecret(secret_key=key, encrypted_value=encrypted_value)
                    db.session.add(secret)
            
            save_or_update_secret('MAIL_SERVER', mail_server)
            save_or_update_secret('MAIL_PORT', mail_port)
            save_or_update_secret('MAIL_USE_TLS', str(mail_use_tls))
            save_or_update_secret('MAIL_USERNAME', mail_username)
            if mail_password:
                save_or_update_secret('MAIL_PASSWORD', mail_password)
            
            db.session.commit()
            
            app.config['MAIL_SERVER'] = mail_server
            app.config['MAIL_PORT'] = int(mail_port) if mail_port.isdigit() else 587
            app.config['MAIL_USE_TLS'] = mail_use_tls
            app.config['MAIL_USERNAME'] = mail_username
            if mail_password:
                app.config['MAIL_PASSWORD'] = mail_password
            
            mail.init_app(app)
            
            log_activity(
                user_id=None,
                activity_type='smtp_config_update',
                description=f'SMTP settings updated by admin'
            )
            
            flash('SMTP settings updated successfully!', 'success')
            return redirect(url_for('smtp_settings'))
        
        except Exception as e:
            flash(f'Error updating SMTP settings: {str(e)}', 'error')
            return redirect(url_for('smtp_settings'))
    
    def get_secret_value(key, default=''):
        secret = models.AdminSecret.query.filter_by(secret_key=key).first()
        if secret:
            return encryption_service.decrypt(secret.encrypted_value)
        return default
    
    current_settings = {
        'mail_server': get_secret_value('MAIL_SERVER', app.config.get('MAIL_SERVER', 'smtp.gmail.com')),
        'mail_port': get_secret_value('MAIL_PORT', str(app.config.get('MAIL_PORT', 587))),
        'mail_use_tls': get_secret_value('MAIL_USE_TLS', 'True') == 'True',
        'mail_username': get_secret_value('MAIL_USERNAME', app.config.get('MAIL_USERNAME', '')),
    }
    
    return render_template('admin_smtp_settings.html', settings=current_settings)

@app.route('/admin/test_email', methods=['POST'])
def test_email():
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        test_recipient = request.form.get('test_email', '').strip()
        
        if not test_recipient:
            return jsonify({'success': False, 'message': 'Please provide a test email address'})
        
        msg = Message(
            subject='Test Email from Exam Portal',
            sender=app.config['MAIL_USERNAME'],
            recipients=[test_recipient]
        )
        msg.body = 'This is a test email from the Exam Portal admin panel. If you received this, your SMTP settings are configured correctly!'
        
        mail.send(msg)
        
        log_activity(
            user_id=None,
            activity_type='test_email_sent',
            description=f'Test email sent to {test_recipient}'
        )
        
        return jsonify({'success': True, 'message': f'Test email sent successfully to {test_recipient}!'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to send test email: {str(e)}'})

@app.route('/admin/activities')
def admin_activities():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 50
    activity_type_filter = request.args.get('type', None)
    
    offset = (page - 1) * per_page
    activities, total_count = get_recent_activities(
        limit=per_page,
        offset=offset,
        activity_type=activity_type_filter if activity_type_filter else None
    )
    
    total_pages = (total_count + per_page - 1) // per_page
    
    activity_types = db.session.query(models.ActivityLog.activity_type).distinct().all()
    activity_types = [at[0] for at in activity_types]
    
    return render_template('admin_activities.html',
        activities=activities,
        page=page,
        total_pages=total_pages,
        total_count=total_count,
        activity_types=activity_types,
        current_filter=activity_type_filter
    )

@app.route('/admin/users_list')
def admin_users_list():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    sort_by = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    
    allowed_sort_fields = ['username', 'name', 'email', 'created_at', 'location', 'college_name']
    if sort_by not in allowed_sort_fields:
        sort_by = 'created_at'
    
    query = models.User.query
    
    if order == 'asc':
        query = query.order_by(getattr(models.User, sort_by).asc())
    else:
        query = query.order_by(getattr(models.User, sort_by).desc())
    
    users = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin_users.html',
        users=users.items,
        page=page,
        total_pages=users.pages,
        total_users=users.total,
        sort_by=sort_by,
        order=order
    )

@app.route('/admin/user_details/<int:user_id>')
def user_details(user_id):
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    user = models.User.query.get_or_404(user_id)
    
    responses = models.ExamResponse.query.filter_by(user_id=user.id).all()
    total_questions = len(responses)
    correct_answers = sum(1 for r in responses if r.is_correct)
    score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    proctor_events = models.ProctorEvent.query.filter_by(user_id=user.id).all()
    
    user_data = {
        'id': user.id,
        'username': user.username,
        'name': user.name or 'N/A',
        'email': user.email or 'N/A',
        'contact_number': user.contact_number or 'N/A',
        'location': user.location or 'N/A',
        'institute_name': user.institute_name or 'N/A',
        'college_name': user.college_name or 'N/A',
        'degree': user.degree or 'N/A',
        'year_of_passing': user.year_of_passing or 'N/A',
        'resume_url': user.resume_url or '',
        'created_at': user.created_at.strftime('%B %d, %Y at %I:%M %p') if user.created_at else 'N/A',
        'exam_completed': total_questions > 0,
        'score': round(score, 2),
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'proctor_events_count': len(proctor_events)
    }
    
    return jsonify({'success': True, 'user': user_data})

@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    username = session.get('username', 'Unknown')
    is_admin = 'admin' in session
    
    if is_admin:
        log_activity(
            user_id=None,
            activity_type='admin_logout',
            description='Admin logged out'
        )
    elif user_id:
        log_activity(
            user_id=user_id,
            activity_type='user_logout',
            description=f'User {username} logged out'
        )
    
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
