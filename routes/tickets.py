from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Ticket, Customer, User
from app import db
from datetime import datetime

tickets_bp = Blueprint('tickets', __name__, url_prefix='/api/tickets')

@tickets_bp.route('', methods=['GET'])
@jwt_required()
def get_tickets():
    from flask_jwt_extended import get_jwt
    current_user = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role')
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    priority = request.args.get('priority')
    
    query = Ticket.query
    
    if role == 'customer':
        customer = Customer.query.filter_by(user_id=int(current_user)).first()
        if not customer:
            return jsonify({'message': 'Customer profile not found'}), 404
        query = query.filter_by(customer_id=customer.id)
    elif role == 'tech':
        user_id = int(current_user)
        query = query.filter(
            (Ticket.assigned_to == user_id) | (Ticket.assigned_to.is_(None))
        )
    
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    
    tickets = query.order_by(Ticket.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'tickets': [{
            'id': ticket.id,
            'title': ticket.title,
            'description': ticket.description,
            'status': ticket.status,
            'priority': ticket.priority,
            'created_at': ticket.created_at.isoformat(),
            'customer_name': ticket.customer.name,
            'assigned_to': ticket.assigned_user.username if ticket.assigned_user else None
        } for ticket in tickets.items],
        'total': tickets.total,
        'pages': tickets.pages,
        'current_page': page
    })

@tickets_bp.route('', methods=['POST'])
@jwt_required()
def create_ticket():
    from flask_jwt_extended import get_jwt
    data = request.get_json()
    current_user = get_jwt_identity()
    claims = get_jwt()

    if not data or 'title' not in data or 'description' not in data:
        return jsonify({"msg": "Missing required fields: title and description"}), 400

    # Get customer ID based on role
    if claims.get('role') == 'customer':
        customer = Customer.query.filter_by(user_id=int(current_user)).first()
        if not customer:
            return jsonify({'message': 'Customer profile not found'}), 404
        customer_id = customer.id
    else:
        # Admin/sales/tech can create tickets for any customer
        if 'customer_id' not in data:
            return jsonify({'message': 'customer_id required'}), 400
        customer_id = data['customer_id']

    try:
        ticket = Ticket(
            customer_id=customer_id,
            title=data['title'],
            description=data['description'],
            priority=data.get('priority', 'medium')
        )
        db.session.add(ticket)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to create ticket", "error": str(e)}), 500
    
    return jsonify({
        'id': ticket.id,
        'title': ticket.title,
        'status': ticket.status,
        'customer_name': ticket.customer.name
    }), 201

@tickets_bp.route('/<int:ticket_id>', methods=['GET'])
@jwt_required()
def get_ticket(ticket_id):
    from flask_jwt_extended import get_jwt
    current_user = get_jwt_identity()
    claims = get_jwt()
    
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Check permissions
    if claims.get('role') == 'customer':
        customer = Customer.query.filter_by(user_id=int(current_user)).first()
        if not customer or ticket.customer_id != customer.id:
            return jsonify({'message': 'Unauthorized'}), 403
    
    return jsonify({
        'id': ticket.id,
        'title': ticket.title,
        'description': ticket.description,
        'status': ticket.status,
        'priority': ticket.priority,
        'created_at': ticket.created_at.isoformat(),
        'resolved_at': ticket.resolved_at.isoformat() if ticket.resolved_at else None,
        'customer_name': ticket.customer.name,
        'assigned_to': ticket.assigned_user.username if ticket.assigned_user else None
    })

@tickets_bp.route('/<int:ticket_id>', methods=['PUT'])
@jwt_required()
def update_ticket(ticket_id):
    from flask_jwt_extended import get_jwt
    current_user = get_jwt_identity()
    claims = get_jwt()
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Check permissions
    if claims.get('role') == 'customer':
        customer = Customer.query.filter_by(user_id=int(current_user)).first()
        if not customer or ticket.customer_id != customer.id:
            return jsonify({"msg": "Unauthorized"}), 403
    elif claims.get('role') not in ['admin', 'tech', 'sales']:
        return jsonify({"msg": "Unauthorized"}), 403
    
    data = request.get_json()
    
    if 'status' in data and claims.get('role') in ['tech', 'admin']:
        ticket.status = data['status']
        if data['status'] == 'resolved':
            ticket.resolved_at = datetime.utcnow()
    
    if 'assigned_to' in data and claims.get('role') in ['tech', 'admin']:
        ticket.assigned_to = data['assigned_to']
    
    if 'priority' in data and claims.get('role') in ['tech', 'admin']:
        ticket.priority = data['priority']
    
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'id': ticket.id,
        'status': ticket.status,
        'priority': ticket.priority,
        'assigned_to': ticket.assigned_to,
        'message': 'Ticket updated successfully'
    })

@tickets_bp.route('/customer/<int:customer_id>', methods=['GET'])
@jwt_required()
def get_customer_tickets(customer_id):
    from flask_jwt_extended import get_jwt
    current_user = get_jwt_identity()
    claims = get_jwt()
    
    # Check permissions
    if claims.get('role') == 'customer':
        customer = Customer.query.filter_by(user_id=int(current_user)).first()
        if not customer or customer.id != customer_id:
            return jsonify({'message': 'Unauthorized'}), 403
    elif claims.get('role') not in ['admin', 'tech', 'sales']:
        return jsonify({'message': 'Unauthorized'}), 403
    
    customer = Customer.query.get_or_404(customer_id)
    tickets = Ticket.query.filter_by(customer_id=customer_id).order_by(
        Ticket.created_at.desc()
    ).all()
    
    return jsonify([{
        'id': ticket.id,
        'title': ticket.title,
        'description': ticket.description,
        'status': ticket.status,
        'priority': ticket.priority,
        'created_at': ticket.created_at.isoformat(),
        'assigned_to': ticket.assigned_user.username if ticket.assigned_user else None
    } for ticket in tickets])

@tickets_bp.route('/<int:ticket_id>/status', methods=['PATCH'])
@jwt_required()
def update_ticket_status(ticket_id):
    from flask_jwt_extended import get_jwt
    claims = get_jwt()
    
    if claims.get('role') not in ['admin', 'tech']:
        return jsonify({'message': 'Tech access required'}), 403
    
    ticket = Ticket.query.get_or_404(ticket_id)
    data = request.get_json()
    
    if not data or 'status' not in data:
        return jsonify({'message': 'Status required'}), 400
    
    valid_statuses = ['open', 'in_progress', 'resolved', 'closed']
    if data['status'] not in valid_statuses:
        return jsonify({'message': 'Invalid status'}), 400
    
    ticket.status = data['status']
    if data['status'] == 'resolved':
        ticket.resolved_at = datetime.utcnow()
    
    ticket.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'id': ticket.id,
        'status': ticket.status,
        'message': 'Ticket status updated successfully'
    })
