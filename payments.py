from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import Payment, Subscription, Customer
from app import db
from datetime import datetime
import uuid

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@payments_bp.route('', methods=['POST'])
@jwt_required()
def create_payment():
    """Create new payment (sales role required)"""
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'sales']:
        return jsonify({'message': 'Sales access required'}), 403
    
    data = request.get_json()
    
    if not data or not all(k in data for k in ('subscription_id', 'amount', 'payment_method')):
        return jsonify({'message': 'Missing required fields'}), 400
    
    subscription = Subscription.query.get_or_404(data['subscription_id'])
    
    # Generate transaction ID
    transaction_id = str(uuid.uuid4())
    
    payment = Payment(
        subscription_id=subscription.id,
        amount=float(data['amount']),
        payment_method=data['payment_method'],
        transaction_id=transaction_id,
        status=data.get('status', 'completed')
    )
    
    db.session.add(payment)
    db.session.commit()
    
    return jsonify({
        'id': payment.id,
        'transaction_id': payment.transaction_id,
        'amount': payment.amount,
        'status': payment.status,
        'message': 'Payment recorded successfully'
    }), 201

@payments_bp.route('/subscription/<int:subscription_id>', methods=['GET'])
@jwt_required()
def get_subscription_payments(subscription_id):
    """Get all payments for a subscription"""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    
    subscription = Subscription.query.get_or_404(subscription_id)
    
    # Check permissions
    if claims.get('role') == 'customer':
        customer = Customer.query.filter_by(user_id=int(current_user_id)).first()
        if not customer or subscription.customer_id != customer.id:
            return jsonify({'message': 'Unauthorized'}), 403
    
    payments = Payment.query.filter_by(subscription_id=subscription_id).all()
    
    return jsonify([{
        'id': payment.id,
        'amount': payment.amount,
        'payment_date': payment.payment_date.isoformat(),
        'payment_method': payment.payment_method,
        'transaction_id': payment.transaction_id,
        'status': payment.status
    } for payment in payments])

@payments_bp.route('/process', methods=['POST'])
@jwt_required()
def process_payment():
    """Process payment through payment gateway"""
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'sales']:
        return jsonify({'message': 'Sales access required'}), 403
    
    data = request.get_json()
    
    if not data or not all(k in data for k in ('subscription_id', 'amount', 'payment_method')):
        return jsonify({'message': 'Missing required fields'}), 400
    
    subscription = Subscription.query.get_or_404(data['subscription_id'])
    
    # Simulate payment processing
    transaction_id = str(uuid.uuid4())
    
    # In a real implementation, integrate with payment gateway here
    # For demo, we'll simulate success/failure
    import random
    success = random.choice([True, True, True, False])  # 75% success rate
    
    status = 'completed' if success else 'failed'
    
    payment = Payment(
        subscription_id=subscription.id,
        amount=float(data['amount']),
        payment_method=data['payment_method'],
        transaction_id=transaction_id,
        status=status
    )
    
    db.session.add(payment)
    db.session.commit()
    
    return jsonify({
        'id': payment.id,
        'transaction_id': payment.transaction_id,
        'amount': payment.amount,
        'status': payment.status,
        'success': success,
        'message': 'Payment processed successfully' if success else 'Payment failed'
    }), 201 if success else 400

@payments_bp.route('', methods=['GET'])
@jwt_required()
def get_all_payments():
    """Get all payments (admin/sales only)"""
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'sales']:
        return jsonify({'message': 'Unauthorized'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = Payment.query
    if status:
        query = query.filter_by(status=status)
    
    payments = query.order_by(Payment.payment_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'payments': [{
            'id': payment.id,
            'subscription_id': payment.subscription_id,
            'customer_name': payment.subscription.customer.name,
            'amount': payment.amount,
            'payment_date': payment.payment_date.isoformat(),
            'payment_method': payment.payment_method,
            'transaction_id': payment.transaction_id,
            'status': payment.status
        } for payment in payments.items],
        'total': payments.total,
        'pages': payments.pages,
        'current_page': page
    })

@payments_bp.route('/<int:payment_id>', methods=['GET'])
@jwt_required()
def get_payment(payment_id):
    """Get specific payment details"""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    
    payment = Payment.query.get_or_404(payment_id)
    
    # Check permissions
    if claims.get('role') == 'customer':
        customer = Customer.query.filter_by(user_id=int(current_user_id)).first()
        if not customer or payment.subscription.customer_id != customer.id:
            return jsonify({'message': 'Unauthorized'}), 403
    
    return jsonify({
        'id': payment.id,
        'subscription_id': payment.subscription_id,
        'customer_name': payment.subscription.customer.name,
        'plan_name': payment.subscription.plan.name,
        'amount': payment.amount,
        'payment_date': payment.payment_date.isoformat(),
        'payment_method': payment.payment_method,
        'transaction_id': payment.transaction_id,
        'status': payment.status
    })