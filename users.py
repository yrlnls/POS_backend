from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, db

users_bp = Blueprint('users', __name__)

@users_bp.route('/users', methods=['GET'])
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

@users_bp.route('/users/<int:user_id>', methods=['GET'])
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
