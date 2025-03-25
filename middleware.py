import jwt
from flask import request, jsonify, current_app
from config import SECRET_KEY
from functools import wraps
from db import get_db
import time
import logging

logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass

def create_token(user_data, expiry_hours=24):
    """Create a JWT token with standard claims"""
    try:
        payload = {
            "user_id": user_data["id"],
            "email": user_data["email"],
            "role": user_data.get("role", "non_member"),
            "iat": int(time.time()),
            "exp": int(time.time() + expiry_hours * 3600),
            "iss": "gym_management_system",
            "aud": ["gym_members", "dashboard"]
        }
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    except Exception as e:
        logger.error(f"Token creation failed: {str(e)}")
        raise AuthenticationError("Failed to create authentication token")

def verify_token(token):
    """Verify and decode JWT token"""
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_iss": True,
                "verify_aud": True,
                "require": ["exp", "iat", "iss", "aud", "user_id", "email", "role"]
            },
            audience=["gym_members", "dashboard"]
        )
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")

def get_user_data(user_id):
    """Get user data from database"""
    try:
        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, email, role, membership_expiry, auto_payment
                FROM users
                WHERE id = %s
            """, (user_id,))
            user_data = cursor.fetchone()
            cursor.close()
            
            if not user_data:
                raise AuthenticationError("User not found")
            return user_data
    except Exception as e:
        logger.error(f"Database error in get_user_data: {str(e)}")
        raise AuthenticationError("Failed to retrieve user data")

def authenticate(f):
    """Authentication decorator with automatic token refresh"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            # Get token from Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise AuthenticationError("Missing or invalid authorization header")

            token = auth_header.split(" ")[1]
            decoded_token = verify_token(token)
            
            # Get fresh user data from database
            user_data = get_user_data(decoded_token["user_id"])
            
            # Check if membership has expired for members
            if user_data["role"] == "member" and user_data["membership_expiry"]:
                if user_data["membership_expiry"] < time.time():
                    with get_db() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE users SET role = 'non_member' WHERE id = %s",
                            (user_data["id"],)
                        )
                        conn.commit()
                        cursor.close()
                        user_data["role"] = "non_member"
            
            # Create new token if close to expiry (1 hour or less remaining)
            if decoded_token["exp"] - time.time() <= 3600:
                new_token = create_token(user_data)
                response = f(user_data, *args, **kwargs)
                if isinstance(response, tuple):
                    response_data, status_code = response
                    response_data["new_token"] = new_token
                    return jsonify(response_data), status_code
                else:
                    response.headers["X-New-Token"] = new_token
                    return response
            
            return f(user_data, *args, **kwargs)
            
        except AuthenticationError as e:
            logger.warning(f"Authentication failed: {str(e)}")
            return jsonify({"error": str(e)}), 401
        except Exception as e:
            logger.error(f"Unexpected error in authentication: {str(e)}")
            return jsonify({"error": "Authentication failed"}), 401

    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(user_data, *args, **kwargs):
        if user_data.get("role") != "admin":
            logger.warning(f"Unauthorized admin access attempt by user {user_data.get('email')}")
            return jsonify({"error": "Unauthorized - Admins Only"}), 403
        return f(user_data, *args, **kwargs)
    return wrapper

def member_required(f):
    @wraps(f)
    def wrapper(user_data, *args, **kwargs):
        if user_data.get("role") not in ["member", "admin"]:
            logger.warning(f"Unauthorized member access attempt by user {user_data.get('email')}")
            return jsonify({"error": "Unauthorized - Members Only"}), 403
        return f(user_data, *args, **kwargs)
    return wrapper

def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers.update({
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'",
        'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0'
    })
    return response
