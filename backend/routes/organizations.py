from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Organization, User, user_organizations
from utils.permissions import require_org_role
import uuid

organizations_bp = Blueprint('organizations', __name__)

@organizations_bp.route('', methods=['GET'])
@jwt_required()
def get_user_organizations():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    orgs = []
    for org in user.organizations:
        role = user.get_role_in_organization(org.id)
        orgs.append({
            'id': str(org.id),
            'name': org.name,
            'slug': org.slug,
            'description': org.description,
            'role': role,
            'created_at': org.created_at.isoformat()
        })
    
    return jsonify({'organizations': orgs}), 200

@organizations_bp.route('', methods=['POST'])
@jwt_required()
def create_organization():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'Organization name is required'}), 400
    
    slug = data.get('slug', data['name'].lower().replace(' ', '-'))
    
    # Check if slug already exists
    if Organization.query.filter_by(slug=slug).first():
        return jsonify({'error': 'Organization slug already exists'}), 400
    
    try:
        # Create organization
        org = Organization(
            name=data['name'],
            slug=slug,
            description=data.get('description', '')
        )
        db.session.add(org)
        db.session.flush()
        
        # Add creator as admin
        stmt = user_organizations.insert().values(
            user_id=current_user_id,
            organization_id=org.id,
            role='admin'
        )
        db.session.execute(stmt)
        
        db.session.commit()
        
        return jsonify({
            'id': str(org.id),
            'name': org.name,
            'slug': org.slug,
            'description': org.description,
            'created_at': org.created_at.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@organizations_bp.route('/<org_id>', methods=['GET'])
@jwt_required()
@require_org_role(['admin', 'member', 'viewer'])
def get_organization(org_id):
    org = Organization.query.get(org_id)
    
    if not org:
        return jsonify({'error': 'Organization not found'}), 404
    
    return jsonify({
        'id': str(org.id),
        'name': org.name,
        'slug': org.slug,
        'description': org.description,
        'created_at': org.created_at.isoformat(),
        'services_count': len(org.services),
        'teams_count': len(org.teams),
        'incidents_count': len(org.incidents)
    }), 200

@organizations_bp.route('/<org_id>', methods=['PUT'])
@jwt_required()
@require_org_role(['admin'])
def update_organization(org_id):
    org = Organization.query.get(org_id)
    
    if not org:
        return jsonify({'error': 'Organization not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        org.name = data['name']
    
    if 'description' in data:
        org.description = data['description']
    
    if 'slug' in data and data['slug'] != org.slug:
        # Check if new slug is available
        if Organization.query.filter_by(slug=data['slug']).first():
            return jsonify({'error': 'Slug already exists'}), 400
        org.slug = data['slug']
    
    try:
        db.session.commit()
        return jsonify({
            'id': str(org.id),
            'name': org.name,
            'slug': org.slug,
            'description': org.description
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@organizations_bp.route('/<org_id>', methods=['DELETE'])
@jwt_required()
@require_org_role(['admin'])
def delete_organization(org_id):
    org = Organization.query.get(org_id)
    
    if not org:
        return jsonify({'error': 'Organization not found'}), 404
    
    try:
        db.session.delete(org)
        db.session.commit()
        return jsonify({'message': 'Organization deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@organizations_bp.route('/<org_id>/members', methods=['GET'])
@jwt_required()
@require_org_role(['admin', 'member'])
def get_organization_members(org_id):
    org = Organization.query.get(org_id)
    
    if not org:
        return jsonify({'error': 'Organization not found'}), 404
    
    members = []
    for user in org.users:
        role = user.get_role_in_organization(org_id)
        members.append({
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': role
        })
    
    return jsonify({'members': members}), 200

@organizations_bp.route('/<org_id>/members', methods=['POST'])
@jwt_required()
@require_org_role(['admin'])
def add_organization_member(org_id):
    org = Organization.query.get(org_id)
    
    if not org:
        return jsonify({'error': 'Organization not found'}), 404
    
    data = request.get_json()
    
    if not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400
    
    # Find user by email
    user = User.query.filter_by(email=data['email']).first()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user is already a member
    if user.get_role_in_organization(org_id):
        return jsonify({'error': 'User is already a member'}), 400
    
    role = data.get('role', 'member')
    if role not in ['admin', 'member', 'viewer']:
        return jsonify({'error': 'Invalid role'}), 400
    
    try:
        stmt = user_organizations.insert().values(
            user_id=user.id,
            organization_id=org_id,
            role=role
        )
        db.session.execute(stmt)
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

@organizations_bp.route('/<org_id>/members/<user_id>', methods=['PUT'])
@jwt_required()
@require_org_role(['admin'])
def update_member_role(org_id, user_id):
    data = request.get_json()
    
    if not data.get('role'):
        return jsonify({'error': 'Role is required'}), 400
    
    if data['role'] not in ['admin', 'member', 'viewer']:
        return jsonify({'error': 'Invalid role'}), 400
    
    try:
        stmt = user_organizations.update().where(
            (user_organizations.c.user_id == user_id) &
            (user_organizations.c.organization_id == org_id)
        ).values(role=data['role'])
        
        result = db.session.execute(stmt)
        
        if result.rowcount == 0:
            return jsonify({'error': 'Member not found'}), 404
        
        db.session.commit()
        return jsonify({'message': 'Role updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@organizations_bp.route('/<org_id>/members/<user_id>', methods=['DELETE'])
@jwt_required()
@require_org_role(['admin'])
def remove_organization_member(org_id, user_id):
    current_user_id = get_jwt_identity()
    
    # Prevent self-removal if user is the last admin
    if current_user_id == user_id:
        # Count admins in the organization
        admin_count = db.session.execute(
            db.select(db.func.count()).select_from(user_organizations).where(
                (user_organizations.c.organization_id == org_id) &
                (user_organizations.c.role == 'admin')
            )
        ).scalar()
        
        if admin_count <= 1:
            return jsonify({'error': 'Cannot remove the last admin'}), 400
    
    try:
        stmt = user_organizations.delete().where(
            (user_organizations.c.user_id == user_id) &
            (user_organizations.c.organization_id == org_id)
        )
        
        result = db.session.execute(stmt)
        
        if result.rowcount == 0:
            return jsonify({'error': 'Member not found'}), 404
        
        db.session.commit()
        return jsonify({'message': 'Member removed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
