
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required,current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date

db = SQLAlchemy()


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(250), unique = True, nullable = False)
    created_at = db.Column(db.DateTime, default = datetime.now())

class Projects(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    # user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    title = db.Column(db.String(250), nullable = False)
    description = db.Column(db.Text)
    status = db.Column(db.String(100), default = "active")
    created_at = db.Column(db.DateTime, default = datetime.now())

class WorkSession(db.Model):
    __tablename__ = "work_sessions"
    id = db.Column(db.Integer, primary_key = True)
    # user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable = False)

    session_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

    duration_minutes = db.Column(db.Integer, nullable=False)
    work_description = db.Column(db.Text, nullable=False)
    outcome = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.now())