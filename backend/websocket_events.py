from flask_socketio import emit, join_room, leave_room
from flask_jwt_extended import decode_token
from models import User
import uuid
from datetime import datetime

def register_socketio_events(socketio):
    """Register Socket.IO event handlers"""
    
    @socketio.on('connect')
    def handle_connect(auth):
        """Handle client connection"""
        # Allow unauthenticated connections for public status pages
        if not auth or 'token' not in auth:
            # Allow connection but don't join any authenticated rooms
            emit('connected', {'message': 'Connected to public status updates'})
            return True
        
        try:
            # Decode JWT token for authenticated users
            decoded = decode_token(auth['token'])
            user_id = decoded['sub']
            
            # Verify user exists
            user = User.query.get(user_id)
            if not user:
                return False
            
            # Join user to their personal room
            join_room(f'user_{user_id}')
            
            # Join user to organization rooms
            for org in user.organizations:
                join_room(f'org_{org.id}')
            
            emit('connected', {'message': 'Connected to status updates'})
            return True
            
        except Exception as e:
            print(f'Connection error: {e}')
            return False
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        emit('disconnected', {'message': 'Disconnected from status updates'})
    
    @socketio.on('join_organization')
    def handle_join_organization(data):
        """Join an organization's room for real-time updates"""
        if 'organization_id' not in data:
            emit('error', {'message': 'Organization ID required'})
            return
        
        org_id = data['organization_id']
        room = f'org_{org_id}'
        join_room(room)
        emit('joined', {'message': f'Joined organization {org_id} updates', 'room': room})
    
    @socketio.on('leave_organization')
    def handle_leave_organization(data):
        """Leave an organization's room"""
        if 'organization_id' not in data:
            emit('error', {'message': 'Organization ID required'})
            return
        
        org_id = data['organization_id']
        room = f'org_{org_id}'
        leave_room(room)
        emit('left', {'message': f'Left organization {org_id} updates', 'room': room})
    
    @socketio.on('join_public_status')
    def handle_join_public_status(data):
        """Join a public status page room (no auth required)"""
        if 'org_slug' not in data:
            emit('error', {'message': 'Organization slug required'})
            return
        
        org_slug = data['org_slug']
        room = f'public_{org_slug}'
        join_room(room)
        emit('joined_public', {'message': f'Joined public status updates for {org_slug}', 'room': room})
    
    @socketio.on('leave_public_status')
    def handle_leave_public_status(data):
        """Leave a public status page room"""
        if 'org_slug' not in data:
            emit('error', {'message': 'Organization slug required'})
            return
        
        org_slug = data['org_slug']
        room = f'public_{org_slug}'
        leave_room(room)
        emit('left_public', {'message': f'Left public status updates for {org_slug}', 'room': room})
    
    @socketio.on('ping')
    def handle_ping():
        """Handle ping to keep connection alive"""
        emit('pong', {'timestamp': datetime.utcnow().isoformat()})
