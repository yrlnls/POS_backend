from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Ticket, Customer, User, db
from datetime import datetime

tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route('/tickets', methods=['GET'])
@jwt_required()
def get_tickets():
    current_user = get_jwt_identity()
    # current_user is a string (user id), fetch user from DB
    user = User.query.get(int(current_user))
    
    if user.role == 'customer':
        tickets = Ticket.query.filter_by(customer_id=user.id).all()
    elif user.role == 'tech':
        tickets = Ticket.query.filter(Ticket.assigned_to.in_([None, user.id])).all()
    else:
        tickets = Ticket.query.all()
    
    return jsonify([{
        'id': ticket.id,
        'title': ticket.title,
        'status': ticket.status,
        'priority': ticket.priority,
        'created_at': ticket.created_at.isoformat(),
        'customer': Customer.query.get(ticket.customer_id).name
    } for ticket in tickets])

@tickets_bp.route('/tickets', methods=['POST'])
@jwt_required()
def create_ticket():
    data = request.get_json()
    current_user = get_jwt_identity()
    # current_user is a string (user id), convert to int
    user_id = int(current_user)

    # Validate required fields
    if not data or 'title' not in data or 'description' not in data:
        return jsonify({"msg": "Missing required fields: title and description"}), 400

    try:
        ticket = Ticket(
            customer_id=user_id,
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
        'status': ticket.status
    }), 201

@tickets_bp.route('/tickets/<int:ticket_id>', methods=['PUT'])
@jwt_required()
def update_ticket(ticket_id):
    current_user = get_jwt_identity()
    # current_user is a string (user id), fetch user from DB
    user = User.query.get(int(current_user))
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if user.role == 'customer' and ticket.customer_id != user.id:
        return jsonify({"msg": "Unauthorized"}), 403
    
    data = request.get_json()
    if 'status' in data and user.role in ['tech', 'admin']:
        ticket.status = data['status']
        if data['status'] == 'resolved':
            ticket.resolved_at = datetime.utcnow()
    
    if 'assigned_to' in data and user.role in ['tech', 'admin']:
        ticket.assigned_to = data['assigned_to']
    
    db.session.commit()
    return jsonify({
        'id': ticket.id,
        'status': ticket.status,
        'assigned_to': ticket.assigned_to
    })
