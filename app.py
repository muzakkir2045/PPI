
from flask import Flask, render_template, redirect, request, session, abort, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required,current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, or_
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
    

@app.route('/work_sessions/<int:project_id>')
def work_sessions(project_id):

    sessions = WorkSession.query.filter_by(project_id = project_id).all()
    total_sessions = db.session.query(
        func.count(WorkSession.id)
    ).filter(
        WorkSession.project_id == project_id
    ).scalar() or 0

    total_minutes = db.session.query(
        func.sum(WorkSession.duration_minutes)
    ).filter(
        WorkSession.project_id == project_id
    ).scalar() or 0

    avg_session = (total_minutes/total_sessions if total_sessions > 0 else 0)

    max_session = db.session.query(
        func.max(WorkSession.duration_minutes)
    ).filter(
        WorkSession.project_id == project_id
    ).scalar() or 0

    min_session = db.session.query(
        func.min(WorkSession.duration_minutes)
    ).filter(
        WorkSession.project_id == project_id
    ).scalar() or 0


    outcome_doesnt_exists = db.session.query(
        func.count(WorkSession.id)
    ).filter(
        WorkSession.project_id == project_id, WorkSession.outcome == ''
    ).scalar() or 0

    outcome_exists = total_sessions - outcome_doesnt_exists

    time_without_outcome = db.session.query(
        func.sum(WorkSession.duration_minutes)
    ).filter(
        WorkSession.project_id == project_id, 
        WorkSession.outcome == ''
    ).scalar() or 0

    time_with_outcome = db.session.query(
        func.sum(WorkSession.duration_minutes)
    ).filter(
        WorkSession.project_id == project_id, 
        WorkSession.outcome.isnot(None),
        WorkSession.outcome != ''
    ).scalar() or 0


    long_sessions_with_outcome = (
        db.session.query(func.count(WorkSession.id))
        .filter(
            WorkSession.project_id == project_id,
            WorkSession.duration_minutes > avg_session,
            WorkSession.outcome.isnot(None),
            WorkSession.outcome != ''
        )
        .scalar()
    ) or 0

    long_sessions_without_outcome = (
        db.session.query(func.count(WorkSession.id))
        .filter(
            WorkSession.project_id == project_id,
            WorkSession.duration_minutes > avg_session,
            or_(
                WorkSession.outcome.is_(None),
                WorkSession.outcome == ''
            )
        )
        .scalar()
    ) or 0

    short_sessions_with_outcome = (
        db.session.query(func.count(WorkSession.id))
        .filter(
            WorkSession.project_id == project_id,
            WorkSession.duration_minutes < avg_session,
            WorkSession.outcome.isnot(None),
            WorkSession.outcome != ''
        )
        .scalar()
    ) or 0

    short_sessions_without_outcome = (
        db.session.query(func.count(WorkSession.id))
        .filter(
            WorkSession.project_id == project_id,
            WorkSession.duration_minutes < avg_session,
            or_(
                WorkSession.outcome.is_(None),
                WorkSession.outcome == ''
            )
        )
        .scalar()
    ) or 0

    total_outcome_long = db.session.query(
        func.sum(func.length(WorkSession.outcome))
    ).filter(
        WorkSession.project_id == project_id,
        WorkSession.duration_minutes > avg_session,
        WorkSession.outcome.isnot(None),
        WorkSession.outcome != ''
    ).scalar() or 0

    total_duration_long = db.session.query(
        func.sum(WorkSession.duration_minutes)
    ).filter(
        WorkSession.project_id == project_id,
        WorkSession.duration_minutes > avg_session,
        WorkSession.outcome.isnot(None),
        WorkSession.outcome != ''
    ).scalar() or 0

    outcome_density_long = (
        total_outcome_long / total_duration_long
        if total_duration_long > 0 else 0
    )


    total_outcome_short = db.session.query(
        func.sum(func.length(WorkSession.outcome))
    ).filter(
        WorkSession.project_id == project_id,
        WorkSession.duration_minutes < avg_session,
        WorkSession.outcome.isnot(None),
        WorkSession.outcome != ''
    ).scalar() or 0

    total_duration_short = db.session.query(
        func.sum(WorkSession.duration_minutes)
    ).filter(
        WorkSession.project_id == project_id,
        WorkSession.duration_minutes < avg_session,
        WorkSession.outcome.isnot(None),
        WorkSession.outcome != ''
    ).scalar() or 0

    outcome_density_short = (
        total_outcome_short / total_duration_short
        if total_duration_short > 0 else 0
    )

    if outcome_density_short > outcome_density_long:
        summary_message = "Shorter sessions tend to produce clearer outcomes " \
        "per minute than longer sessions."
        
    elif outcome_density_short < outcome_density_long:
        summary_message = "Longer sessions appear to generate more outcome" \
        " value per minute than shorter ones."
        
    else:
        summary_message = "Session length does not significantly affect outcome quality in this project."
        

    outcome_rate = outcome_exists/total_sessions if total_sessions > 0 else 0
    if outcome_rate >= 0.7:
        reliability_message = "Most sessions produce a recorded outcome. Your work is consistent."
    elif 0.4 <= outcome_rate < 0.7:
        reliability_message = "Outcomes are produced inconsistently. Some sessions may lack clear closure."
    else:
        reliability_message = "Many sessions end without a recorded outcome. This may reduce learning clarity."

    observation_message = None

    if long_sessions_without_outcome > long_sessions_with_outcome:
        observation_message = "Long sessions often end without a concrete outcome."
    elif short_sessions_with_outcome >= short_sessions_without_outcome:
        observation_message = "Short sessions frequently result in clear outcomes."


    if outcome_rate < 0.4:
        recommendation = "Many sessions end without a clear outcome. Make " \
        "it a habit to explicitly record what was achieved at the end of each session."
    else:
        if outcome_density_short > outcome_density_long:
            recommendation = "Try working in shorter, focused sessions and " \
            "explicitly closing each session with a written outcome."
        elif outcome_density_long > outcome_density_short:
            recommendation = "Longer uninterrupted sessions seem to work " \
            "better for this project. Protect time for deep work."
        else:
            recommendation = "Session length appears flexible. Focus on clearly " \
            "defining outcomes regardless of session duration."

    insights = {
        "effectiveness": summary_message,
        "reliability": reliability_message,
        "observation": observation_message,
        "recommendation" : recommendation
    }


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
    project = Projects.query.get(project_id)
    db.session.delete(project)
    db.session.commit()
    return redirect('/dashboard')


        
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)

