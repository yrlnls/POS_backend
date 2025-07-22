from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Customer, ServicePlan, Subscription, User
from app import db
from datetime import datetime, timedelta

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/api/customers', methods=['GET'])
@jwt_required()
def get_customers():
    from flask_jwt_extended import get_jwt
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'sales', 'tech']:
        return jsonify({"msg": "Unauthorized"}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    
    query = Customer.query
    if search:
        query = query.filter(
            Customer.name.contains(search) | 
            Customer.email.contains(search)
        )
    
    customers = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify([{
        'id': customer.id,
        'name': customer.name,
        'email': customer.email,
        'phone': customer.phone,
        'billing_address': customer.billing_address,
        'service_address': customer.service_address,
        'created_at': customer.created_at.isoformat()
    } for customer in customers.items])

@customers_bp.route('/api/customers', methods=['POST'])
@jwt_required()
def create_customer():
    from flask_jwt_extended import get_jwt
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'sales']:
        return jsonify({"msg": "Unauthorized"}), 403
    
    data = request.get_json()
    
    if not data or not all(k in data for k in ('name', 'email')):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Check if email already exists
    existing = Customer.query.filter_by(email=data['email']).first()
    if existing:
        return jsonify({'message': 'Customer with this email already exists'}), 409
    
    customer = Customer(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone'),
        personal_info=data.get('personal_info'),
        contact_info=data.get('contact_info'),
        billing_address=data.get('billing_address'),
        service_address=data.get('service_address')
    )
    db.session.add(customer)
    db.session.commit()
    
    return jsonify({
        'id': customer.id,
        'name': customer.name,
        'email': customer.email,
        'message': 'Customer created successfully'
    }), 201

@customers_bp.route('/api/customers/<int:customer_id>', methods=['GET'])
@jwt_required()
def get_customer(customer_id):
    from flask_jwt_extended import get_jwt
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    
    # Check permissions
    if claims.get('role') == 'customer':
        customer = Customer.query.filter_by(user_id=int(current_user_id)).first()
        if not customer or customer.id != customer_id:
            return jsonify({'message': 'Unauthorized'}), 403
    elif claims.get('role') not in ['admin', 'sales', 'tech']:
        return jsonify({'message': 'Unauthorized'}), 403
    
    customer = Customer.query.get_or_404(customer_id)
    
    return jsonify({
        'id': customer.id,
        'name': customer.name,
        'email': customer.email,
        'phone': customer.phone,
        'personal_info': customer.personal_info,
        'contact_info': customer.contact_info,
        'billing_address': customer.billing_address,
        'service_address': customer.service_address,
        'created_at': customer.created_at.isoformat(),
        'updated_at': customer.updated_at.isoformat()
    })

@customers_bp.route('/api/customers/<int:customer_id>', methods=['PUT'])
@jwt_required()
def update_customer(customer_id):
    from flask_jwt_extended import get_jwt
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    
    # Check permissions
    if claims.get('role') == 'customer':
        customer = Customer.query.filter_by(user_id=int(current_user_id)).first()
        if not customer or customer.id != customer_id:
            return jsonify({'message': 'Unauthorized'}), 403
    elif claims.get('role') not in ['admin', 'sales']:
        return jsonify({'message': 'Unauthorized'}), 403
    
    customer = Customer.query.get_or_404(customer_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    
    # Update fields if provided
    if 'name' in data:
        customer.name = data['name']
    if 'email' in data:
        # Check if new email already exists
        existing = Customer.query.filter(
            Customer.email == data['email'],
            Customer.id != customer_id
        ).first()
        if existing:
            return jsonify({'message': 'Email already exists'}), 409
        customer.email = data['email']
    if 'phone' in data:
        customer.phone = data['phone']
    if 'personal_info' in data:
        customer.personal_info = data['personal_info']
    if 'contact_info' in data:
        customer.contact_info = data['contact_info']
    if 'billing_address' in data:
        customer.billing_address = data['billing_address']
    if 'service_address' in data:
        customer.service_address = data['service_address']
    
    customer.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'id': customer.id,
        'message': 'Customer updated successfully'
    })

@customers_bp.route('/api/customers/<int:customer_id>/subscriptions', methods=['GET'])
@jwt_required()
def get_customer_subscriptions_route(customer_id):
    from flask_jwt_extended import get_jwt
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    
    # Check permissions
    if claims.get('role') == 'customer':
        customer = Customer.query.filter_by(user_id=int(current_user_id)).first()
        if not customer or customer.id != customer_id:
            return jsonify({'message': 'Unauthorized'}), 403
    elif claims.get('role') not in ['admin', 'sales', 'tech']:
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

@customers_bp.route('/api/customers/<int:customer_id>/subscribe', methods=['POST'])
@jwt_required()
def create_subscription(customer_id):
    from flask_jwt_extended import get_jwt
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'sales']:
        return jsonify({"msg": "Unauthorized"}), 403
    
    data = request.get_json()
    customer = Customer.query.get_or_404(customer_id)
    plan = ServicePlan.query.get_or_404(data['plan_id'])
    
    # Check for existing active subscription
    existing = Subscription.query.filter_by(
        customer_id=customer.id,
        status='active'
    ).first()
    
    if existing:
        return jsonify({'message': 'Customer already has an active subscription'}), 400
    
    # Calculate end date
    duration_days = data.get('duration_days', 30)
    end_date = datetime.utcnow() + timedelta(days=duration_days)
    
    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        status='active',
        payment_method=data.get('payment_method', 'cash'),
        end_date=end_date
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