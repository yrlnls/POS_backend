from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from models import NetworkNode
from app import db
from datetime import datetime

network_nodes_bp = Blueprint('network_nodes', __name__, url_prefix='/api/network-nodes')

@network_nodes_bp.route('', methods=['GET'])
@jwt_required()
def get_network_nodes():
    """Get all network nodes (tech/admin only)"""
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'tech']:
        return jsonify({'message': 'Tech access required'}), 403
    
    nodes = NetworkNode.query.all()
    
    return jsonify([{
        'id': node.id,
        'name': node.name,
        'location': node.location,
        'status': node.status,
        'capacity': node.capacity,
        'current_load': node.current_load,
        'load_percentage': round((node.current_load / node.capacity) * 100, 2) if node.capacity > 0 else 0
    } for node in nodes])

@network_nodes_bp.route('', methods=['POST'])
@jwt_required()
def create_network_node():
    """Create new network node (admin only)"""
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    data = request.get_json()
    
    if not data or not all(k in data for k in ('name', 'location', 'capacity')):
        return jsonify({'message': 'Missing required fields'}), 400
    
    node = NetworkNode(
        name=data['name'],
        location=data['location'],
        capacity=int(data['capacity']),
        current_load=data.get('current_load', 0),
        status=data.get('status', 'active')
    )
    
    db.session.add(node)
    db.session.commit()
    
    return jsonify({
        'id': node.id,
        'name': node.name,
        'message': 'Network node created successfully'
    }), 201

@network_nodes_bp.route('/<int:node_id>', methods=['PUT'])
@jwt_required()
def update_network_node(node_id):
    """Update network node (admin/tech)"""
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'tech']:
        return jsonify({'message': 'Tech access required'}), 403
    
    node = NetworkNode.query.get_or_404(node_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    
    # Update fields if provided
    if 'status' in data:
        node.status = data['status']
    if 'current_load' in data:
        node.current_load = int(data['current_load'])
    if 'capacity' in data and claims.get('role') == 'admin':
        node.capacity = int(data['capacity'])
    
    node.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'id': node.id,
        'message': 'Network node updated successfully'
    })

@network_nodes_bp.route('/<int:node_id>', methods=['GET'])
@jwt_required()
def get_network_node(node_id):
    """Get specific network node details"""
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'tech']:
        return jsonify({'message': 'Tech access required'}), 403
    
    node = NetworkNode.query.get_or_404(node_id)
    
    return jsonify({
        'id': node.id,
        'name': node.name,
        'location': node.location,
        'status': node.status,
        'capacity': node.capacity,
        'current_load': node.current_load,
        'load_percentage': round((node.current_load / node.capacity) * 100, 2) if node.capacity > 0 else 0,
        'created_at': node.created_at.isoformat(),
        'updated_at': node.updated_at.isoformat()
    })