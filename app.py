
from flask import Flask, render_template, redirect, request, session, abort, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required,current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Date, Time, DateTime
from datetime import datetime, timedelta

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'my_secret_key'

db = SQLAlchemy(app)

# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'login'


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


@app.route('/')
def home():
    return redirect('/dashboard')

@app.route('/dashboard', methods = ['POST','GET'])
def dashboard():
    projects = Projects.query.all()
    return render_template('dashboard.html' , projects = projects)



@app.route('/new_project', methods = ['GET','POST'])
def new_project():
    if request.method == "POST":
        title = request.form.get('title')
        description = request.form.get('description','Description Not Added')
        status = request.form.get('status','active')


        project = Projects(
            title = title,
            description = description,
            status = status
        )
        db.session.add(project)
        db.session.commit()
        return redirect('/dashboard')
    return render_template('new_project.html')
    

@app.route('/work_sessions/<int:id>')
def work_sessions(id):
    sessions = WorkSession.query.filter_by(project_id = id).all()
    return render_template('project_sessions.html', sessions = sessions)


@app.route('/new_session', methods = ['GET','POST'])
def new_session():
    if request.method == 'POST':
        session_date = datetime.strptime(
            request.form["session_date"], "%Y-%m-%d"
        ).date()

        start_t = datetime.strptime(
            request.form["start_time"], "%H:%M"
        ).time()

        end_t = datetime.strptime(
            request.form["end_time"], "%H:%M"
        ).time()


        start_dt = datetime.combine(session_date, start_t)
        end_dt   = datetime.combine(session_date, end_t)

        if end_dt <= start_dt:
            end_dt += timedelta(days=1)

        duration_minutes = int(
            (end_dt - start_dt).total_seconds() / 60
        )
        project_session = WorkSession(
            session_date = session_date,
            start_time = start_dt,
            end_time = end_dt,
            duration_minutes = duration_minutes,
            work_description = request.form.get('work_description'),
            outcome = request.form.get('outcome')
        )
        db.session.add(project_session)
        db.session.commit()
        return redirect('/work_sessions/<int:id>')
    return render_template('new_project_sessions.html')

        
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)






