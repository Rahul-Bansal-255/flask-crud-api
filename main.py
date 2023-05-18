import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__) + '/database.db')
db = SQLAlchemy(app)

app.config["JWT_SECRET_KEY"] = "super-secret" 
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(30), unique = True, nullable = False)
    password = db.Column(db.String(1000), nullable = False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(30), nullable = False)
    description = db.Column(db.String(1000), nullable = True)
    status = db.Column(db.Boolean, default = True)
    user = db.Column(db.String(30), db.ForeignKey("user.username"))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "user": self.user
        }

@app.get("/")
@app.get("/home")
def home():
    return "simple api"

@app.post("/signup")
def signup():
    data = request.get_json()
    print(data)
    if data.get('username') == None or data.get('password') == None:
        response = app.response_class(
            status = 400
        )
        return response
    
    user = User(
        username = data['username'],
        password = data['password']
    )
    db.session.add(user)
    db.session.commit()
    response = app.response_class(
        status = 200
    )
    return response

@app.post("/signin")
def signin():
    data = request.get_json()
    
    if data.get('username') == None or data.get('password') == None:
        response = app.response_class(
            status = 400
        )
        return response
    
    user = User.query.filter_by(username = data.get('username'), password = data.get('password')).first()
    if user == None:
        response = app.response_class(
            status = 400
        )
        return response
    
    access_token = create_access_token(identity=data.get('username'))
    return jsonify(access_token=access_token)

@app.get("/tasks")
@jwt_required()
def get_tasks():
    current_user = get_jwt_identity()
    tasks = Task.query.filter_by(user = current_user)
    tasks = [t.to_dict() for t in tasks]
    return jsonify(tasks)

@app.post("/tasks")
@jwt_required()
def add_task():
    current_user = get_jwt_identity()
    data = request.get_json()

    if data.get('title') == None:
        response = app.response_class(
            status = 400
        )
        return response
    
    task = Task(
        title = data.get('title'),
        description = data.get('description'),
        user = current_user
    )
    db.session.add(task)
    db.session.commit()
    
    response = app.response_class(
        status = 200
    )
    return response

@app.patch("/tasks")
@jwt_required()
def update_task():
    current_user = get_jwt_identity()
    data = request.get_json()

    if data.get('task_id') == None:
        response = app.response_class(
            status = 400
        )
        return response
    
    task = Task.query.get_or_404(data.get('task_id')).to_dict()
    if task['user'] != current_user:
        response = app.response_class(
            status = 400
        )
        return response
    
    task = Task.query.get(data.get('task_id'))
    task.status = False
    db.session.commit()
    
    response = app.response_class(
        status = 200
    )
    return response

@app.delete("/tasks")
@jwt_required()
def delete_task():
    current_user = get_jwt_identity()
    data = request.get_json()

    if data.get('task_id') == None:
        response = app.response_class(
            status = 400
        )
        return response
    
    task = Task.query.get_or_404(data.get('task_id')).to_dict()
    if task['user'] != current_user:
        response = app.response_class(
            status = 400
        )
        return response
    
    task = Task.query.get_or_404(data.get('task_id'))
    db.session.delete(task)
    db.session.commit()
    
    response = app.response_class(
        status = 200
    )
    return response


if __name__=="__main__":
    
    with app.app_context():
        db.create_all()
        app.debug=True
        app.run()