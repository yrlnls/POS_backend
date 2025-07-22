from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from models import User, Customer, Subscription, Payment, Ticket, ServicePlan, Equipment, NetworkNode
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics"""
    claims = get_jwt()
    role = claims.get('role')
    
    if role not in ['admin', 'sales', 'tech']:
        return jsonify({'message': 'Unauthorized'}), 403
    
    # Basic counts
    total_customers = Customer.query.count()
    active_subscriptions = Subscription.query.filter_by(status='active').count()
    total_revenue = db.session.query(func.sum(Payment.amount)).filter_by(status='completed').scalar() or 0
    open_tickets = Ticket.query.filter_by(status='open').count()
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_customers = Customer.query.filter(Customer.created_at >= thirty_days_ago).count()
    recent_payments = Payment.query.filter(
        Payment.payment_date >= thirty_days_ago,
        Payment.status == 'completed'
    ).count()
    
    # Service plan popularity
    plan_stats = db.session.query(
        ServicePlan.name,
        func.count(Subscription.id).label('subscription_count')
    ).join(Subscription).filter(
        Subscription.status == 'active'
    ).group_by(ServicePlan.id, ServicePlan.name).all()
    
    # Monthly revenue (last 12 months)
    monthly_revenue = []
    for i in range(12):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        revenue = db.session.query(func.sum(Payment.amount)).filter(
            Payment.payment_date >= month_start,
            Payment.payment_date <= month_end,
            Payment.status == 'completed'
        ).scalar() or 0
        
        monthly_revenue.append({
            'month': month_start.strftime('%Y-%m'),
            'revenue': float(revenue)
        })
    
    monthly_revenue.reverse()  # Show oldest to newest
    
    # Ticket statistics
    ticket_stats = {
        'open': Ticket.query.filter_by(status='open').count(),
        'in_progress': Ticket.query.filter_by(status='in_progress').count(),
        'resolved': Ticket.query.filter_by(status='resolved').count(),
        'closed': Ticket.query.filter_by(status='closed').count()
    }
    
    # Network node status (for tech/admin)
    network_stats = {}
    if role in ['admin', 'tech']:
        total_nodes = NetworkNode.query.count()
        active_nodes = NetworkNode.query.filter_by(status='active').count()
        avg_load = db.session.query(func.avg(NetworkNode.current_load)).scalar() or 0
        
        network_stats = {
            'total_nodes': total_nodes,
            'active_nodes': active_nodes,
            'average_load': round(float(avg_load), 2)
        }
    
    return jsonify({
        'overview': {
            'total_customers': total_customers,
            'active_subscriptions': active_subscriptions,
            'total_revenue': float(total_revenue),
            'open_tickets': open_tickets,
            'new_customers_30d': new_customers,
            'recent_payments_30d': recent_payments
        },
        'service_plans': [
            {'name': name, 'subscriptions': count}
            for name, count in plan_stats
        ],
        'monthly_revenue': monthly_revenue,
        'ticket_stats': ticket_stats,
        'network_stats': network_stats
    })

@dashboard_bp.route('/recent-activity', methods=['GET'])
@jwt_required()
def get_recent_activity():
    """Get recent system activity"""
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'sales', 'tech']:
        return jsonify({'message': 'Unauthorized'}), 403
    
    # Recent customers (last 10)
    recent_customers = Customer.query.order_by(
        Customer.created_at.desc()
    ).limit(10).all()
    
    # Recent payments (last 10)
    recent_payments = Payment.query.order_by(
        Payment.payment_date.desc()
    ).limit(10).all()
    
    # Recent tickets (last 10)
    recent_tickets = Ticket.query.order_by(
        Ticket.created_at.desc()
    ).limit(10).all()
    
    return jsonify({
        'recent_customers': [{
            'id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'created_at': customer.created_at.isoformat()
        } for customer in recent_customers],
        'recent_payments': [{
            'id': payment.id,
            'customer_name': payment.subscription.customer.name,
            'amount': payment.amount,
            'payment_date': payment.payment_date.isoformat(),
            'status': payment.status
        } for payment in recent_payments],
        'recent_tickets': [{
            'id': ticket.id,
            'title': ticket.title,
            'customer_name': ticket.customer.name,
            'status': ticket.status,
            'priority': ticket.priority,
            'created_at': ticket.created_at.isoformat()
        } for ticket in recent_tickets]
    })