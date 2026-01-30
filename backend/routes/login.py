"""
Login routes for authentication
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import traceback

from database import Database

# Create blueprint for login routes
login_bp = Blueprint('login', __name__)


@login_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """Login endpoint for user authentication"""
    try:
        # Handle preflight
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        data = request.get_json()
        print(f"🔐 Login attempt received for: {data.get('username') if data else 'None'}")
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        username = data.get('username') or data.get('email')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Username/email and password are required'
            }), 400
        
        # Query user from database
        query = """
            SELECT user_id, username, email, password, role, ent_id, is_active 
            FROM users 
            WHERE (username = %s OR email = %s) AND is_active = 1
        """
        user = Database.execute_query(query, (username, username), fetch_one=True)
        
        if not user:
            print(f"❌ User not found: {username}")
            return jsonify({
                'success': False,
                'message': 'Invalid credentials'
            }), 401
        
        # Verify password (plain text comparison)
        stored_password = user['password'] or ''
        password_match = (stored_password == password)
        print(f"🔑 Password check for {username}: {'✅ Match' if password_match else '❌ No match'}")
        if stored_password:
            print(f"   Stored password: {stored_password[:5]}..., Provided: {password[:5] if password else 'None'}...")
        
        if not password_match:
            print(f"❌ Invalid password for user: {username}")
            return jsonify({
                'success': False,
                'message': 'Invalid credentials'
            }), 401
        
        print(f"✅ Login successful for user: {username} (ID: {user['user_id']})")
        
        # Create access token
        # Convert user_id to string - Flask-JWT-Extended requires identity to be a string
        access_token = create_access_token(
            identity=str(user['user_id']),
            additional_claims={
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'ent_id': user.get('ent_id')
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'data': {
                'token': access_token,
                'user': {
                    'id': user['user_id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role'],
                    'ent_id': user.get('ent_id')
                }
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'An error occurred during login'
        }), 500


@login_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json()
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'VIEWER')  # Default to VIEWER
        ent_id = data.get('ent_id', None)
        
        if not all([username, email, password]):
            return jsonify({
                'success': False,
                'message': 'Username, email, and password are required'
            }), 400
        
        # Validate role
        valid_roles = ['ADMIN', 'ANALYST', 'VIEWER']
        if role.upper() not in valid_roles:
            return jsonify({
                'success': False,
                'message': f'Invalid role. Must be one of: {", ".join(valid_roles)}'
            }), 400
        
        role = role.upper()
        
        # Check if user already exists
        check_query = "SELECT user_id FROM users WHERE username = %s OR email = %s"
        existing_user = Database.execute_query(check_query, (username, email), fetch_one=True)
        
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Username or email already exists'
            }), 409
        
        # Store password as plain text (no hashing)
        # Insert new user
        insert_query = """
            INSERT INTO users (username, email, password, role, ent_id, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        user_id = Database.execute_query(
            insert_query, 
            (username, email, password, role, ent_id, 1)
        )
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'data': {
                'user_id': user_id
            }
        }), 201
        
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'An error occurred during registration'
        }), 500


@login_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """Verify JWT token and return user info"""
    try:
        current_user_id = get_jwt_identity()
        
        query = """
            SELECT user_id, username, email, role, ent_id 
            FROM users 
            WHERE user_id = %s AND is_active = 1
        """
        user = Database.execute_query(query, (current_user_id,), fetch_one=True)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'id': user['user_id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role'],
                    'ent_id': user.get('ent_id')
                }
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Token verification error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401


@login_bp.route('/logout', methods=['POST', 'OPTIONS'])
def logout():
    """Logout endpoint - allows logout without requiring valid token"""
    try:
        # Handle preflight
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        # Try to get user ID from token (optional - don't require valid token)
        # Logout should work even with invalid/expired tokens
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                # Try to decode token, but don't fail if it's invalid
                from flask_jwt_extended import decode_token
                token = auth_header.replace('Bearer ', '')
                decoded = decode_token(token)
                user_id = decoded.get('sub')
                if user_id:
                    print(f"🚪 Logout request from user ID: {user_id}")
            except Exception as e:
                # Token is invalid/expired - that's fine for logout
                print(f"🚪 Logout request (token invalid/expired: {str(e)}) - allowing logout anyway")
        else:
            print(f"🚪 Logout request (no token provided)")
        
        # Note: With JWT, we typically handle logout on the client side by removing the token
        # Logout endpoint is mainly for server-side logging/blacklisting if needed
        
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        print(f"❌ Logout error: {str(e)}")
        # Even if there's an error, we can still allow logout
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        }), 200

