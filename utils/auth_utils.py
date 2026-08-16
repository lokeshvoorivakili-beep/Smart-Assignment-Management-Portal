import bcrypt
from functools import wraps
from flask import session, jsonify, request

def hash_password(password: str) -> str:
    """Hashes plain text password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verifies plain text password against stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False

def login_required(role=None):
    """
    Decorator for protecting routes.
    Ensures user is logged in and possesses the required role ('student', 'faculty', 'admin').
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or 'user_role' not in session:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': 'Authentication required. Please login.'}), 401
                return jsonify({'success': False, 'message': 'Unauthorized'}), 401
            
            if role and session.get('user_role') != role:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': f'Forbidden. {role.capitalize()} privileges required.'}), 403
                return jsonify({'success': False, 'message': 'Forbidden'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
