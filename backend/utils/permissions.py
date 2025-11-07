from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity
from models import User
import uuid

def require_org_role(allowed_roles):
    """Decorator to check if user has required role in organization"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            org_id = kwargs.get('org_id') or request.args.get('org_id')
            
            if not org_id:
                # Try to get org_id from request body
                data = request.get_json(silent=True)
                if data:
                    org_id = data.get('organization_id')
            
            if not org_id:
                return jsonify({'error': 'Organization ID is required'}), 400
            
            user = User.query.get(current_user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Superadmins have access to everything
            if user.is_superadmin:
                return f(*args, **kwargs)
            
            # Check user's role in the organization
            user_role = user.get_role_in_organization(uuid.UUID(org_id))
            
            if not user_role:
                return jsonify({'error': 'You are not a member of this organization'}), 403
            
            if user_role not in allowed_roles:
                return jsonify({'error': f'Insufficient permissions. Required roles: {allowed_roles}'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_team_role(allowed_roles):
    """Decorator to check if user has required role in team"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from models import Team, TeamMember
            
            current_user_id = get_jwt_identity()
            team_id = kwargs.get('team_id') or request.args.get('team_id')
            
            if not team_id:
                return jsonify({'error': 'Team ID is required'}), 400
            
            user = User.query.get(current_user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Superadmins have access to everything
            if user.is_superadmin:
                return f(*args, **kwargs)
            
            # Get team and check organization role
            team = Team.query.get(team_id)
            if not team:
                return jsonify({'error': 'Team not found'}), 404
            
            # Organization admins have access to all teams
            org_role = user.get_role_in_organization(team.organization_id)
            if org_role == 'admin':
                return f(*args, **kwargs)
            
            # Check team membership
            team_member = TeamMember.query.filter_by(
                team_id=uuid.UUID(team_id),
                user_id=uuid.UUID(current_user_id)
            ).first()
            
            if not team_member:
                return jsonify({'error': 'You are not a member of this team'}), 403
            
            if team_member.role not in allowed_roles:
                return jsonify({'error': f'Insufficient permissions. Required roles: {allowed_roles}'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
