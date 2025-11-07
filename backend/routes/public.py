from flask import Blueprint, request, jsonify
from models import db, Organization, Service, Incident, IncidentUpdate
from datetime import datetime, timedelta

public_bp = Blueprint('public', __name__)

@public_bp.route('/status/<org_slug>', methods=['GET'])
def get_public_status(org_slug):
    """Get public status page data for an organization"""
    org = Organization.query.filter_by(slug=org_slug).first()
    
    if not org:
        return jsonify({'error': 'Organization not found'}), 404
    
    # Get all public services
    services = Service.query.filter_by(
        organization_id=org.id,
        is_public=True
    ).order_by(Service.display_order).all()
    
    services_data = []
    overall_status = 'operational'
    
    for service in services:
        services_data.append({
            'id': str(service.id),
            'name': service.name,
            'description': service.description,
            'status': service.status
        })
        
        # Determine overall status
        if service.status == 'major_outage':
            overall_status = 'major_outage'
        elif service.status == 'partial_outage' and overall_status not in ['major_outage']:
            overall_status = 'partial_outage'
        elif service.status == 'degraded' and overall_status not in ['major_outage', 'partial_outage']:
            overall_status = 'degraded'
        elif service.status == 'maintenance' and overall_status == 'operational':
            overall_status = 'maintenance'
    
    # Get active incidents (unresolved or resolved in last 24 hours)
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    
    active_incidents = Incident.query.filter(
        db.and_(
            Incident.organization_id == org.id,
            db.or_(
                Incident.status.in_(['investigating', 'identified', 'monitoring']),
                db.and_(
                    Incident.status == 'resolved',
                    Incident.resolved_at >= cutoff_time
                )
            )
        )
    ).order_by(Incident.created_at.desc()).all()
    
    incidents_data = []
    for incident in active_incidents:
        # Get latest update
        latest_update = IncidentUpdate.query.filter_by(
            incident_id=incident.id
        ).order_by(IncidentUpdate.created_at.desc()).first()
        
        incidents_data.append({
            'id': str(incident.id),
            'title': incident.title,
            'status': incident.status,
            'impact': incident.impact,
            'type': incident.type,
            'created_at': incident.created_at.isoformat(),
            'resolved_at': incident.resolved_at.isoformat() if incident.resolved_at else None,
            'latest_update': {
                'message': latest_update.message,
                'created_at': latest_update.created_at.isoformat()
            } if latest_update else None,
            'affected_services': [s.name for s in incident.affected_services if s.is_public]
        })
    
    # Get scheduled maintenance
    scheduled_maintenance = Incident.query.filter(
        db.and_(
            Incident.organization_id == org.id,
            Incident.type == 'maintenance',
            Incident.status.in_(['scheduled', 'in_progress']),
            db.or_(
                Incident.scheduled_end == None,
                Incident.scheduled_end > datetime.utcnow()
            )
        )
    ).order_by(Incident.scheduled_start).all()
    
    maintenance_data = []
    for maintenance in scheduled_maintenance:
        maintenance_data.append({
            'id': str(maintenance.id),
            'title': maintenance.title,
            'description': maintenance.description,
            'status': maintenance.status,
            'scheduled_start': maintenance.scheduled_start.isoformat() if maintenance.scheduled_start else None,
            'scheduled_end': maintenance.scheduled_end.isoformat() if maintenance.scheduled_end else None,
            'affected_services': [s.name for s in maintenance.affected_services if s.is_public]
        })
    
    # Get incident history (last 7 days)
    history_cutoff = datetime.utcnow() - timedelta(days=7)
    
    incident_history = Incident.query.filter(
        db.and_(
            Incident.organization_id == org.id,
            Incident.created_at >= history_cutoff
        )
    ).order_by(Incident.created_at.desc()).all()
    
    history_data = []
    for incident in incident_history:
        history_data.append({
            'id': str(incident.id),
            'title': incident.title,
            'type': incident.type,
            'impact': incident.impact,
            'status': incident.status,
            'created_at': incident.created_at.isoformat(),
            'resolved_at': incident.resolved_at.isoformat() if incident.resolved_at else None,
            'duration': str(incident.resolved_at - incident.created_at) if incident.resolved_at else None
        })
    
    return jsonify({
        'organization': {
            'name': org.name,
            'description': org.description
        },
        'overall_status': overall_status,
        'services': services_data,
        'active_incidents': incidents_data,
        'scheduled_maintenance': maintenance_data,
        'incident_history': history_data,
        'last_updated': datetime.utcnow().isoformat()
    }), 200

@public_bp.route('/status/<org_slug>/incidents/<incident_id>', methods=['GET'])
def get_public_incident(org_slug, incident_id):
    """Get public incident details"""
    org = Organization.query.filter_by(slug=org_slug).first()
    
    if not org:
        return jsonify({'error': 'Organization not found'}), 404
    
    incident = Incident.query.filter_by(
        id=incident_id,
        organization_id=org.id
    ).first()
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    # Get all updates
    updates = []
    for update in incident.updates:
        updates.append({
            'id': str(update.id),
            'status': update.status,
            'message': update.message,
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
        'affected_services': [{'name': s.name, 'status': s.status} for s in incident.affected_services if s.is_public],
        'updates': updates,
        'created_at': incident.created_at.isoformat(),
        'updated_at': incident.updated_at.isoformat()
    }), 200

@public_bp.route('/status/<org_slug>/subscribe', methods=['POST'])
def subscribe_to_updates(org_slug):
    """Subscribe to status updates (placeholder for email/SMS notifications)"""
    org = Organization.query.filter_by(slug=org_slug).first()
    
    if not org:
        return jsonify({'error': 'Organization not found'}), 404
    
    data = request.get_json()
    
    if not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400
    
    # TODO: Implement actual subscription logic (email service, database table, etc.)
    # For now, just return success
    
    return jsonify({
        'message': 'Successfully subscribed to status updates',
        'email': data['email']
    }), 200
