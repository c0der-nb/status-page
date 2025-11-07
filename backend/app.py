import os
from datetime import timedelta
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from dotenv import load_dotenv

from models import db
from routes.auth import auth_bp
from routes.organizations import organizations_bp
from routes.teams import teams_bp
from routes.services import services_bp
from routes.incidents import incidents_bp
from routes.public import public_bp
from routes.users import users_bp
from websocket_events import register_socketio_events

# Load environment variables
load_dotenv()

# Initialize SocketIO globally
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    # Use SQLite for development, PostgreSQL for production
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///statuspage.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    app.config['PROPAGATE_EXCEPTIONS'] = True  # Ensure exceptions are handled by our handlers
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt = JWTManager(app)
    
    # JWT error handlers to ensure CORS headers are included
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        response = jsonify({'error': 'Token has expired'})
        response.status_code = 401
        return response
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        response = jsonify({'error': 'Invalid token'})
        response.status_code = 422
        return response
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        response = jsonify({'error': 'Authorization header missing'})
        response.status_code = 401
        return response
    
    # Configure CORS - simplified to avoid conflicts with after_request
    # We'll handle CORS mainly in after_request to ensure it's always applied
    
    # Initialize SocketIO with app
    socketio.init_app(app)
    register_socketio_events(socketio)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(organizations_bp, url_prefix='/api/organizations')
    app.register_blueprint(teams_bp, url_prefix='/api/teams')
    app.register_blueprint(services_bp, url_prefix='/api/services')
    app.register_blueprint(incidents_bp, url_prefix='/api/incidents')
    app.register_blueprint(public_bp, url_prefix='/api/public')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    # Handle OPTIONS requests for CORS preflight
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
            response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
            return response
    
    # Ensure CORS headers are added to all responses
    @app.after_request
    def after_request(response):
        # Always add CORS headers for API routes
        if request.path.startswith('/api/'):
            origin = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
            response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
        return response
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden'}), 403
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized'}), 401
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        response = jsonify({'error': 'Internal server error', 'message': str(error)})
        response.status_code = 500
        return response
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        # Log the error
        app.logger.error(f"Unhandled exception: {error}")
        db.session.rollback()
        response = jsonify({'error': 'Internal server error', 'message': str(error)})
        response.status_code = 500
        return response
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

# Create Flask app instance
app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=False, port=5008, allow_unsafe_werkzeug=True)
