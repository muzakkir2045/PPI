
from flask import Flask, render_template, redirect, request, session, abort, url_for
from flask_login import LoginManager, login_user, logout_user, login_required,current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
from metrics import insights_analyzer
from models import db, Users, Projects, WorkSession
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "instance"))
os.makedirs(INSTANCE_PATH, exist_ok=True)


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

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/')
def home():
    return redirect('/register')

@app.route('/dashboard', methods = ['POST','GET'])
@login_required
def dashboard():
    projects = Projects.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html' , projects = projects)



@app.route('/new_project', methods = ['GET','POST'])
@login_required
def new_project():
    if request.method == "POST":
        project = Projects(
            title=request.form.get('title'),
            description=request.form.get('description', 'No Description'),
            status=request.form.get('status', 'active'),
            user_id=current_user.id
        )
        db.session.add(project)
        db.session.commit()
        return redirect('/dashboard')
    return render_template('new_project.html')
    

@app.route('/work_sessions/<int:project_id>')
@login_required
def work_sessions(project_id):

    project = Projects.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

    ( 
        sessions ,
        project_id, 
        total_minutes, 
        total_sessions, 
        avg_session,
        insights,
        outcome_exists ) = insights_analyzer(project.id, db, WorkSession) 

    return render_template('project_sessions.html',
        sessions = sessions, project_id = project.id,
        total_time_spent = total_minutes,
        total_sessions = total_sessions,
        avg_session = avg_session,
        insights = insights,
        outcome_exists = outcome_exists,
        )

@app.route('/projects/<int:project_id>/new_session', methods = ['GET','POST'])
@login_required
def new_session(project_id):
    project = Projects.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()

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
            project_id = project.id,
            session_date = session_date,
            start_time = start_dt,
            end_time = end_dt,
            duration_minutes = duration_minutes,
            work_description = request.form.get('work_description'),
            outcome = request.form.get('outcome')
        )
        db.session.add(project_session)
        db.session.commit()
        return redirect(url_for('work_sessions', project_id = project.id))
    return render_template('new_project_sessions.html', project_id = project.id)

@app.route('/dashboard/view/<int:project_id>')
@login_required
def view_project(project_id):
    project = Projects.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first_or_404()
    return render_template('view_project.html',project = project)

@app.route('/dashboard/delete/<int:project_id>', methods = ['POST'])
@login_required
def delete_project(project_id):
    project = Projects.query.filter_by(
        id = project_id,
        user_id = current_user.id
    ).first_or_404()

    db.session.delete(project)
    db.session.commit()
    return redirect('/dashboard')


@app.route('/dashboard/edit/<int:project_id>',methods = ['GET','POST'])
@login_required
def edit_project(project_id):
    project = Projects.query.filter_by(
            id=project_id,
            user_id=current_user.id
        ).first_or_404()


    if request.method == "POST":
        project.title = request.form.get('title')
        project.description = request.form.get('description','No Description')
        project.status = request.form.get('status','active')

        db.session.commit()
        return redirect('/dashboard')
    return render_template('edit_project.html', project = project)


@app.route('/register', methods = ['GET','POST'])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        if Users.query.filter_by(username = username).first():
            return render_template('register.html', error = "Username already taken")
        
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = Users(username = username, password = hashed_password)

        db.session.add(new_user)
        db.session.commit()
        return render_template('login.html')
    return render_template('register.html')


@app.route('/login', methods = ['GET','POST'])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        user = Users.query.filter_by(username = username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error = "Invalid username or password")
    return render_template('login.html')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/seed-test-data")
@login_required
def seed_test_data():

    # Prevent duplicate seed
    existing = Projects.query.filter_by(
        title="Deep Work Engine MVP",
        user_id=current_user.id
    ).first()

    if existing:
        return "Seed project already exists."

    project = Projects(
        title="Deep Work Engine MVP",
        description="Building and refining core MVP analytics system",
        status="active",
        user_id=current_user.id
    )

    db.session.add(project)
    db.session.commit()

    sessions_data = [
        # Day 1
        {
            "date": date.today() - timedelta(days=14),
            "start": (9, 0),
            "end": (10, 5),
            "desc": "Worked on dashboard layout improvements",
            "outcome": "Refactored layout structure and improved spacing consistency."
        },
        # Day 2
        {
            "date": date.today() - timedelta(days=13),
            "start": (20, 0),
            "end": (20, 35),
            "desc": "Session metrics debugging",
            "outcome": "Identified circular import issue in metrics layer."
        },
        # Day 3
        {
            "date": date.today() - timedelta(days=12),
            "start": (8, 30),
            "end": (10, 15),
            "desc": "Improved recommendation logic",
            "outcome": "Adjusted threshold logic for deep vs shallow work detection. Recommendations now vary properly."
        },
        # Day 4
        {
            "date": date.today() - timedelta(days=11),
            "start": (22, 0),
            "end": (22, 25),
            "desc": "Minor bug fixes",
            "outcome": None
        },
        # Day 5
        {
            "date": date.today() - timedelta(days=10),
            "start": (9, 15),
            "end": (11, 0),
            "desc": "Session insight refinement",
            "outcome": "Implemented outcome existence ratio and improved analytical output clarity."
        },
        # Day 6
        {
            "date": date.today() - timedelta(days=8),
            "start": (18, 0),
            "end": (19, 10),
            "desc": "Database restructuring",
            "outcome": "Moved models into dedicated module and stabilized DB initialization."
        },
        # Day 7
        {
            "date": date.today() - timedelta(days=6),
            "start": (7, 45),
            "end": (8, 20),
            "desc": "Quick morning planning session",
            "outcome": "Outlined roadmap for global analytics feature."
        },
        # Day 8
        {
            "date": date.today() - timedelta(days=4),
            "start": (21, 0),
            "end": (22, 45),
            "desc": "Deep analytics experimentation",
            "outcome": "Tested cross-project aggregation queries and validated SQL groupings."
        },
        # Day 9
        {
            "date": date.today() - timedelta(days=2),
            "start": (10, 0),
            "end": (11, 30),
            "desc": "UX adjustments for session view",
            "outcome": "Improved hierarchy and visual spacing in session metrics section."
        },
        # Day 10
        {
            "date": date.today() - timedelta(days=1),
            "start": (19, 30),
            "end": (20, 5),
            "desc": "Short review session",
            "outcome": "Reviewed previous insights and noted pattern of longer productive sessions."
        },
    ]

    for s in sessions_data:
        start_dt = datetime.combine(s["date"], datetime.min.time()) + timedelta(
            hours=s["start"][0],
            minutes=s["start"][1]
        )

        end_dt = datetime.combine(s["date"], datetime.min.time()) + timedelta(
            hours=s["end"][0],
            minutes=s["end"][1]
        )

        duration_minutes = int((end_dt - start_dt).total_seconds() / 60)

        session = WorkSession(
            user_id=current_user.id,
            project_id=project.id,
            session_date=s["date"],
            start_time=start_dt,
            end_time=end_dt,
            duration_minutes=duration_minutes,
            work_description=s["desc"],
            outcome=s["outcome"]
        )

        db.session.add(session)

    db.session.commit()

    return "Realistic seed data created."



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)




