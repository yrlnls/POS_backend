from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User
from app import db

users_bp = Blueprint('users', __name__)

@users_bp.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    current_user = get_jwt_identity()
    # current_user is now a string (user id), so fetch user from DB
    user = User.query.get(int(current_user))
    if not user or user.role != 'admin':
        return jsonify({"msg": "Unauthorized"}), 403
    
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'email': user.email
    } for user in users])

@users_bp.route('/api/users', methods=['POST'])
@jwt_required()
def create_user():
    from flask_jwt_extended import get_jwt
    current_user = get_jwt_identity()
    user = User.query.get(int(current_user))
    if not user or user.role != 'admin':
        return jsonify({"msg": "Unauthorized"}), 403
    
    data = request.get_json()
    
    if not data or not all(k in data for k in ('username', 'email', 'password', 'role')):
        return jsonify({'message': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 409
    
    user = User(
        username=data['username'],
        email=data['email'],
        role=data['role']
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'message': 'User created successfully'
    }), 201

@users_bp.route('/api/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user = get_jwt_identity()
    # current_user is a string (user id), fetch user from DB
    user = User.query.get(int(current_user))
    if not user or (user.role != 'admin' and user.id != user_id):
        return jsonify({"msg": "Unauthorized"}), 403
    
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'email': user.email
    })

@users_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user = get_jwt_identity()
    user = User.query.get(int(current_user))
    if not user or (user.role != 'admin' and user.id != user_id):
        return jsonify({"msg": "Unauthorized"}), 403
    
    target_user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    
    # Update fields if provided
    if 'username' in data:
        existing = User.query.filter(
            User.username == data['username'],
            User.id != user_id
        ).first()
        if existing:
            return jsonify({'message': 'Username already exists'}), 409
        target_user.username = data['username']
    
    if 'email' in data:
        existing = User.query.filter(
            User.email == data['email'],
            User.id != user_id
        ).first()
        if existing:
            return jsonify({'message': 'Email already exists'}), 409
        target_user.email = data['email']
    
    if 'password' in data:
        target_user.set_password(data['password'])
    
    if 'role' in data and user.role == 'admin':
        target_user.role = data['role']
    
    target_user.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'id': target_user.id,
        'username': target_user.username,
        'email': target_user.email,
        'role': target_user.role,
        'message': 'User updated successfully'
    })

@users_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    current_user = get_jwt_identity()
    user = User.query.get(int(current_user))
    if not user or user.role != 'admin':
        return jsonify({"msg": "Unauthorized"}), 403
    
    target_user = User.query.get_or_404(user_id)
    
    # Prevent admin from deleting themselves
    if target_user.id == user.id:
        return jsonify({'message': 'Cannot delete your own account'}), 400
    
    db.session.delete(target_user)
    db.session.commit()
    
    return jsonify({'message': 'User deleted successfully'})
