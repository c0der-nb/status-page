from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import emit
from models import db, Service, ServiceStatusHistory, Organization, User
import uuid
from datetime import datetime

services_bp = Blueprint('services', __name__)

@services_bp.route('', methods=['GET'])
@jwt_required()
def get_services():
    org_id = request.args.get('org_id')
    
    if not org_id:
        return jsonify({'error': 'Organization ID is required'}), 400
    
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user has access to this organization
    if not user.is_superadmin and not user.get_role_in_organization(org_id):
        return jsonify({'error': 'Access denied'}), 403
    
    services = Service.query.filter_by(organization_id=org_id).order_by(Service.display_order).all()
    
    services_data = []
    for service in services:
        services_data.append({
            'id': str(service.id),
            'name': service.name,
            'description': service.description,
            'status': service.status,
            'team_id': str(service.team_id) if service.team_id else None,
            'team_name': service.team.name if service.team else None,
            'display_order': service.display_order,
            'is_public': service.is_public,
            'created_at': service.created_at.isoformat(),
            'updated_at': service.updated_at.isoformat()
        })
    
    return jsonify({'services': services_data}), 200

@services_bp.route('', methods=['POST'])
@jwt_required()
def create_service():
    data = request.get_json()
    
    required_fields = ['name', 'organization_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check user permissions
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user has permission in this organization
    if not user.is_superadmin:
        user_role = user.get_role_in_organization(data['organization_id'])
        if user_role not in ['admin', 'member']:
            return jsonify({'error': 'Insufficient permissions'}), 403
    
    try:
        # Get the max display order for this organization
        max_order = db.session.query(db.func.max(Service.display_order)).filter_by(
            organization_id=data['organization_id']
        ).scalar() or 0
        
        service = Service(
            organization_id=data['organization_id'],
            name=data['name'],
            description=data.get('description', ''),
            status=data.get('status', 'operational'),
            team_id=data['team_id'] if data.get('team_id') else None,
            display_order=max_order + 1,
            is_public=data.get('is_public', True)
        )
        db.session.add(service)
        db.session.flush()
        
        # Add initial status history
        current_user_id = get_jwt_identity()
        history = ServiceStatusHistory(
            service_id=service.id,
            status='operational',
            changed_by_id=current_user_id,
            reason='Service created'
        )
        db.session.add(history)
        
        db.session.commit()
        
        # Emit real-time update
        from app import socketio
        # Emit to organization room
        socketio.emit('service_created', {
            'organization_id': str(service.organization_id),
            'service': {
                'id': str(service.id),
                'name': service.name,
                'status': service.status
            }
        }, room=f'org_{service.organization_id}')
        
        # Also emit to public room if service is public
        if service.is_public:
            org = Organization.query.get(service.organization_id)
            if org:
                socketio.emit('public_service_created', {
                    'service': {
                        'id': str(service.id),
                        'name': service.name,
                        'description': service.description,
                        'status': service.status,
                        'display_order': service.display_order
                    }
                }, room=f'public_{org.slug}')
                print(f"Emitted public_service_created to room: public_{org.slug}")
        
        return jsonify({
            'id': str(service.id),
            'name': service.name,
            'description': service.description,
            'status': service.status,
            'organization_id': str(service.organization_id),
            'team_id': str(service.team_id) if service.team_id else None,
            'display_order': service.display_order,
            'is_public': service.is_public,
            'created_at': service.created_at.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@services_bp.route('/<service_id>', methods=['GET'])
@jwt_required()
def get_service(service_id):
    service = Service.query.get(service_id)
    
    if not service:
        return jsonify({'error': 'Service not found'}), 404
    
    # Check access
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user.is_superadmin and not user.get_role_in_organization(service.organization_id):
        return jsonify({'error': 'Access denied'}), 403
    
    # Get recent status history
    history = ServiceStatusHistory.query.filter_by(
        service_id=service.id
    ).order_by(ServiceStatusHistory.created_at.desc()).limit(10).all()
    
    history_data = []
    for h in history:
        history_data.append({
            'id': str(h.id),
            'status': h.status,
            'reason': h.reason,
            'changed_by': h.changed_by.username if h.changed_by else 'System',
            'created_at': h.created_at.isoformat()
        })
    
    return jsonify({
        'id': str(service.id),
        'name': service.name,
        'description': service.description,
        'status': service.status,
        'organization_id': str(service.organization_id),
        'team_id': str(service.team_id) if service.team_id else None,
        'team_name': service.team.name if service.team else None,
        'display_order': service.display_order,
        'is_public': service.is_public,
        'status_history': history_data,
        'created_at': service.created_at.isoformat(),
        'updated_at': service.updated_at.isoformat()
    }), 200

@services_bp.route('/<service_id>', methods=['PUT'])
@jwt_required()
def update_service(service_id):
    service = Service.query.get(service_id)
    
    if not service:
        return jsonify({'error': 'Service not found'}), 404
    
    # Check user permissions for this service's organization
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user has permission in the service's organization
    if not user.is_superadmin:
        user_role = user.get_role_in_organization(service.organization_id)
        if user_role not in ['admin', 'member']:
            return jsonify({'error': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    
    # Track if status changed
    status_changed = False
    old_status = service.status
    
    if 'name' in data:
        service.name = data['name']
    
    if 'description' in data:
        service.description = data['description']
    
    if 'status' in data and data['status'] != service.status:
        if data['status'] not in ['operational', 'degraded', 'partial_outage', 'major_outage', 'maintenance']:
            return jsonify({'error': 'Invalid status'}), 400
        service.status = data['status']
        status_changed = True
    
    if 'team_id' in data:
        service.team_id = uuid.UUID(data['team_id']) if data['team_id'] else None
    
    if 'display_order' in data:
        service.display_order = data['display_order']
    
    if 'is_public' in data:
        service.is_public = data['is_public']
    
    service.updated_at = datetime.utcnow()
    
    try:
        # Add status history if status changed
        if status_changed:
            history = ServiceStatusHistory(
                service_id=service.id,
                status=service.status,
                changed_by_id=current_user_id,
                reason=data.get('status_reason', 'Status updated')
            )
            db.session.add(history)
        
        db.session.commit()
        
        # Emit real-time update if status changed
        if status_changed:
            from app import socketio
            # Emit to organization room (authenticated users)
            socketio.emit('service_status_changed', {
                'organization_id': str(service.organization_id),
                'service': {
                    'id': str(service.id),
                    'name': service.name,
                    'old_status': old_status,
                    'new_status': service.status
                }
            }, room=f'org_{service.organization_id}')
            
            # Also emit to public room if service is public
            if service.is_public:
                org = Organization.query.get(service.organization_id)
                if org:
                    socketio.emit('public_service_status_changed', {
                        'service': {
                            'id': str(service.id),
                            'name': service.name,
                            'status': service.status,
                            'old_status': old_status
                        }
                    }, room=f'public_{org.slug}')
                    print(f"Emitted public_service_status_changed to room: public_{org.slug}")
        
        return jsonify({
            'id': str(service.id),
            'name': service.name,
            'description': service.description,
            'status': service.status,
            'team_id': str(service.team_id) if service.team_id else None,
            'display_order': service.display_order,
            'is_public': service.is_public,
            'updated_at': service.updated_at.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@services_bp.route('/<service_id>', methods=['DELETE'])
@jwt_required()
def delete_service(service_id):
    service = Service.query.get(service_id)
    
    if not service:
        return jsonify({'error': 'Service not found'}), 404
    
    # Check user permissions for this service's organization
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user has admin permission in the service's organization
    if not user.is_superadmin:
        user_role = user.get_role_in_organization(service.organization_id)
        if user_role != 'admin':
            return jsonify({'error': 'Only administrators can delete services'}), 403
    
    org_id = str(service.organization_id)
    
    try:
        db.session.delete(service)
        db.session.commit()
        
        # Emit real-time update
        from app import socketio
        socketio.emit('service_deleted', {
            'organization_id': org_id,
            'service_id': service_id
        }, room=f'org_{org_id}')
        
        return jsonify({'message': 'Service deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@services_bp.route('/reorder', methods=['POST'])
@jwt_required()
def reorder_services():
    data = request.get_json()
    
    if not data.get('organization_id'):
        return jsonify({'error': 'Organization ID is required'}), 400
    
    if not data.get('service_ids'):
        return jsonify({'error': 'Service IDs are required'}), 400
    
    # Check user permissions
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user has permission in this organization
    if not user.is_superadmin:
        user_role = user.get_role_in_organization(data['organization_id'])
        if user_role not in ['admin', 'member']:
            return jsonify({'error': 'Insufficient permissions'}), 403
    
    try:
        for index, service_id in enumerate(data['service_ids']):
            service = Service.query.get(service_id)
            if service and str(service.organization_id) == data['organization_id']:
                service.display_order = index
        
        db.session.commit()
        return jsonify({'message': 'Services reordered successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
