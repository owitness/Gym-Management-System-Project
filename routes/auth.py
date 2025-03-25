from flask import Blueprint, request, jsonify, current_app
from db import get_db
import bcrypt
from datetime import datetime
from middleware import create_token, authenticate, AuthenticationError
import logging
import re

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, None

@auth_bp.route("/register", methods=["POST"])
def register_user():
    try:
        data = request.json
        required_fields = ['name', 'email', 'password', 'dob', 'address', 'city', 'state', 'zipcode']
        
        # Validate required fields
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        # Validate email format
        if not validate_email(data['email']):
            return jsonify({"error": "Invalid email format"}), 400

        # Validate password strength
        is_valid, password_error = validate_password(data['password'])
        if not is_valid:
            return jsonify({"error": password_error}), 400

        # Hash password
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Check if email exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (data['email'],))
            if cursor.fetchone():
                return jsonify({"error": "Email already exists"}), 400

            # Insert new user
            cursor.execute("""
                INSERT INTO users (
                    name, email, password, role, dob, address, city, state, zipcode,
                    auto_payment, created_at
                ) VALUES (%s, %s, %s, 'non_member', %s, %s, %s, %s, %s, %s, NOW())
            """, (
                data['name'], data['email'], hashed_password, data['dob'],
                data['address'], data['city'], data['state'], data['zipcode'],
                data.get('auto_payment', False)
            ))
            conn.commit()
            
            # Get the new user's data
            user_id = cursor.lastrowid
            cursor.execute("""
                SELECT id, email, role, membership_expiry, auto_payment
                FROM users WHERE id = %s
            """, (user_id,))
            user_data = cursor.fetchone()
            
            # Create token
            token = create_token(user_data)
            
            logger.info(f"User registered successfully: {data['email']}")
            return jsonify({
                "message": "Registration successful",
                "token": token,
                "user": {
                    "id": user_data['id'],
                    "email": user_data['email'],
                    "role": user_data['role']
                }
            }), 201

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": "Registration failed. Please try again."}), 500

@auth_bp.route("/login", methods=["POST"])
def login_user():
    try:
        data = request.json
        if not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email and password are required"}), 400

        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Get user data
            cursor.execute("""
                SELECT id, email, password, role, membership_expiry, auto_payment
                FROM users WHERE email = %s
            """, (data['email'],))
            user = cursor.fetchone()

            if not user:
                logger.warning(f"Login attempt with non-existent email: {data['email']}")
                return jsonify({"error": "Invalid email or password"}), 401

            # Verify password
            if not bcrypt.checkpw(data['password'].encode('utf-8'), user['password'].encode('utf-8')):
                logger.warning(f"Failed login attempt for user: {data['email']}")
                return jsonify({"error": "Invalid email or password"}), 401

            # Check membership expiry
            if user['role'] == 'member' and user['membership_expiry']:
                if user['membership_expiry'] < datetime.now():
                    cursor.execute(
                        "UPDATE users SET role = 'non_member' WHERE id = %s",
                        (user['id'],)
                    )
                    conn.commit()
                    user['role'] = 'non_member'

            # Create token
            token = create_token(user)
            
            logger.info(f"User {data['email']} logged in successfully")
            return jsonify({
                "message": "Login successful",
                "token": token,
                "user": {
                    "id": user['id'],
                    "email": user['email'],
                    "role": user['role']
                }
            }), 200

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "Login failed. Please try again."}), 500

@auth_bp.route("/profile", methods=["GET"])
@authenticate
def get_user_profile(user_data):
    try:
        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, name, email, role, dob, address, city, state, zipcode,
                       membership_expiry, auto_payment, created_at
                FROM users WHERE id = %s
            """, (user_data['id'],))
            profile = cursor.fetchone()

            if not profile:
                return jsonify({"error": "User not found"}), 404

            # Remove sensitive data
            profile.pop('password', None)
            
            return jsonify(profile), 200

    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        return jsonify({"error": "Failed to fetch profile"}), 500

@auth_bp.route("/logout", methods=["POST"])
@authenticate
def logout_user(user_data):
    # Since we're using JWTs, we don't need to do anything server-side
    # The client should remove the token
    logger.info(f"User {user_data['email']} logged out")
    return jsonify({"message": "Logged out successfully"}), 200

