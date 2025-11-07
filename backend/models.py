from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import uuid
from bcrypt import hashpw, gensalt, checkpw

db = SQLAlchemy()

# Association tables - using String for UUID compatibility with SQLite
user_organizations = db.Table('user_organizations',
    db.Column('user_id', db.String(36), db.ForeignKey('users.id'), primary_key=True),
    db.Column('organization_id', db.String(36), db.ForeignKey('organizations.id'), primary_key=True),
    db.Column('role', db.String(50), default='member'),  # admin, member, viewer
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)

incident_services = db.Table('incident_services',
    db.Column('incident_id', db.String(36), db.ForeignKey('incidents.id'), primary_key=True),
    db.Column('service_id', db.String(36), db.ForeignKey('services.id'), primary_key=True)
)

class Organization(db.Model):
    __tablename__ = 'organizations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    services = db.relationship('Service', backref='organization', lazy=True, cascade='all, delete-orphan')
    incidents = db.relationship('Incident', backref='organization', lazy=True, cascade='all, delete-orphan')
    teams = db.relationship('Team', backref='organization', lazy=True, cascade='all, delete-orphan')
    users = db.relationship('User', secondary=user_organizations, backref='organizations')

class User(db.Model):
    __tablename__ = 'users'
    
    # Use String for SQLite compatibility, UUID for PostgreSQL
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    is_superadmin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team_memberships = db.relationship('TeamMember', backref='user', lazy=True, cascade='all, delete-orphan')
    incident_updates = db.relationship('IncidentUpdate', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def get_role_in_organization(self, org_id):
        """Get user's role in a specific organization"""
        # Ensure org_id is a string for comparison
        org_id_str = str(org_id) if org_id else None
        result = db.session.execute(
            db.select(user_organizations.c.role).where(
                (user_organizations.c.user_id == str(self.id)) &
                (user_organizations.c.organization_id == org_id_str)
            )
        ).first()
        return result[0] if result else None

class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members = db.relationship('TeamMember', backref='team', lazy=True, cascade='all, delete-orphan')
    services = db.relationship('Service', backref='team', lazy=True)

class TeamMember(db.Model):
    __tablename__ = 'team_members'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = db.Column(db.String(36), db.ForeignKey('teams.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(50), default='member')  # lead, member
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    team_id = db.Column(db.String(36), db.ForeignKey('teams.id'))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='operational')  # operational, degraded, partial_outage, major_outage, maintenance
    display_order = db.Column(db.Integer, default=0)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    status_history = db.relationship('ServiceStatusHistory', backref='service', lazy=True, cascade='all, delete-orphan')
    incidents = db.relationship('Incident', secondary=incident_services, backref='affected_services')

class ServiceStatusHistory(db.Model):
    __tablename__ = 'service_status_history'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service_id = db.Column(db.String(36), db.ForeignKey('services.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    changed_by_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    changed_by = db.relationship('User', foreign_keys=[changed_by_id])

class Incident(db.Model):
    __tablename__ = 'incidents'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='investigating')  # investigating, identified, monitoring, resolved
    impact = db.Column(db.String(50), default='none')  # none, minor, major, critical
    type = db.Column(db.String(50), default='incident')  # incident, maintenance
    scheduled_start = db.Column(db.DateTime)  # For maintenance
    scheduled_end = db.Column(db.DateTime)  # For maintenance
    resolved_at = db.Column(db.DateTime)
    created_by_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    updates = db.relationship('IncidentUpdate', backref='incident', lazy=True, cascade='all, delete-orphan')
    created_by = db.relationship('User', foreign_keys=[created_by_id])

class IncidentUpdate(db.Model):
    __tablename__ = 'incident_updates'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = db.Column(db.String(36), db.ForeignKey('incidents.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    status = db.Column(db.String(50))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
