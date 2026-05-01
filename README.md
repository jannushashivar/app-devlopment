import os
class Config:
    SECRET_KEY = "secret123"
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "jwt-secret"
from flask_sqlalchemy
import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), default="member")  # admin/member

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="pending")
    user_id = db.Column(db.Integer)
    project_id = db.Column(db.Integer)
from flask
import Flask, request, jsonify, render_template
from config
import Config
from models 
import db, User, Project, Task
from flask_jwt_extended
import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from werkzeug.security
import generate_password_hash, check_password_hash
from flask_cors 
import CORS

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
jwt = JWTManager(app)
CORS(app)

# Create DB
with app.app_context():
    db.create_all()

# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    return render_template("login.html")

# SIGNUP
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"msg": "User already exists"}), 400

    hashed_password = generate_password_hash(data["password"])

    user = User(
        username=data["username"],
        password=hashed_password,
        role=data.get("role", "member")
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"msg": "User created successfully"})

# LOGIN
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    user = User.query.filter_by(username=data["username"]).first()

    if user and check_password_hash(user.password, data["password"]):
        token = create_access_token(identity={
            "id": user.id,
            "role": user.role
        })
        return jsonify({"token": token})

    return jsonify({"msg": "Invalid username or password"}), 401

# DASHBOARD PAGE
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# CREATE PROJECT (ADMIN ONLY)
@app.route("/projects", methods=["POST"])
@jwt_required()
def create_project():
    current_user = get_jwt_identity()

    if current_user["role"] != "admin":
        return jsonify({"msg": "Admin access required"}), 403

    data = request.get_json()

    project = Project(name=data["name"])
    db.session.add(project)
    db.session.commit()

    return jsonify({"msg": "Project created"})

# GET PROJECTS
@app.route("/projects", methods=["GET"])
@jwt_required()
def get_projects():
    projects = Project.query.all()
    return jsonify([{"id": p.id, "name": p.name} for p in projects])

# CREATE TASK
@app.route("/tasks", methods=["POST"])
@jwt_required()
def create_task():
    data = request.get_json()

    task = Task(
        title=data["title"],
        user_id=data["user_id"],
        project_id=data["project_id"]
    )

    db.session.add(task)
    db.session.commit()

    return jsonify({"msg": "Task created"})

# GET TASKS
@app.route("/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    tasks = Task.query.all()

    return jsonify([
        {
            "id": t.id,
            "title": t.title,
            "status": t.status
        } for t in tasks
    ])

# UPDATE TASK STATUS
@app.route("/tasks/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    task = Task.query.get(task_id)

    if not task:
        return jsonify({"msg": "Task not found"}), 404

    data = request.get_json()
    task.status = data.get("status", task.status)

    db.session.commit()

    return jsonify({"msg": "Task updated"})

# RUN
if __name__ == "__main__":
    app.run(debug=True)
    <!DOCTYPE html>
<html>
<head>
    <title>Login</title>
</head>
<body>

<h2>Login</h2>

<input id="username" placeholder="Username"><br><br>
<input id="password" type="password" placeholder="Password"><br><br>

<button onclick="login()">Login</button>

<script>
function login() {
    fetch("/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            username: document.getElementById("username").value,
            password: document.getElementById("password").value
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.token) {
            localStorage.setItem("token", data.token);
            window.location.href = "/dashboard";
        } else {
            alert("Login failed");
        }
    });
}
</script>

</body>
</html>
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
</head>
<body>

<h2>Dashboard</h2>

<h3>Create Project (Admin)</h3>
<input id="projectName" placeholder="Project name">
<button onclick="createProject()">Create</button>

<h3>Create Task</h3>
<input id="taskTitle" placeholder="Task title">
<button onclick="createTask()">Create</button>

<h3>Tasks</h3>
<ul id="taskList"></ul>

<script>
const token = localStorage.getItem("token");

function createProject() {
    fetch("/projects", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({
            name: document.getElementById("projectName").value
        })
    }).then(() => alert("Project Created"));
}

function createTask() {
    fetch("/tasks", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({
            title: document.getElementById("taskTitle").value,
            user_id: 1,
            project_id: 1
        })
    }).then(() => loadTasks());
}

function loadTasks() {
    fetch("/tasks", {
        headers: {
            "Authorization": "Bearer " + token
        }
    })
    .then(res => res.json())
    .then(data => {
        const list = document.getElementById("taskList");
        list.innerHTML = "";

        data.forEach(task => {
            const li = document.createElement("li");
            li.innerHTML = `${task.title} - ${task.status}`;
            list.appendChild(li);
        });
    });
}

loadTasks();
</script>

</body>
</html>
body {
    font-family: Arial;
    margin: 20px;
}
