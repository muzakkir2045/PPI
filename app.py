
from flask import Flask, render_template, redirect, request, session, abort, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required,current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'my_secret_key'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.route('/')
def home():
    return render_template('index.html')


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(250), unique = True, nullable = False)
    created_at = db.Column(db.String(250), nullable = False)

class Projects(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    title = db.Column(db.String(250), nullable = False)
    description = db.Column(db.Text, nullable = True)
    status = db.Column(db.String(100), nullbale = False)
    created_at = db.Column(db.String(250), nullable = False)

class Work_Sessions(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable = False)
    session_date = db.Column
    start_time = db.Column
    end_time = db.Column
    duration_minutes = db.Column
    work_descp = db.Column
    outcome = db.Column
    created_at = db.column


@app.route('/dashboard', methods = ['POST','GET'])
def dashboard():

    start = request.form.get('start_time')
    end = request.form.get('end_time')
    op_desired = request.form.get('output_desired')
    op_produced = request.form.get('output_produced')

    format_string = "%Y-%m-%dT%H:%M"
    start = datetime.strptime(start, format_string)
    end = datetime.strptime(end, format_string)

    if op_desired.lower() == op_produced.lower():
        message = "Session was useful"
    else:
        message = "The session was not that growthful"
    diff = end - start
    return f"The session time is {diff} , The Session report is {message}"


@app.route('/output')
def output():
    return None


if __name__ == "__main__":
    app.run(debug=True)






