import logging
from flask import request, jsonify, Blueprint
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message

from .models import db, User, Couple, Task
from . import Mail

logger = logging.getLogger(__name__)

bp = Blueprint('routes', __name__)

def send_assignment_email(task_content, assignee, recipient_email):
    try:
        mail = Mail()
        msg = Message(
            subject="New Goal in TwoDo! 🚀",
            recipients=[recipient_email],
            body=f"Hi!\n\nA new task was added to TwoDo: '{task_content}'\nResponsibility: {assignee}\n\nCheck it out and let's get it done! ✨"
        )
        mail.send(msg)
        logger.info(f"Email sent to {recipient_email}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

@bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_pw = generate_password_hash(data['password'])
    couple_name = data['couple_name']
    
    couple = Couple.query.filter_by(name=couple_name).first()
    if not couple:
        couple = Couple(name=couple_name)
        db.session.add(couple)
        db.session.flush()
    
    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=hashed_pw,
        couple_id=couple.id
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        login_user(user)
        return jsonify({'message': 'Logged in successfully'}), 200
    return jsonify({'message': 'Invalid username or password'}), 401

@bp.route('/api/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

@bp.route('/api/tasks', methods=['GET'])
@login_required
def get_tasks():
    tasks = Task.query.filter_by(couple_id=current_user.couple_id).all()
    tasks_data = [{
        'id': task.id,
        'content': task.content,
        'category': task.category,
        'deadline': task.deadline,
        'status': task.status,
        'assigned_to': task.assigned_to
    } for task in tasks]
    return jsonify(tasks_data), 200

@bp.route('/api/tasks', methods=['POST'])
@login_required
def add_task():
    data = request.get_json()
    content = data.get('task')
    
    if content:
        new_task = Task(
            content=content, 
            category=data.get('category'), 
            deadline=data.get('deadline'), 
            assigned_to=data.get('assigned_to', 'Both'),
            couple_id=current_user.couple_id
        )
        db.session.add(new_task)
        db.session.commit()
        
        partner = User.query.filter(
            User.couple_id == current_user.couple_id,
            User.id != current_user.id
        ).first()
        
        if partner and data.get('assigned_to') in ['Partner', 'Both']:
            send_assignment_email(content, data.get('assigned_to'), partner.email)
            
        return jsonify({'message': 'Task added successfully'}), 201
    return jsonify({'message': 'Task content is required'}), 400

@bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task_status(task_id):
    data = request.get_json()
    new_status = data.get('status')
    task = Task.query.get(task_id)
    if task and task.couple_id == current_user.couple_id:
        task.status = new_status
        db.session.commit()
        return jsonify({'message': 'Task status updated successfully'}), 200
    return jsonify({'message': 'Task not found or unauthorized'}), 404

@bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task and task.couple_id == current_user.couple_id:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully'}), 200
    return jsonify({'message': 'Task not found or unauthorized'}), 404
