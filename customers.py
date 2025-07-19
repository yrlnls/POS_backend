from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Customer, ServicePlan, Subscription, db
from datetime import datetime, timedelta

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/customers', methods=['GET'])
@jwt_required()
def get_customers():
    current_user = get_jwt_identity()
    if current_user['role'] not in ['admin', 'sales']:
        return jsonify({"msg": "Unauthorized"}), 403
    
    customers = Customer.query.all()
    return jsonify([{
        'id': customer.id,
        'name': customer.name,
        'email': customer.email,
        'phone': customer.phone,
        'address': customer.address
    } for customer in customers])

@customers_bp.route('/customers', methods=['POST'])
@jwt_required()
def create_customer():
    current_user = get_jwt_identity()
    if current_user['role'] not in ['admin', 'sales']:
        return jsonify({"msg": "Unauthorized"}), 403
    
    data = request.get_json()
    customer = Customer(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone'),
        address=data.get('address')
    )
    db.session.add(customer)
    db.session.commit()
    
    return jsonify({
        'id': customer.id,
        'name': customer.name,
        'email': customer.email
    }), 201

@customers_bp.route('/customers/<int:customer_id>/subscribe', methods=['POST'])
@jwt_required()
def create_subscription(customer_id):
    current_user = get_jwt_identity()
    if current_user['role'] not in ['admin', 'sales']:
        return jsonify({"msg": "Unauthorized"}), 403
    
    data = request.get_json()
    customer = Customer.query.get_or_404(customer_id)
    plan = ServicePlan.query.get_or_404(data['plan_id'])
    
    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        status='active',
        payment_method=data.get('payment_method', 'cash'),
        end_date=datetime.utcnow() + timedelta(days=30)
    )
    db.session.add(subscription)
    db.session.commit()
    
    return jsonify({
        'id': subscription.id,
        'customer': customer.name,
        'plan': plan.name,
        'status': subscription.status
    }), 201
