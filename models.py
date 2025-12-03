from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    verification_photo = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    name = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    contact_number = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    institute_name = db.Column(db.String(255), nullable=True)
    college_name = db.Column(db.String(255), nullable=True)
    degree = db.Column(db.String(200), nullable=True)
    year_of_passing = db.Column(db.String(50), nullable=True)
    resume_url = db.Column(db.Text, nullable=True)
    
    responses = db.relationship('ExamResponse', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    question_type = db.Column(db.String(20), nullable=False, default='MCQ')
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=True)
    option_b = db.Column(db.String(255), nullable=True)
    option_c = db.Column(db.String(255), nullable=True)
    option_d = db.Column(db.String(255), nullable=True)
    correct_answer = db.Column(db.String(1), nullable=True)
    correct_answer_text = db.Column(db.Text, nullable=True)
    points = db.Column(db.Integer, default=1)
    
    responses = db.relationship('ExamResponse', backref='question', lazy=True, cascade='all, delete-orphan')

class ExamResponse(db.Model):
    __tablename__ = 'exam_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    user_answer = db.Column(db.String(1), nullable=True)
    user_answer_text = db.Column(db.Text, nullable=True)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    points_earned = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class AdminSettings(db.Model):
    __tablename__ = 'admin_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.String(255), nullable=False)

class ProctorEvent(db.Model):
    __tablename__ = 'proctor_events'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    event_details = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), nullable=False, default='warning')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('proctor_events', lazy=True))

class AdminSecret(db.Model):
    __tablename__ = 'admin_secrets'
    
    id = db.Column(db.Integer, primary_key=True)
    secret_key = db.Column(db.String(100), unique=True, nullable=False)
    encrypted_value = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    activity_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('activities', lazy=True))
