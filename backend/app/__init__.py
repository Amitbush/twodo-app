import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from flask_mail import Mail
from prometheus_flask_exporter import PrometheusMetrics
from pythonjsonlogger import jsonlogger

from .models import db, User

def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-456')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 
        'postgresql://localhost/twodo_db'
    ).replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Email Configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'twodoapp.amitorgad@gmail.com'
    app.config['MAIL_PASSWORD'] = 'rwxmiitqzgetuqtr'
    app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

    # Initialize extensions
    db.init_app(app)
    Mail(app)

    login_manager = LoginManager()
    login_manager.login_view = 'routes.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Metrics
    PrometheusMetrics(app)

    # Logging
    logger = logging.getLogger()
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)

    with app.app_context():
        from . import routes
        app.register_blueprint(routes.bp)
        db.create_all()

    return app
