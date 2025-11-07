from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Incident, IncidentUpdate, Service, User, Organization
import uuid
from datetime import datetime

incidents_bp = Blueprint('incidents', __name__)

@incidents_bp.route('', methods=['GET'])
@jwt_required()
def get_incidents():
    org_id = request.args.get('org_id')
    status = request.args.get('status')
    incident_type = request.args.get('type')
    
    if not org_id:
        return jsonify({'error': 'Organization ID is required'}), 400
    
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user has access to this organization
    if not user.is_superadmin and not user.get_role_in_organization(org_id):
        return jsonify({'error': 'Access denied'}), 403
    
    query = Incident.query.filter_by(organization_id=org_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if incident_type:
        query = query.filter_by(type=incident_type)
    
    incidents = query.order_by(Incident.created_at.desc()).all()
    
    incidents_data = []
    for incident in incidents:
        incidents_data.append({
            'id': str(incident.id),
            'title': incident.title,
            'description': incident.description,
            'status': incident.status,
            'impact': incident.impact,
            'type': incident.type,
            'scheduled_start': incident.scheduled_start.isoformat() if incident.scheduled_start else None,
            'scheduled_end': incident.scheduled_end.isoformat() if incident.scheduled_end else None,
            'resolved_at': incident.resolved_at.isoformat() if incident.resolved_at else None,
            'created_by': incident.created_by.username if incident.created_by else 'System',
            'affected_services': [{'id': str(s.id), 'name': s.name} for s in incident.affected_services],
            'updates_count': len(incident.updates),
            'created_at': incident.created_at.isoformat(),
            'updated_at': incident.updated_at.isoformat()
        })
    
    return jsonify({'incidents': incidents_data}), 200

@incidents_bp.route('', methods=['POST'])
@jwt_required()
def create_incident():
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    required_fields = ['title', 'organization_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check user permissions
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user has permission in this organization
    if not user.is_superadmin:
        user_role = user.get_role_in_organization(data['organization_id'])
        if user_role not in ['admin', 'member']:
            return jsonify({'error': 'Insufficient permissions'}), 403
    
    # Validate type
    incident_type = data.get('type', 'incident')
    if incident_type not in ['incident', 'maintenance']:
        return jsonify({'error': 'Invalid incident type'}), 400
    
    # Validate status
    status = data.get('status', 'investigating')
    if status not in ['investigating', 'identified', 'monitoring', 'resolved', 'scheduled', 'in_progress', 'completed']:
        return jsonify({'error': 'Invalid status'}), 400
    
    # Validate impact
    impact = data.get('impact', 'none')
    if impact not in ['none', 'minor', 'major', 'critical']:
        return jsonify({'error': 'Invalid impact level'}), 400
    
    try:
        incident = Incident(
            organization_id=data['organization_id'],
            title=data['title'],
            description=data.get('description', ''),
            status=status,
            impact=impact,
            type=incident_type,
            created_by_id=current_user_id
        )
        
        # For maintenance, set scheduled times
        if incident_type == 'maintenance':
            if data.get('scheduled_start'):
                incident.scheduled_start = datetime.fromisoformat(data['scheduled_start'].replace('Z', '+00:00'))
            if data.get('scheduled_end'):
                incident.scheduled_end = datetime.fromisoformat(data['scheduled_end'].replace('Z', '+00:00'))
        
        db.session.add(incident)
        db.session.flush()
        
        # Add affected services
        if data.get('service_ids'):
            for service_id in data['service_ids']:
                service = Service.query.get(service_id)
                if service and str(service.organization_id) == data['organization_id']:
                    incident.affected_services.append(service)
        
        # Add initial update
        initial_update = IncidentUpdate(
            incident_id=incident.id,
            user_id=current_user_id,
            status=status,
            message=data.get('initial_message', f'{incident_type.capitalize()} created')
        )
        db.session.add(initial_update)
        
        db.session.commit()
        
        # Emit real-time update
        from app import socketio
        # Emit to organization room
        socketio.emit('incident_created', {
            'organization_id': str(incident.organization_id),
            'incident': {
                'id': str(incident.id),
                'title': incident.title,
                'status': incident.status,
                'type': incident.type,
                'impact': incident.impact
            }
        }, room=f'org_{incident.organization_id}')
        
        # Also emit to public room
        org = Organization.query.get(incident.organization_id)
        if org:
            socketio.emit('public_incident_created', {
                'incident': {
                    'id': str(incident.id),
                    'title': incident.title,
                    'status': incident.status,
                    'type': incident.type,
                    'impact': incident.impact,
                    'created_at': incident.created_at.isoformat()
                }
            }, room=f'public_{org.slug}')
            print(f"Emitted public_incident_created to room: public_{org.slug}")
        
        return jsonify({
            'id': str(incident.id),
            'title': incident.title,
            'description': incident.description,
            'status': incident.status,
            'impact': incident.impact,
            'type': incident.type,
            'organization_id': str(incident.organization_id),
            'affected_services': [{'id': str(s.id), 'name': s.name} for s in incident.affected_services],
            'created_at': incident.created_at.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@incidents_bp.route('/<incident_id>', methods=['GET'])
@jwt_required()
def get_incident(incident_id):
    incident = Incident.query.get(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    # Check access
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user.is_superadmin and not user.get_role_in_organization(incident.organization_id):
        return jsonify({'error': 'Access denied'}), 403
    
    # Get all updates
    updates = []
    for update in incident.updates:
        updates.append({
            'id': str(update.id),
            'status': update.status,
            'message': update.message,
            'user': update.user.username if update.user else 'System',
            'created_at': update.created_at.isoformat()
        })
    
    return jsonify({
        'id': str(incident.id),
        'title': incident.title,
        'description': incident.description,
        'status': incident.status,
        'impact': incident.impact,
        'type': incident.type,
        'scheduled_start': incident.scheduled_start.isoformat() if incident.scheduled_start else None,
        'scheduled_end': incident.scheduled_end.isoformat() if incident.scheduled_end else None,
        'resolved_at': incident.resolved_at.isoformat() if incident.resolved_at else None,
        'organization_id': str(incident.organization_id),
        'created_by': incident.created_by.username if incident.created_by else 'System',
        'affected_services': [{'id': str(s.id), 'name': s.name, 'status': s.status} for s in incident.affected_services],
        'updates': updates,
        'created_at': incident.created_at.isoformat(),
        'updated_at': incident.updated_at.isoformat()
    }), 200

@incidents_bp.route('/<incident_id>', methods=['PUT'])
@jwt_required()
def update_incident(incident_id):
    incident = Incident.query.get(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    # Check user permissions for this incident's organization
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user has permission in the incident's organization
    if not user.is_superadmin:
        user_role = user.get_role_in_organization(incident.organization_id)
        if user_role not in ['admin', 'member']:
            return jsonify({'error': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    
    # Track changes for update message
    changes = []
    
    if 'title' in data:
        incident.title = data['title']
        changes.append('title')
    
    if 'description' in data:
        incident.description = data['description']
        changes.append('description')
    
    if 'status' in data and data['status'] != incident.status:
        if data['status'] not in ['investigating', 'identified', 'monitoring', 'resolved', 'scheduled', 'in_progress', 'completed']:
            return jsonify({'error': 'Invalid status'}), 400
        
        old_status = incident.status
        incident.status = data['status']
        changes.append(f'status from {old_status} to {data["status"]}')
        
        # Set resolved_at if resolving
        if data['status'] in ['resolved', 'completed']:
            incident.resolved_at = datetime.utcnow()
    
    if 'impact' in data and data['impact'] != incident.impact:
        if data['impact'] not in ['none', 'minor', 'major', 'critical']:
            return jsonify({'error': 'Invalid impact level'}), 400
        
        old_impact = incident.impact
        incident.impact = data['impact']
        changes.append(f'impact from {old_impact} to {data["impact"]}')
    
    if 'scheduled_start' in data:
        incident.scheduled_start = datetime.fromisoformat(data['scheduled_start'].replace('Z', '+00:00')) if data['scheduled_start'] else None
    
    if 'scheduled_end' in data:
        incident.scheduled_end = datetime.fromisoformat(data['scheduled_end'].replace('Z', '+00:00')) if data['scheduled_end'] else None
    
    incident.updated_at = datetime.utcnow()
    
    try:
        # Update affected services
        if 'service_ids' in data:
            incident.affected_services.clear()
            for service_id in data['service_ids']:
                service = Service.query.get(service_id)
                if service and service.organization_id == incident.organization_id:
                    incident.affected_services.append(service)
            changes.append('affected services')
        
        # Add update entry if there were changes
        if changes:
            update_message = data.get('update_message', f'Updated: {", ".join(changes)}')
            update = IncidentUpdate(
                incident_id=incident.id,
                user_id=current_user_id,
                status=incident.status,
                message=update_message
            )
            db.session.add(update)
        
        db.session.commit()
        
        # Emit real-time update
        from app import socketio
        # Emit to organization room
        socketio.emit('incident_updated', {
            'organization_id': str(incident.organization_id),
            'incident': {
                'id': str(incident.id),
                'title': incident.title,
                'status': incident.status,
                'impact': incident.impact,
                'changes': changes
            }
        }, room=f'org_{incident.organization_id}')
        
        # Also emit to public room
        org = Organization.query.get(incident.organization_id)
        if org:
            socketio.emit('public_incident_updated', {
                'incident': {
                    'id': str(incident.id),
                    'title': incident.title,
                    'status': incident.status,
                    'impact': incident.impact,
                    'resolved_at': incident.resolved_at.isoformat() if incident.resolved_at else None
                }
            }, room=f'public_{org.slug}')
            print(f"Emitted public_incident_updated to room: public_{org.slug}")
        
        return jsonify({
            'id': str(incident.id),
            'title': incident.title,
            'description': incident.description,
            'status': incident.status,
            'impact': incident.impact,
            'resolved_at': incident.resolved_at.isoformat() if incident.resolved_at else None,
            'updated_at': incident.updated_at.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@incidents_bp.route('/<incident_id>/updates', methods=['POST'])
@jwt_required()
def add_incident_update(incident_id):
    incident = Incident.query.get(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    # Check user permissions for this incident's organization
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user has permission in the incident's organization
    if not user.is_superadmin:
        user_role = user.get_role_in_organization(incident.organization_id)
        if user_role not in ['admin', 'member']:
            return jsonify({'error': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    
    if not data.get('message'):
        return jsonify({'error': 'Update message is required'}), 400
    
    try:
        update = IncidentUpdate(
            incident_id=incident.id,
            user_id=current_user_id,
            status=data.get('status', incident.status),
            message=data['message']
        )
        db.session.add(update)
        
        # Update incident status if provided
        if data.get('status') and data['status'] != incident.status:
            incident.status = data['status']
            if data['status'] in ['resolved', 'completed']:
                incident.resolved_at = datetime.utcnow()
        
        incident.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Emit real-time update
        from app import socketio
        # Emit to organization room
        socketio.emit('incident_update_added', {
            'organization_id': str(incident.organization_id),
            'incident_id': str(incident.id),
            'update': {
                'id': str(update.id),
                'status': update.status,
                'message': update.message,
                'created_at': update.created_at.isoformat()
            }
        }, room=f'org_{incident.organization_id}')
        
        # Also emit to public room
        org = Organization.query.get(incident.organization_id)
        if org:
            socketio.emit('public_incident_update_added', {
                'incident_id': str(incident.id),
                'update': {
                    'id': str(update.id),
                    'status': update.status,
                    'message': update.message,
                    'created_at': update.created_at.isoformat()
                }
            }, room=f'public_{org.slug}')
            print(f"Emitted public_incident_update_added to room: public_{org.slug}")
        
        return jsonify({
            'id': str(update.id),
            'incident_id': str(update.incident_id),
            'status': update.status,
            'message': update.message,
            'created_at': update.created_at.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@incidents_bp.route('/<incident_id>', methods=['DELETE'])
@jwt_required()
def delete_incident(incident_id):
    incident = Incident.query.get(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    # Check user permissions for this incident's organization
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user has admin permission in the incident's organization
    if not user.is_superadmin:
        user_role = user.get_role_in_organization(incident.organization_id)
        if user_role != 'admin':
            return jsonify({'error': 'Only admins can delete incidents'}), 403
    
    org_id = str(incident.organization_id)
    
    try:
        db.session.delete(incident)
        db.session.commit()
        
        # Emit real-time update
        from app import socketio
        socketio.emit('incident_deleted', {
            'organization_id': org_id,
            'incident_id': incident_id
        }, room=f'org_{org_id}')
        
        return jsonify({'message': 'Incident deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
