from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate

import os
import sys
import shutil

def get_db_path():
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        db_path = os.path.join(exe_dir, "db.sqlite")

        # If DB doesn't exist next to exe, copy it from bundled temp folder
        if not os.path.exists(db_path):
            bundled_db = os.path.join(sys._MEIPASS, "db.sqlite")
            if os.path.exists(bundled_db):
                shutil.copy(bundled_db, db_path)

        return db_path

    else:
        # Normal run
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), "db.sqlite")

# Initialize Flask
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{get_db_path()}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "supersecretkey"

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

migrate = Migrate(app, db)

# User model
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)

# Task model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text)
    course = db.Column(db.String(250))
    due_date = db.Column(db.Date, nullable=False)
    priority = db.Column(db.String(50))
    status = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

# Suggestion model
class Suggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task = db.relationship('Task', backref=db.backref('suggestions', cascade="all, delete-orphan"))
    category = db.Column(db.String, nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = Users.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))
        return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

# Registration
@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if Users.query.filter_by(username=username).first():
            return render_template("sign_up.html", error="Username already exists")
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = Users(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("sign_up.html")

# Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# Home page
@app.route("/home")
@login_required
def home():
    #Define tasks
    tasks = Task.query.filter_by(user_id=current_user.id).all()

    #Define the information from tasks that are on the task box in the calendar
    tasks_data = [
    {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "course": task.course,
        "due_date": task.due_date.isoformat() if task.due_date else "",
        "status": task.status,
        "priority": task.priority
    }
    for task in tasks
    ]

    #Save time-based suggestions
    time_suggestions = []

    #Generate dynamic suggestions
    for task in tasks:
        #Time-based suggestion
        if task.due_date and task.status != "Completed":
            today = date.today()
            days_remaining = (task.due_date - today).days

            if days_remaining == 1:
                time_suggestions.append({"task_id": task.id, "text": f"{task.name} is due Tomorrow!"})
            elif days_remaining == 0:
                time_suggestions.append({"task_id": task.id, "text": f"{task.name} is due Today!"})
            elif days_remaining < 0:
                time_suggestions.append({"task_id": task.id, "text": f"{task.name} is overdue!"})

    #Only receive suggestions for tasks that are not completed
    suggestions = Suggestion.query.join(Task).filter(
        Task.user_id == current_user.id,
        Task.status != "Completed"
    ).all()

    return render_template("index.html", tasks=tasks_data, time_suggestions=time_suggestions)

#Updating the tasks on the calendar
@app.route("/update_task_status/<int:task_id>", methods=["POST"])
@login_required
def update_task_status(task_id):
    task = Task.query.get(task_id)
    if task and task.user_id == current_user.id:
        data = request.get_json()
        task.status = data.get("status", task.status)
        db.session.commit()
        return {"success": True}
    return {"success": False}, 400

# Task list page
@app.route("/task_list")
@login_required
def task_list():
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.due_date).all()
    return render_template("task_list.html", tasks=tasks)

# Add task
@app.route("/add", methods=["GET", "POST"])
@login_required
def add_task():
    if request.method == "POST":
        task_name = request.form.get("task_name")
        task_desc = request.form.get("task_desc")
        task_course = request.form.get("task_course")
        task_date_str = request.form.get("task_date")
        task_priority = request.form.get("task_priority")
        task_status = request.form.get("task_status")
        if task_name and task_date_str:
            task_date = datetime.strptime(task_date_str, "%Y-%m-%d").date()
            new_task = Task(
                name=task_name,
                description=task_desc,
                course=task_course,
                due_date=task_date,
                priority=task_priority,
                status=task_status,
                user_id=current_user.id)
            db.session.add(new_task)
            db.session.commit()
            generate_suggestion(new_task)

        return redirect(url_for("task_list"))
    return render_template("add_task.html")

#Edit task
@app.route("/edit_task/<int:task_id>", methods=["POST"])
def edit_task(task_id):
    data = request.get_json()
    task = Task.query.get(task_id)

    if task:
        task.name = data.get("name", task.name)
        task.description = data.get("description", task.description)
        task.course = data.get("course", task.course)
        due_date_str = data.get("due_date")
        if due_date_str:
            try:
                task.due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            except ValueError:
                print("Invalid date format:", due_date_str)
        task.priority = data.get("priority", task.priority)
        task.status = data.get("status", task.status)
        db.session.commit()
        
    return redirect(url_for("task_list"))

