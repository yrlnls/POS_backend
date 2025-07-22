from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from models import ServicePlan
from app import db
from datetime import datetime

service_plans_bp = Blueprint('service_plans', __name__, url_prefix='/api/plans')

@service_plans_bp.route('', methods=['GET'])
def get_service_plans():
    """Get all service plans (public endpoint)"""
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    
    query = ServicePlan.query
    if active_only:
        query = query.filter_by(is_active=True)
    
    plans = query.all()
    
    return jsonify([{
        'id': plan.id,
        'name': plan.name,
        'description': plan.description,
        'speed': plan.speed,
        'data_cap': plan.data_cap,
        'price': plan.price,
        'is_active': plan.is_active
    } for plan in plans])

@service_plans_bp.route('', methods=['POST'])
@jwt_required()
def create_service_plan():
    """Create new service plan (admin only)"""
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    data = request.get_json()
    
    if not data or not all(k in data for k in ('name', 'speed', 'price')):
        return jsonify({'message': 'Missing required fields'}), 400
    
    plan = ServicePlan(
        name=data['name'],
        description=data.get('description'),
        speed=data['speed'],
        data_cap=data.get('data_cap'),
        price=float(data['price']),
        is_active=data.get('is_active', True)
    )
    
    db.session.add(plan)
    db.session.commit()
    
    return jsonify({
        'id': plan.id,
        'name': plan.name,
        'message': 'Service plan created successfully'
    }), 201

@service_plans_bp.route('/<int:plan_id>', methods=['GET'])
def get_service_plan(plan_id):
    """Get specific service plan"""
    plan = ServicePlan.query.get_or_404(plan_id)
    
    return jsonify({
        'id': plan.id,
        'name': plan.name,
        'description': plan.description,
        'speed': plan.speed,
        'data_cap': plan.data_cap,
        'price': plan.price,
        'is_active': plan.is_active,
        'created_at': plan.created_at.isoformat(),
        'updated_at': plan.updated_at.isoformat()
    })

@service_plans_bp.route('/<int:plan_id>', methods=['PUT'])
@jwt_required()
def update_service_plan(plan_id):
    """Update service plan (admin only)"""
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    plan = ServicePlan.query.get_or_404(plan_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    
    # Update fields if provided
    if 'name' in data:
        plan.name = data['name']
    if 'description' in data:
        plan.description = data['description']
    if 'speed' in data:
        plan.speed = data['speed']
    if 'data_cap' in data:
        plan.data_cap = data['data_cap']
    if 'price' in data:
        plan.price = float(data['price'])
    if 'is_active' in data:
        plan.is_active = data['is_active']
    
    plan.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'id': plan.id,
        'message': 'Service plan updated successfully'
    })

@service_plans_bp.route('/<int:plan_id>', methods=['DELETE'])
@jwt_required()
def delete_service_plan(plan_id):
    """Delete service plan (admin only)"""
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    plan = ServicePlan.query.get_or_404(plan_id)
    
    # Check if plan has active subscriptions
    if plan.subscriptions:
        active_subs = [sub for sub in plan.subscriptions if sub.status == 'active']
        if active_subs:
            return jsonify({
                'message': 'Cannot delete plan with active subscriptions',
                'active_subscriptions': len(active_subs)
            }), 400
    
    db.session.delete(plan)
    db.session.commit()
    
    return jsonify({'message': 'Service plan deleted successfully'})