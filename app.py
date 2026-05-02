from flask import Flask, request, jsonify, render_template
import config
import models
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(config.Config)

models.db.init_app(app)
jwt = JWTManager(app)
CORS(app)

# Create DB
with app.app_context():
    models.db.create_all()

# HOME
@app.route("/")
def home():
    return render_template("login.html")

# SIGNUP
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    if models.User.query.filter_by(username=data["username"]).first():
        return jsonify({"msg": "User already exists"}), 400

    user = models.User(
        username=data["username"],
        password=generate_password_hash(data["password"]),
        role=data.get("role", "member")
    )

    models.db.session.add(user)
    models.db.session.commit()

    return jsonify({"msg": "User created"})

# LOGIN
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    user = models.User.query.filter_by(username=data["username"]).first()

    if user and check_password_hash(user.password, data["password"]):
        token = create_access_token(identity={
            "id": user.id,
            "role": user.role
        })
        return jsonify({"token": token})

    return jsonify({"msg": "Invalid credentials"}), 401

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# CREATE PROJECT (ADMIN)
@app.route("/projects", methods=["POST"])
@jwt_required()
def create_project():
    current_user = get_jwt_identity()

    if current_user["role"] != "admin":
        return jsonify({"msg": "Admin only"}), 403

    data = request.get_json()

    project = models.Project(name=data["name"])
    models.db.session.add(project)
    models.db.session.commit()

    return jsonify({"msg": "Project created"})

# GET PROJECTS
@app.route("/projects", methods=["GET"])
@jwt_required()
def get_projects():
    projects = models.Project.query.all()
    return jsonify([{"id": p.id, "name": p.name} for p in projects])

# CREATE TASK
@app.route("/tasks", methods=["POST"])
@jwt_required()
def create_task():
    data = request.get_json()

    task = models.Task(
        title=data["title"],
        user_id=data["user_id"],
        project_id=data["project_id"]
    )

    models.db.session.add(task)
    models.db.session.commit()

    return jsonify({"msg": "Task created"})

# GET TASKS
@app.route("/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    tasks = models.Task.query.all()

    return jsonify([
        {"id": t.id, "title": t.title, "status": t.status}
        for t in tasks
    ])

# UPDATE TASK
@app.route("/tasks/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    task = models.Task.query.get(task_id)

    if not task:
        return jsonify({"msg": "Not found"}), 404

    data = request.get_json()
    task.status = data.get("status", task.status)

    models.db.session.commit()

    return jsonify({"msg": "Updated"})

# RUN
if __name__ == "__main__":
    app.run(debug=True)