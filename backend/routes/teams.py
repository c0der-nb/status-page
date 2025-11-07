from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Team, TeamMember, User, Organization
from utils.permissions import require_org_role, require_team_role
import uuid

teams_bp = Blueprint('teams', __name__)

@teams_bp.route('', methods=['GET'])
@jwt_required()
def get_teams():
    org_id = request.args.get('org_id')
    
    if not org_id:
        return jsonify({'error': 'Organization ID is required'}), 400
    
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Check if user has access to this organization
    if not user.is_superadmin and not user.get_role_in_organization(org_id):
        return jsonify({'error': 'Access denied'}), 403
    
    teams = Team.query.filter_by(organization_id=org_id).all()
    
    teams_data = []
    for team in teams:
        teams_data.append({
            'id': str(team.id),
            'name': team.name,
            'description': team.description,
            'members_count': len(team.members),
            'services_count': len(team.services),
            'created_at': team.created_at.isoformat()
        })
    
    return jsonify({'teams': teams_data}), 200

@teams_bp.route('', methods=['POST'])
@jwt_required()
@require_org_role(['admin'])
def create_team():
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'Team name is required'}), 400
    
    if not data.get('organization_id'):
        return jsonify({'error': 'Organization ID is required'}), 400
    
    try:
        team = Team(
            organization_id=data['organization_id'],
            name=data['name'],
            description=data.get('description', '')
        )
        db.session.add(team)
        db.session.flush()
        
        # Add creator as team lead if specified
        if data.get('add_creator', True):
            current_user_id = get_jwt_identity()
            member = TeamMember(
                team_id=team.id,
                user_id=current_user_id,
                role='lead'
            )
            db.session.add(member)
        
        db.session.commit()
        
        return jsonify({
            'id': str(team.id),
            'name': team.name,
            'description': team.description,
            'organization_id': str(team.organization_id),
            'created_at': team.created_at.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@teams_bp.route('/<team_id>', methods=['GET'])
@jwt_required()
@require_team_role(['lead', 'member'])
def get_team(team_id):
    team = Team.query.get(team_id)
    
    if not team:
        return jsonify({'error': 'Team not found'}), 404
    
    members = []
    for member in team.members:
        members.append({
            'id': str(member.user.id),
            'email': member.user.email,
            'username': member.user.username,
            'first_name': member.user.first_name,
            'last_name': member.user.last_name,
            'role': member.role,
            'joined_at': member.joined_at.isoformat()
        })
    
    services = []
    for service in team.services:
        services.append({
            'id': str(service.id),
            'name': service.name,
            'status': service.status
        })
    
    return jsonify({
        'id': str(team.id),
        'name': team.name,
        'description': team.description,
        'organization_id': str(team.organization_id),
        'members': members,
        'services': services,
        'created_at': team.created_at.isoformat()
    }), 200

@teams_bp.route('/<team_id>', methods=['PUT'])
@jwt_required()
@require_team_role(['lead'])
def update_team(team_id):
    team = Team.query.get(team_id)
    
    if not team:
        return jsonify({'error': 'Team not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        team.name = data['name']
    
    if 'description' in data:
        team.description = data['description']
    
    try:
        db.session.commit()
        return jsonify({
            'id': str(team.id),
            'name': team.name,
            'description': team.description
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@teams_bp.route('/<team_id>', methods=['DELETE'])
@jwt_required()
def delete_team(team_id):
    team = Team.query.get(team_id)
    
    if not team:
        return jsonify({'error': 'Team not found'}), 404
    
    # Check if user is org admin
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user.is_superadmin:
        org_role = user.get_role_in_organization(team.organization_id)
        if org_role != 'admin':
            return jsonify({'error': 'Only organization admins can delete teams'}), 403
    
    try:
        db.session.delete(team)
        db.session.commit()
        return jsonify({'message': 'Team deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@teams_bp.route('/<team_id>/members', methods=['POST'])
@jwt_required()
@require_team_role(['lead'])
def add_team_member(team_id):
    team = Team.query.get(team_id)
    
    if not team:
        return jsonify({'error': 'Team not found'}), 404
    
    data = request.get_json()
    
    if not data.get('user_id'):
        return jsonify({'error': 'User ID is required'}), 400
    
    # Check if user exists and is in the organization
    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not user.get_role_in_organization(team.organization_id):
        return jsonify({'error': 'User must be a member of the organization'}), 400
    
    # Check if already a member
    existing = TeamMember.query.filter_by(
        team_id=team_id,
        user_id=data['user_id']
    ).first()
    
    if existing:
        return jsonify({'error': 'User is already a team member'}), 400
    
    role = data.get('role', 'member')
    if role not in ['lead', 'member']:
        return jsonify({'error': 'Invalid role'}), 400
    
    try:
        member = TeamMember(
            team_id=team_id,
            user_id=data['user_id'],
            role=role
        )
        db.session.add(member)
        db.session.commit()
        
        return jsonify({
            'message': 'Member added successfully',
            'member': {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'role': role
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@teams_bp.route('/<team_id>/members/<user_id>', methods=['PUT'])
@jwt_required()
@require_team_role(['lead'])
def update_team_member_role(team_id, user_id):
    member = TeamMember.query.filter_by(
        team_id=team_id,
        user_id=user_id
    ).first()
    
    if not member:
        return jsonify({'error': 'Team member not found'}), 404
    
    data = request.get_json()
    
    if not data.get('role'):
        return jsonify({'error': 'Role is required'}), 400
    
    if data['role'] not in ['lead', 'member']:
        return jsonify({'error': 'Invalid role'}), 400
    
    member.role = data['role']
    
    try:
        db.session.commit()
        return jsonify({'message': 'Role updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@teams_bp.route('/<team_id>/members/<user_id>', methods=['DELETE'])
@jwt_required()
@require_team_role(['lead'])
def remove_team_member(team_id, user_id):
    member = TeamMember.query.filter_by(
        team_id=team_id,
        user_id=user_id
    ).first()
    
    if not member:
        return jsonify({'error': 'Team member not found'}), 404
    
    # Don't allow removing the last lead
    if member.role == 'lead':
        lead_count = TeamMember.query.filter_by(
            team_id=team_id,
            role='lead'
        ).count()
        
        if lead_count <= 1:
            return jsonify({'error': 'Cannot remove the last team lead'}), 400
    
    try:
        db.session.delete(member)
        db.session.commit()
        return jsonify({'message': 'Member removed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
