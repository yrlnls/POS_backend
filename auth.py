from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, create_refresh_token, get_jwt
from models import User, Customer
from app import db
from werkzeug.security import check_password_hash
import secrets
import string

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# In-memory blacklist for demo (use Redis in production)
blacklisted_tokens = set()

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'message': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 409
    
    user = User(
        username=data['username'],
        email=data['email'],
        role=data.get('role', 'customer')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Create customer profile if role is customer
    if user.role == 'customer':
        customer = Customer(
            user_id=user.id,
            name=data.get('name', data['username']),
            email=data['email']
        )
        db.session.add(customer)
        db.session.commit()
    
    return jsonify({
        'message': 'User registered successfully',
        'user_id': user.id
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Invalid username or password'}), 401

    access_token = create_access_token(
        identity=str(user.id), 
        additional_claims={'role': user.role, 'username': user.username}
    )
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'role': user.role,
        'user_id': user.id,
        'username': user.username
    })

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    new_token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role, 'username': user.username}
    )
    
    return jsonify({'access_token': new_token})

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    blacklisted_tokens.add(jti)
    return jsonify({'message': 'Successfully logged out'}), 200

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'message': 'Email required'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # Don't reveal if email exists or not
        return jsonify({'message': 'If email exists, reset instructions have been sent'}), 200
    
    # Generate reset token (in production, send via email)
    reset_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    # Store reset token (in production, use Redis with expiration)
    # For demo, we'll just return it
    return jsonify({
        'message': 'Reset token generated',
        'reset_token': reset_token,  # Remove this in production
        'user_id': user.id  # Remove this in production
    }), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    
    if not data or not all(k in data for k in ('user_id', 'reset_token', 'new_password')):
        return jsonify({'message': 'Missing required fields'}), 400
    
    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'message': 'Invalid reset token'}), 400
    
    # In production, validate reset_token from Redis/database
    user.set_password(data['new_password'])
    db.session.commit()
    
    return jsonify({'message': 'Password reset successfully'}), 200

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

# Check if token is blacklisted
@auth_bp.before_app_request
def check_if_token_revoked():
    pass  # Implement token blacklist checking if needed