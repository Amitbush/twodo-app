import os
import logging
from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from prometheus_flask_exporter import PrometheusMetrics
from pythonjsonlogger import jsonlogger
from flask_mail import Mail, Message

# --- 1. לוגים ---
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-456')

# --- 2. הגדרת PostgreSQL דינמית וחסינה ---
# השורה הזו מנסה לקרוא DATABASE_URL (למשל בדוקר או בענן).
# אם לא נמצא, היא מתחברת ל-PostgreSQL המקומי במק (ללא סיסמה כברירת מחדל).
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'postgresql://localhost/twodo_db'
).replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- הגדרות אימייל עבור TwoDo (Gmail) ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'twodoapp.amitorgad@gmail.com'
app.config['MAIL_PASSWORD'] = 'rwxmiitqzgetuqtr'
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

db = SQLAlchemy(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# --- 3. מודלים ---
class Couple(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    users = db.relationship('User', backref='couple', lazy=True)
    tasks = db.relationship('Task', backref='couple', lazy=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    couple_id = db.Column(db.Integer, db.ForeignKey('couple.id'))

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default='General') 
    deadline = db.Column(db.String(50)) 
    status = db.Column(db.String(20), default='Pending') 
    assigned_to = db.Column(db.String(80), default='Both')
    couple_id = db.Column(db.Integer, db.ForeignKey('couple.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

metrics = PrometheusMetrics(app)

# --- פונקציית עזר לשליחת אימייל ממותגת TwoDo ---
def send_assignment_email(task_content, assignee, recipient_email):
    try:
        msg = Message(
            subject="New Goal in TwoDo! 🚀",
            recipients=[recipient_email],
            body=f"Hi!\n\nA new task was added to TwoDo: '{task_content}'\nResponsibility: {assignee}\n\nCheck it out and let's get it done! ✨"
        )
        mail.send(msg)
        logger.info(f"Email sent to {recipient_email}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

# --- 4. Routes ---

@app.route('/')
@login_required
def index():
    tasks = Task.query.filter_by(couple_id=current_user.couple_id).all()
    return render_template('index.html', tasks=tasks)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password_hash, request.form.get('password')):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form.get('password'))
        couple_name = request.form.get('couple_name')
        
        couple = Couple.query.filter_by(name=couple_name).first()
        if not couple:
            couple = Couple(name=couple_name)
            db.session.add(couple)
            db.session.flush()
        
        new_user = User(
            username=request.form.get('username'),
            email=request.form.get('email'),
            password_hash=hashed_pw,
            couple_id=couple.id
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/add', methods=['POST'])
@login_required
def add_task():
    content = request.form.get('task')
    category = request.form.get('category')
    deadline = request.form.get('deadline')
    assigned_to = request.form.get('assigned_to', 'Both')
    
    if content:
        new_task = Task(
            content=content, 
            category=category, 
            deadline=deadline, 
            assigned_to=assigned_to,
            couple_id=current_user.couple_id
        )
        db.session.add(new_task)
        db.session.commit()
        
        partner = User.query.filter(
            User.couple_id == current_user.couple_id,
            User.id != current_user.id
        ).first()
        
        if partner and assigned_to in ['Partner', 'Both']:
            send_assignment_email(content, assigned_to, partner.email)
        
    return redirect(url_for('index'))

@app.route('/update_status/<int:task_id>/<string:new_status>')
@login_required
def update_status(task_id, new_status):
    task = Task.query.get(task_id)
    if task and task.couple_id == current_user.couple_id:
        task.status = new_status
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
@login_required
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task and task.couple_id == current_user.couple_id:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)