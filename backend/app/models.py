from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

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