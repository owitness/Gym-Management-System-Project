from flask import request, jsonify, current_app
import jwt
from config import SECRET_KEY
from functools import wraps
from db import get_db
import time
import logging
from datetime import datetime, timedelta, timezone
import mysql.connector

logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass

def create_token(user_data, expiry_hours=24):
    """Create a JWT token with basic claims"""
    try:
        # Ensure all required fields are present
        required_fields = ['id', 'email', 'role']
        missing_fields = [field for field in required_fields if field not in user_data]
        if missing_fields:
            raise ValueError(f"Missing required fields for token creation: {', '.join(missing_fields)}")

        # Calculate expiration time
        exp_time = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)
        
        # Create token payload with additional metadata
        payload = {
            "user_id": user_data["id"],
            "email": user_data["email"],
            "role": user_data["role"],
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int(exp_time.timestamp()),
            "refresh_token": False  # Indicates this is not a refresh token
        }

        # Encode the token using PyJWT
        token = jwt.encode(
            payload,
            SECRET_KEY,
            algorithm="HS256"
        )
        
        # PyJWT.encode returns bytes in Python 3, convert to string
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        return token

    except Exception as e:
        logger.error(f"Token creation failed: {str(e)}")
        raise AuthenticationError(f"Failed to create authentication token: {str(e)}")

def create_refresh_token(user_data, expiry_days=7):
    """Create a refresh token with longer expiration"""
    try:
        exp_time = datetime.now(timezone.utc) + timedelta(days=expiry_days)
        payload = {
            "user_id": user_data["id"],
            "email": user_data["email"],
            "role": user_data["role"],
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int(exp_time.timestamp()),
            "refresh_token": True  # Indicates this is a refresh token
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        # PyJWT.encode returns bytes in Python 3, convert to string
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        return token
    except Exception as e:
        logger.error(f"Refresh token creation failed: {str(e)}")
        raise AuthenticationError(f"Failed to create refresh token: {str(e)}")

def verify_token(token):
    """Verify and decode JWT token"""
    try:
        if not token:
            raise AuthenticationError("No token provided")

        # Decode and verify the token
        decoded = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

        # Validate token structure
        required_fields = ['user_id', 'email', 'role', 'exp', 'iat']
        missing_fields = [field for field in required_fields if field not in decoded]
        if missing_fields:
            raise AuthenticationError(f"Invalid token structure: missing {', '.join(missing_fields)}")

        # Check expiration
        exp_timestamp = decoded['exp']
        current_timestamp = int(datetime.now(timezone.utc).timestamp())
        if exp_timestamp < current_timestamp:
            raise AuthenticationError("Token has expired")

        return decoded

    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise AuthenticationError(f"Token verification failed: {str(e)}")

def get_user_data(user_id):
    try:
        print(f"DEBUG: Looking up user_id {user_id} in database...")
        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, email, role, membership_expiry, auto_payment FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            print("DEBUG: User fetched =>", result)
            if not result:
                raise AuthenticationError("User not found")
            return result
    except Exception as e:
        logger.error(f"Unexpected error in get_user_data: {str(e)}")
        raise AuthenticationError("Failed to retrieve user data")


# [Previous functions: create_token, create_refresh_token, verify_token, get_user_data unchanged]

def authenticate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            parts = auth_header.split(" ")
            if len(parts) == 2:
                token = parts[1]
        if not token:
            token = request.args.get('token')
        if not token and 'token' in request.cookies:
            token = request.cookies.get('token')
        if not token:
            return jsonify({'error': 'Authentication token is missing'}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = data['user_id']
            user_data = get_user_data(user_id)
            if not user_data:
                return jsonify({'error': 'Authentication failed: User not found'}), 401
            # Pass user_data as a keyword argument
            kwargs['user'] = user_data
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Authentication failed: Token has expired'}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({'error': f'Authentication failed: Invalid token: {str(e)}'}), 401
        except Exception as e:
            return jsonify({'error': f'Authentication failed: {str(e)}'}), 401
    return decorated


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user_data = kwargs.get('user')
        if not user_data:
            return jsonify({"error": "User data not provided"}), 401
        if user_data.get("role") != "admin":
            logger.warning(f"Unauthorized admin access attempt by user {user_data.get('email')}")
            return jsonify({"error": "Unauthorized - Admins Only"}), 403
        return f(*args, **kwargs)
    return wrapper

def member_required(f):
    @wraps(f)
    def wrapper(user, *args, **kwargs):
        if not user:
            return jsonify({"error": "User data not provided"}), 401
        if user.get("role") not in ["member", "admin"]:
            logger.warning(f"Unauthorized member access attempt by user {user.get('email')}")
            return jsonify({"error": "Unauthorized - Members Only"}), 403
        return f(user, *args, **kwargs)
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

def refresh_token(refresh_token):
    """Refresh an expired access token using a refresh token"""
    try:
        decoded = verify_token(refresh_token)
        if not decoded.get('refresh_token'):
            raise AuthenticationError("Invalid refresh token")
        
        user_data = get_user_data(decoded['user_id'])
        new_access_token = create_token(user_data)
        new_refresh_token = create_refresh_token(user_data)
        
        return {
            'access_token': new_access_token,
            'refresh_token': new_refresh_token
        }
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise AuthenticationError(f"Failed to refresh token: {str(e)}")