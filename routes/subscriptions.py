from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import Subscription, Customer, ServicePlan
from app import db
from datetime import datetime, timedelta

subscriptions_bp = Blueprint('subscriptions', __name__, url_prefix='/api/subscriptions')

@subscriptions_bp.route('', methods=['POST'])
@jwt_required()
def create_subscription():
    """Create new subscription (sales role required)"""
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'sales']:
        return jsonify({'message': 'Sales access required'}), 403
    
    data = request.get_json()
    
    if not data or not all(k in data for k in ('customer_id', 'plan_id')):
        return jsonify({'message': 'Missing required fields'}), 400
    
    customer = Customer.query.get_or_404(data['customer_id'])
    plan = ServicePlan.query.get_or_404(data['plan_id'])
    
    if not plan.is_active:
        return jsonify({'message': 'Service plan is not active'}), 400
    
    # Check for existing active subscription
    existing = Subscription.query.filter_by(
        customer_id=customer.id,
        status='active'
    ).first()
    
    if existing:
        return jsonify({'message': 'Customer already has an active subscription'}), 400
    
    # Calculate end date (default 30 days)
    duration_days = data.get('duration_days', 30)
    end_date = datetime.utcnow() + timedelta(days=duration_days)
    
    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        end_date=end_date,
        payment_method=data.get('payment_method', 'cash'),
        status='active'
    )
    
    db.session.add(subscription)
    db.session.commit()
    
    return jsonify({
        'id': subscription.id,
        'customer': customer.name,
        'plan': plan.name,
        'status': subscription.status,
        'end_date': subscription.end_date.isoformat()
    }), 201

@subscriptions_bp.route('/<int:subscription_id>', methods=['GET'])
@jwt_required()
def get_subscription(subscription_id):
    """Get specific subscription"""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    
    subscription = Subscription.query.get_or_404(subscription_id)
    
    # Check permissions
    if claims.get('role') == 'customer':
        customer = Customer.query.filter_by(user_id=int(current_user_id)).first()
        if not customer or subscription.customer_id != customer.id:
            return jsonify({'message': 'Unauthorized'}), 403
    
    return jsonify({
        'id': subscription.id,
        'customer_id': subscription.customer_id,
        'customer_name': subscription.customer.name,
        'plan_id': subscription.plan_id,
        'plan_name': subscription.plan.name,
        'plan_price': subscription.plan.price,
        'start_date': subscription.start_date.isoformat(),
        'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
        'status': subscription.status,
        'payment_method': subscription.payment_method
    })

@subscriptions_bp.route('/<int:subscription_id>/status', methods=['PUT'])
@jwt_required()
def update_subscription_status(subscription_id):
    """Update subscription status (tech support)"""
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'tech', 'sales']:
        return jsonify({'message': 'Tech support access required'}), 403
    
    subscription = Subscription.query.get_or_404(subscription_id)
    data = request.get_json()
    
    if not data or 'status' not in data:
        return jsonify({'message': 'Status required'}), 400
    
    valid_statuses = ['active', 'inactive', 'cancelled', 'suspended']
    if data['status'] not in valid_statuses:
        return jsonify({'message': 'Invalid status'}), 400
    
    subscription.status = data['status']
    subscription.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'id': subscription.id,
        'status': subscription.status,
        'message': 'Subscription status updated successfully'
    })

@subscriptions_bp.route('/customer/<int:customer_id>', methods=['GET'])
@jwt_required()
def get_customer_subscriptions(customer_id):
    """Get all subscriptions for a customer"""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    
    # Check permissions
    if claims.get('role') == 'customer':
        customer = Customer.query.filter_by(user_id=int(current_user_id)).first()
        if not customer or customer.id != customer_id:
            return jsonify({'message': 'Unauthorized'}), 403
    
    customer = Customer.query.get_or_404(customer_id)
    subscriptions = Subscription.query.filter_by(customer_id=customer_id).all()
    
    return jsonify([{
        'id': sub.id,
        'plan_name': sub.plan.name,
        'plan_price': sub.plan.price,
        'start_date': sub.start_date.isoformat(),
        'end_date': sub.end_date.isoformat() if sub.end_date else None,
        'status': sub.status,
        'payment_method': sub.payment_method
    } for sub in subscriptions])

@subscriptions_bp.route('', methods=['GET'])
@jwt_required()
def get_all_subscriptions():
    """Get all subscriptions (admin/sales only)"""
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'sales', 'tech']:
        return jsonify({'message': 'Unauthorized'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = Subscription.query
    if status:
        query = query.filter_by(status=status)
    
    subscriptions = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'subscriptions': [{
            'id': sub.id,
            'customer_name': sub.customer.name,
            'plan_name': sub.plan.name,
            'status': sub.status,
            'start_date': sub.start_date.isoformat(),
            'end_date': sub.end_date.isoformat() if sub.end_date else None
        } for sub in subscriptions.items],
        'total': subscriptions.total,
        'pages': subscriptions.pages,
        'current_page': page
    })