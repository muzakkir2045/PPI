
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date

db = SQLAlchemy()


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(250), unique = True, nullable = False)
    password = db.Column(db.String(250), nullable = False)
    created_at = db.Column(db.DateTime, default = datetime.now())

class Projects(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    title = db.Column(db.String(250), nullable = False)
    description = db.Column(db.Text)
    status = db.Column(db.String(100), default = "active")
    sessions = db.relationship(
        'WorkSession',
        backref='project',
        cascade="all, delete-orphan"
    )
    created_at = db.Column(db.DateTime, default = datetime.now())

class WorkSession(db.Model):
    __tablename__ = "work_sessions"
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable = False)

    session_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

    duration_minutes = db.Column(db.Integer, nullable=False)
    work_description = db.Column(db.Text, nullable=False)
    outcome = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.now())