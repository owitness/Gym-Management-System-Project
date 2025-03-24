import jwt
from flask import request, jsonify, current_app
from config import SECRET_KEY
from functools import wraps
import time

# 🔹 Verify JWT Token
def authenticate(f):
    @wraps(f)  # ✅ Preserve the original function name
    def wrapper(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization header"}), 401

        token = auth_header.split(" ")[1]
        
        try:
            # Decode and validate token
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            
            # Check token expiration
            if decoded_token.get("exp") < time.time():
                return jsonify({"error": "Token expired"}), 401
                
            # Check token issuer and audience
            if decoded_token.get("iss") != "gym_management_system":
                return jsonify({"error": "Invalid token issuer"}), 401
                
            if decoded_token.get("aud") != "gym_members":
                return jsonify({"error": "Invalid token audience"}), 401
                
            # Log successful authentication
            current_app.logger.info(f"User {decoded_token.get('email')} authenticated successfully")
            
            return f(decoded_token, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            current_app.logger.warning(f"Expired token attempt from IP: {request.remote_addr}")
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError as e:
            current_app.logger.warning(f"Invalid token attempt from IP: {request.remote_addr}, Error: {str(e)}")
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            current_app.logger.error(f"Authentication error: {str(e)}")
            return jsonify({"error": "Authentication failed"}), 401

    return wrapper  # ✅ Function name is preserved

# 🔹 Admin-Only Access
def admin_required(f):
    @wraps(f)  # ✅ Preserve the function name
    def wrapper(user, *args, **kwargs):
        if user.get("role") != "admin":
            current_app.logger.warning(f"Unauthorized admin access attempt by user {user.get('email')}")
            return jsonify({"error": "Unauthorized - Admins Only"}), 403
        return f(user, *args, **kwargs)

    return wrapper  # ✅ Function name is preserved

# 🔹 Member-Only Access
def member_required(f):
    @wraps(f)  # ✅ Preserve the function name
    def wrapper(user, *args, **kwargs):
        if user.get("role") not in ["member", "admin"]:
            current_app.logger.warning(f"Unauthorized member access attempt by user {user.get('email')}")
            return jsonify({"error": "Unauthorized - Members Only"}), 403
        return f(user, *args, **kwargs)

    return wrapper  # ✅ Function name is preserved

# 🔹 Add Security Headers
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
