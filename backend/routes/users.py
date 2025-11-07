from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User
import uuid

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': str(user.id),
        'email': user.email,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_active': user.is_active,
        'is_superadmin': user.is_superadmin,
        'created_at': user.created_at.isoformat()
    }), 200

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Update allowed fields
    if 'first_name' in data:
        user.first_name = data['first_name']
    
    if 'last_name' in data:
        user.last_name = data['last_name']
    
    if 'email' in data and data['email'] != user.email:
        # Check if email is already taken
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already in use'}), 400
        user.email = data['email']
    
    if 'username' in data and data['username'] != user.username:
        # Check if username is already taken
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already taken'}), 400
        user.username = data['username']
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@users_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if not data.get('current_password'):
        return jsonify({'error': 'Current password is required'}), 400
    
    if not data.get('new_password'):
        return jsonify({'error': 'New password is required'}), 400
    
    # Verify current password
    if not user.check_password(data['current_password']):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    # Set new password
    user.set_password(data['new_password'])
    
    try:
        db.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@users_bp.route('/search', methods=['GET'])
@jwt_required()
def search_users():
    query = request.args.get('q', '')
    org_id = request.args.get('org_id')
    
    if not query:
        return jsonify({'users': []}), 200
    
    # Search by email or username
    users = User.query.filter(
        db.or_(
            User.email.ilike(f'%{query}%'),
            User.username.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    users_data = []
    for user in users:
        user_data = {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        
        # If org_id provided, include membership status
        if org_id:
            role = user.get_role_in_organization(uuid.UUID(org_id))
            user_data['is_member'] = role is not None
            user_data['role'] = role
        
        users_data.append(user_data)
    
    return jsonify({'users': users_data}), 200
