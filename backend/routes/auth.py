from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from models import db, User, Organization, user_organizations
from sqlalchemy import select

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'username', 'password', 'organization_name']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 400
    
    # Check if organization slug already exists
    org_slug = data.get('organization_slug', data['organization_name'].lower().replace(' ', '-'))
    if Organization.query.filter_by(slug=org_slug).first():
        return jsonify({'error': 'Organization slug already exists'}), 400
    
    try:
        # Create new user
        user = User(
            email=data['email'],
            username=data['username'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', '')
        )
        user.set_password(data['password'])
        db.session.add(user)
        
        # Create new organization
        organization = Organization(
            name=data['organization_name'],
            slug=org_slug,
            description=data.get('organization_description', '')
        )
        db.session.add(organization)
        db.session.flush()  # Get the organization ID
        
        # Add user to organization as admin
        stmt = user_organizations.insert().values(
            user_id=str(user.id),
            organization_id=str(organization.id),
            role='admin'
        )
        db.session.execute(stmt)
        
        db.session.commit()
        
        # Create tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            },
            'organization': {
                'id': str(organization.id),
                'name': organization.name,
                'slug': organization.slug
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    # Find user by email
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is inactive'}), 401
    
    # Get user's organizations
    user_orgs = []
    for org in user.organizations:
        role = user.get_role_in_organization(org.id)
        user_orgs.append({
            'id': str(org.id),
            'name': org.name,
            'slug': org.slug,
            'role': role
        })
    
    # Create tokens
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return jsonify({
        'user': {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_superadmin': user.is_superadmin
        },
        'organizations': user_orgs,
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({'access_token': access_token}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get user's organizations
    user_orgs = []
    for org in user.organizations:
        role = user.get_role_in_organization(org.id)
        user_orgs.append({
            'id': str(org.id),
            'name': org.name,
            'slug': org.slug,
            'role': role
        })
    
    return jsonify({
        'user': {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_superadmin': user.is_superadmin
        },
        'organizations': user_orgs
    }), 200
