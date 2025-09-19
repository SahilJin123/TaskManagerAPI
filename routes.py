from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
import bcrypt

from extensions import db
from models.users import User
from models.tasks import Task

api_bp = Blueprint('api', __name__)

@api_bp.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "User already registered"}), 409

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created successfully"}), 201

@api_bp.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"message": "User not registered"}), 404
    
    if bcrypt.checkpw(password.encode('utf-8'), user.password):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    
    return jsonify({"message": "Invalid credentials"}), 401

@api_bp.route('/createTask', methods=['POST'])
@jwt_required()
def create_task():
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    if 'title' not in data:
        return jsonify({"message": "Title is a required field"}), 400
    
    if 'completed' in data and not isinstance(data.get('completed'), bool):
        return jsonify({"message": "Input in 'completed' must be a boolean"}), 400

    new_task = Task(title=data['title'], description=data.get('description'),completed=data.get('completed'), user_id=current_user_id)
    db.session.add(new_task)
    db.session.commit()
    return jsonify(new_task.to_dict()), 201

@api_bp.route('/getAllTasks', methods=['GET'])
@jwt_required()
def get_all_tasks():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    status_filter = request.args.get('status')
    current_user_id = get_jwt_identity()
    
    query = Task.query.filter_by(user_id=current_user_id)

    if status_filter:
        if status_filter.lower() == 'completed':
            query = query.filter(Task.completed == True)
        elif status_filter.lower() == 'pending':
            query = query.filter(Task.completed == False)

    tasks = query.order_by(Task.id.asc()).offset((page - 1) * limit).limit(limit).all()
    return jsonify([task.to_dict() for task in tasks]), 200

@api_bp.route('/getTask/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    current_user_id = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=current_user_id).first()

    if not task:
        return jsonify({"message": "Invalid task_id or task not found"}), 404

    return jsonify(task.to_dict()), 200


@api_bp.route('/updateTask/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=current_user_id).first_or_404()

    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    task.completed = data.get('completed', task.completed)
    db.session.commit()
    return jsonify(task.to_dict()), 200

@api_bp.route('/deleteTask/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    current_user_id = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=current_user_id).first_or_404()
        
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted successfully"}), 200
