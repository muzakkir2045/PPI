
from flask import Flask, render_template, redirect, request, session, abort, url_for
from flask_login import LoginManager, login_user, logout_user, login_required,current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
from metrics import insights_analyzer
from models import db, Users, Projects, WorkSession
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "instance"))

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static",
    instance_path=INSTANCE_PATH,
    instance_relative_config=True
)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(INSTANCE_PATH, "database.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'my_secret_key'

db.init_app(app)

# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'login'


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
        description = request.form.get('description','No Description')
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
    

@app.route('/work_sessions/<int:project_id>')
def work_sessions(project_id):
    ( 
        sessions ,
        project_id, 
        total_minutes, 
        total_sessions, 
        avg_session,
        insights,
        outcome_exists ) = insights_analyzer(project_id, db, WorkSession) 

    return render_template('project_sessions.html',
        sessions = sessions, project_id = project_id,
        total_time_spent = total_minutes,
        total_sessions = total_sessions,
        avg_session = avg_session,
        insights = insights,
        outcome_exists = outcome_exists,
        )

@app.route('/projects/<int:project_id>/new_session', methods = ['GET','POST'])
def new_session(project_id):
    if request.method == 'POST':
        session_date = datetime.strptime(
            request.form["session-date"], "%Y-%m-%d"
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
            project_id = project_id,
            session_date = session_date,
            start_time = start_dt,
            end_time = end_dt,
            duration_minutes = duration_minutes,
            work_description = request.form.get('work_description'),
            outcome = request.form.get('outcome')
        )
        db.session.add(project_session)
        db.session.commit()
        return redirect(url_for('work_sessions', project_id = project_id))
    return render_template('new_project_sessions.html', project_id = project_id)

@app.route('/dashboard/view/<int:project_id>')
def view_project(project_id):
    project = Projects.query.get(project_id)
    return render_template('view_project.html',project = project)

@app.route('/dashboard/delete/<int:project_id>')
def delete_project(project_id):
    WorkSession.query.filter_by(project_id=project_id).delete()
    project = Projects.query.get(project_id)
    db.session.delete(project)
    db.session.commit()
    return redirect('/dashboard')


@app.route('/dashboard/edit/<int:project_id>',methods = ['GET','POST'])
def edit_project(project_id):
    project = Projects.query.get_or_404(project_id)
    if request.method == "POST":
        project.title = request.form.get('title')
        project.description = request.form.get('description','No Description')
        project.status = request.form.get('status','active')

        db.session.commit()
        return redirect('/dashboard')
    return render_template('edit_project.html', project = project)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)




