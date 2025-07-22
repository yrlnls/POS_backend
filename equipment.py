from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import Equipment, Customer
from app import db
from datetime import datetime

equipment_bp = Blueprint('equipment', __name__, url_prefix='/api/equipment')

@equipment_bp.route('', methods=['GET'])
@jwt_required()
def get_all_equipment():
    """Get all equipment (admin/tech only)"""
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'tech']:
        return jsonify({'message': 'Tech access required'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    equipment_type = request.args.get('type')
    status = request.args.get('status')
    
    query = Equipment.query
    if equipment_type:
        query = query.filter_by(type=equipment_type)
    if status:
        query = query.filter_by(status=status)
    
    equipment_list = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'equipment': [{
            'id': eq.id,
            'customer_name': eq.customer.name,
            'type': eq.type,
            'model': eq.model,
            'serial_number': eq.serial_number,
            'mac_address': eq.mac_address,
            'status': eq.status,
            'installed_date': eq.installed_date.isoformat()
        } for eq in equipment_list.items],
        'total': equipment_list.total,
        'pages': equipment_list.pages,
        'current_page': page
    })

@equipment_bp.route('', methods=['POST'])
@jwt_required()
def create_equipment():
    """Create new equipment record (tech only)"""
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'tech']:
        return jsonify({'message': 'Tech access required'}), 403
    
    data = request.get_json()
    
    if not data or not all(k in data for k in ('customer_id', 'type', 'model', 'serial_number')):
        return jsonify({'message': 'Missing required fields'}), 400
    
    customer = Customer.query.get_or_404(data['customer_id'])
    
    # Check if serial number already exists
    existing = Equipment.query.filter_by(serial_number=data['serial_number']).first()
    if existing:
        return jsonify({'message': 'Equipment with this serial number already exists'}), 409
    
    equipment = Equipment(
        customer_id=customer.id,
        type=data['type'],
        model=data['model'],
        serial_number=data['serial_number'],
        mac_address=data.get('mac_address'),
        status=data.get('status', 'active')
    )
    
    db.session.add(equipment)
    db.session.commit()
    
    return jsonify({
        'id': equipment.id,
        'serial_number': equipment.serial_number,
        'message': 'Equipment created successfully'
    }), 201

@equipment_bp.route('/customer/<int:customer_id>', methods=['GET'])
@jwt_required()
def get_customer_equipment(customer_id):
    """Get all equipment for a customer"""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    
    # Check permissions
    if claims.get('role') == 'customer':
        customer = Customer.query.filter_by(user_id=int(current_user_id)).first()
        if not customer or customer.id != customer_id:
            return jsonify({'message': 'Unauthorized'}), 403
    
    customer = Customer.query.get_or_404(customer_id)
    equipment_list = Equipment.query.filter_by(customer_id=customer_id).all()
    
    return jsonify([{
        'id': eq.id,
        'type': eq.type,
        'model': eq.model,
        'serial_number': eq.serial_number,
        'mac_address': eq.mac_address,
        'status': eq.status,
        'installed_date': eq.installed_date.isoformat()
    } for eq in equipment_list])

@equipment_bp.route('/<int:equipment_id>', methods=['PUT'])
@jwt_required()
def update_equipment(equipment_id):
    """Update equipment status (tech only)"""
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'tech']:
        return jsonify({'message': 'Tech access required'}), 403
    
    equipment = Equipment.query.get_or_404(equipment_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    
    # Update fields if provided
    if 'status' in data:
        equipment.status = data['status']
    if 'mac_address' in data:
        equipment.mac_address = data['mac_address']
    
    db.session.commit()
    
    return jsonify({
        'id': equipment.id,
        'status': equipment.status,
        'message': 'Equipment updated successfully'
    })