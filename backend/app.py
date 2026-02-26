from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_jwt_extended.exceptions import JWTDecodeError, NoAuthorizationError
from datetime import timedelta

from config import Config
from database import Database
from routes.login import login_bp
from routes.upload_data import upload_bp
from routes.structure_data import structure_bp
from routes.entity import entity_bp
from routes.code_master import code_master_bp
from routes.dashboard import dashboard_bp
from routes.forex import forex_bp
from routes.reports import reports_bp
from routes.financial_year_master import financial_year_master_bp

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions with CORS
# Flask-CORS will automatically handle CORS headers for all routes
CORS(app, 
    resources={
        r"/*": {
            "origins": Config.CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "supports_credentials": True,
            "expose_headers": ["Content-Type", "Authorization"]
        }
    },
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    automatic_options=True  # Automatically handle OPTIONS requests
)

# Log incoming requests for debugging
@app.before_request
def log_request():
    origin = request.headers.get('Origin')
    if origin:
        print(f"📡 Request from origin: {origin} - {request.method} {request.path}")

jwt = JWTManager(app)

# JWT Error Handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'success': False,
        'message': 'Token has expired. Please login again.',
        'error': 'Token expired'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    print(f"❌ Invalid JWT token: {error}")
    return jsonify({
        'success': False,
        'message': 'Invalid token. Please login again.',
        'error': str(error)
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    print(f"❌ Missing JWT token: {error}")
    return jsonify({
        'success': False,
        'message': 'Authentication required. Please login again.',
        'error': str(error)
    }), 401

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return False  # Token not in blocklist

# ==================== REGISTER BLUEPRINTS ====================

# Register blueprints - all without /api prefix (handled by reverse proxy)
app.register_blueprint(login_bp, url_prefix='/auth')
app.register_blueprint(upload_bp, url_prefix='/upload')
app.register_blueprint(structure_bp, url_prefix='/structure')
app.register_blueprint(entity_bp, url_prefix='')
app.register_blueprint(code_master_bp, url_prefix='')
app.register_blueprint(forex_bp, url_prefix='')
app.register_blueprint(dashboard_bp, url_prefix='')
app.register_blueprint(reports_bp, url_prefix='')
app.register_blueprint(financial_year_master_bp, url_prefix='')


# ==================== UTILITY ROUTES ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    db_status = Database.test_connection()
    return jsonify({
        'status': 'healthy' if db_status else 'unhealthy',
        'database': 'connected' if db_status else 'disconnected',
        'message': 'API is running'
    }), 200 if db_status else 503


@app.route('/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({
        'success': True,
        'message': 'Backend API is working!'
    }), 200


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'success': False,
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(422)
def unprocessable_entity(e):
    """Handle 422 Unprocessable Entity errors"""
    error_msg = str(e.description) if hasattr(e, 'description') else str(e)
    print(f"❌ 422 Error: {error_msg}")
    return jsonify({
        'success': False,
        'message': 'Request validation failed. Please check your input data.',
        'error': error_msg
    }), 422

@app.errorhandler(401)
def unauthorized(e):
    """Handle 401 Unauthorized errors"""
    error_msg = str(e.description) if hasattr(e, 'description') else str(e)
    print(f"❌ 401 Error: {error_msg}")
    return jsonify({
        'success': False,
        'message': 'Authentication required. Please login again.',
        'error': error_msg
    }), 401

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 Internal Server errors"""
    error_msg = str(e.description) if hasattr(e, 'description') else str(e)
    error_type = type(e).__name__
    print(f"❌ 500 Internal Server Error: {error_type}: {error_msg}")
    
    # In development/debug mode, include more details
    debug_mode = app.config.get('DEBUG', False)
    
    response_data = {
        'success': False,
        'message': 'Internal server error',
        'error_type': error_type
    }
    
    if debug_mode:
        response_data['error_details'] = error_msg
        import traceback
        response_data['traceback'] = traceback.format_exc()
    
    return jsonify(response_data), 500


# ==================== MAIN ====================

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Starting Flask Backend Server")
    print("=" * 50)
    
    # Test database connection on startup
    if Database.test_connection():
        print(f"✅ Server running on http://localhost:{Config.PORT}")
        print(f"✅ Database: {Config.DB_NAME}")
        print(f"✅ CORS Origins: {Config.CORS_ORIGINS}")
        print("=" * 50)
        app.run(
            host='0.0.0.0',
            port=Config.PORT,
            debug=True
        )
    else:
        print("❌ Failed to start server - Database connection failed")
        print("=" * 50)