# Delete task
@app.route("/delete/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if task:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for("task_list"))

# Suggestions
def generate_suggestion(task):
    task_lowercase = task.name.lower()
    description_lowercase = task.description.lower()
    suggestions_to_add = []
    category = "general"

    #Generate study suggestions for tests
    if "test" in task_lowercase or "exam" in task_lowercase:
        suggestions_to_add.append(f"Study and practice for the {task.name}")
        category = "study"
    #Generate review suggestions for tests
    elif "quiz" in task_lowercase:
        suggestions_to_add.append(f"Review material for the {task.name}")
        category = "study"
    #Generate suggestions to break down work
    elif "essay" in task_lowercase or "project" in task_lowercase:
        suggestions_to_add.append(f"Break down {task.name} into multiple work sessions")
        category = "project"
    #Generate suggestions for group projects
    elif "group" in task_lowercase or "group" in description_lowercase or "team" in task_lowercase or "team" in description_lowercase:
        suggestions_to_add.append(f"For {task.name}, meet up with your group members outside of class. Try and aim for at least once a week")
        category = "project"
    #Generate suggestions for reliable research
    elif "research" in task_lowercase or "research" in description_lowercase or "paper" in task_lowercase or "paper" in description_lowercase:
        suggestions_to_add.append(f"The 'Research' tab can help you find peer-reviewed papers and/or articles for {task.name}")
        category = "research"
    #Generate suggestions for reliable research
    elif "dataset" in task_lowercase or "dataset" in description_lowercase:
        suggestions_to_add.append(f"The 'Research' tab can help you find reliable soures containing real datasets for {task.name}")
        category = "research"
    #Generate suggestions to pace oneself
    elif "final" in task_lowercase:
        suggestions_to_add.append(f"Make sure to pace yourself when working towards the {task.name}")
        category = "study"

    # Add suggestions to the database
    for text in suggestions_to_add:
        suggestion = Suggestion(text=text, task_id=task.id, user_id=task.user_id, category=category)
        db.session.add(suggestion)
    db.session.commit()

@app.route("/update_status/<int:task_id>", methods=["POST"])
@login_required
def update_status(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    task.status = request.form['status']
    db.session.commit()
        
    if task.status == "Completed":
        Suggestion.query.filter_by(task_id=task.id).delete()
        db.session.commit()
    return redirect(url_for("task_list"))

@app.route("/research")
@login_required
def research_assistance():
    return render_template("research.html")

@app.route("/help")
@login_required
def help_section():
    return render_template("help.html")

@app.route("/suggestions")
@login_required
def general_suggestions():
    #Define tasks
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    today = date.today()

    #Track all overdue tasks
    overdue_task_ids = set()

    #Remove suggestions for overdue tasks
    for task in tasks:
        if task.due_date and task.status != "Completed":
            days_remaining = (task.due_date - today).days
            if days_remaining < 0:
                Suggestion.query.filter_by(task_id=task.id, user_id=current_user.id).delete()
                overdue_task_ids.add(task.id)
    db.session.commit()

    #Get all suggestions linked to the user's tasks
    suggestions = Suggestion.query.join(Task).filter(
        Task.user_id == current_user.id,
        Task.status != "Completed"
    ).all()

    # Ensure every DB suggestion has a category
    for s in suggestions:
        s.category = s.category or "general"

    # Add priority suggestions separately
    priority_suggestions = []

    #High priority suggestions if task is not started
    for task in tasks:
        task_lower = task.name.lower()
        if task.priority == 'High' and task.status == 'Not Started' and \
        task.id not in overdue_task_ids and \
        ("test" not in task_lower and "exam" not in task_lower and "quiz" not in task_lower):
            priority_suggestions.append({
            "text": f"Start working on {task.name} as soon as possible",
            "category": "priority"
            })
        elif task.priority == 'High' and task.status == 'In Progress' and \
        task.id not in overdue_task_ids and \
        ("test" not in task_lower and "exam" not in task_lower and "quiz" not in task_lower):
            priority_suggestions.append({
            "text": f"Focus on completing {task.name}",
            "category": "priority"
            })
    
    # Group everything
    grouped = {
    "study": [s for s in suggestions if s.category == "study"],
    "project": [s for s in suggestions if s.category == "project"],
    "research": [s for s in suggestions if s.category == "research"],
    "priority": [s for s in suggestions if s.category == "priority"],
    "general": [s for s in suggestions if s.category == "general"],
    }

    # add priority list manually
    grouped["priority"].extend(priority_suggestions)

    return render_template("suggestions.html", grouped=grouped)

if __name__ == "__main__":
    app.run(debug=True)