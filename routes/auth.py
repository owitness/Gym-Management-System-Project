from flask import Blueprint, request, jsonify, current_app
from db import get_db
import bcrypt
from datetime import datetime
import jwt
from middleware import create_token, authenticate, AuthenticationError, refresh_token as refresh_token_func
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
        if not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email and password are required"}), 400

        # Validate email format
        if not validate_email(data['email']):
            return jsonify({"error": "Invalid email format"}), 400

        # Validate password strength
        is_valid, error_msg = validate_password(data['password'])
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (data['email'],))
            if cursor.fetchone():
                return jsonify({"error": "Email already registered"}), 400

            # Hash password
            hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
            
            # Insert new user
            cursor.execute("""
                INSERT INTO users (email, password, role, name, dob, address, city, state, zipcode, auto_payment)
                VALUES (%s, %s, 'non_member', %s, %s, %s, %s, %s, %s, %s)
            """, (
                data['email'],
                hashed_password.decode('utf-8'),
                data.get('name'),
                data.get('dob'),
                data.get('address'),
                data.get('city'),
                data.get('state'),
                data.get('zipcode'),
                data.get('auto_payment', True)
            ))
            
            user_id = cursor.lastrowid

            # If payment information is provided, add payment method
            if data.get('card_number') and data.get('exp') and data.get('cvv'):
                cursor.execute("""
                    INSERT INTO payment_methods (user_id, card_number, exp, cvv, card_holder_name, saved)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    data['card_number'],
                    data['exp'],
                    data['cvv'],
                    data['card_holder_name'],
                    True
                ))
                payment_method_id = cursor.lastrowid
            else:
                payment_method_id = None

            # Handle membership creation based on membership_type
            if data.get('membership_type'):
                # Determine membership duration based on type
                membership_duration = 1  # Default to 1 month
                if data['membership_type'] == 'annual':
                    membership_duration = 12
                
                # Calculate membership amount based on type
                amount = 30.00  # Default monthly price
                if data['membership_type'] == 'annual':
                    amount = 300.00
                elif data['membership_type'] == 'student':
                    amount = 20.00

                # Set start and expiry dates
                from datetime import datetime, timedelta
                start_date = datetime.now().date()
                if data['membership_type'] == 'annual':
                    # Use actual year calculation for annual membership (365 days)
                    expiry_date = start_date.replace(year=start_date.year + 1)
                else:
                    # For other membership types, use 30 days per month
                    expiry_date = start_date + timedelta(days=30 * membership_duration)
                
                # Insert new membership
                cursor.execute("""
                    INSERT INTO memberships (member_id, start_date, expiry_date, status)
                    VALUES (%s, %s, %s, 'active')
                """, (user_id, start_date, expiry_date))

                # Create payment record
                cursor.execute("""
                    INSERT INTO payments (user_id, amount, status, payment_method_id, 
                                         membership_duration, membership_expiry)
                    VALUES (%s, %s, 'Completed', %s, %s, %s)
                """, (user_id, amount, payment_method_id, membership_duration, expiry_date))

                # Update user role to member and set membership_expiry
                cursor.execute("""
                    UPDATE users SET role = 'member', membership_expiry = %s WHERE id = %s
                """, (expiry_date, user_id))

            conn.commit()

            # Get the newly created user
            cursor.execute("""
                SELECT id, email, role, membership_expiry, auto_payment
                FROM users WHERE id = %s
            """, (user_id,))
            user = cursor.fetchone()

            # Create token
            token = create_token(user)
            
            # Set session data
            from flask import session
            session.clear()  # Clear any existing session first
            session['user_id'] = user['id']
            session['email'] = user['email']
            session['role'] = user['role']
            session.permanent = True
            
            logger.info(f"New user registered: {data['email']}")
            return jsonify({
                "message": "Registration successful",
                "token": token,
                "access_token": token,
                "user": {
                    "id": user['id'],
                    "email": user['email'],
                    "role": user['role']
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
            
            # Clear any existing session data first
            from flask import session
            session.clear()
            
            # Set session data
            session['user_id'] = user['id']
            session['email'] = user['email']
            session['role'] = user['role']
            session.permanent = True
            
            logger.info(f"User {data['email']} logged in successfully")
            return jsonify({
                "message": "Login successful",
                "token": token,
                "access_token": token,
                "role": user['role'],
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
def logout_user(user):
    try:
        # Clear server-side session
        from flask import session
        session.clear()
        
        # In a production app, you might also:
        # 1. Invalidate refresh tokens in the database
        # 2. Add the token to a blacklist
        
        return jsonify({"message": "Successfully logged out"}), 200
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({"error": "Logout failed. Please try again."}), 500

@auth_bp.route("/refresh-token", methods=["POST"])
def refresh_token_endpoint():
    try:
        refresh_token = request.json.get('refresh_token')
        if not refresh_token:
            return jsonify({'error': 'Refresh token is required'}), 400
        
        tokens = refresh_token_func(refresh_token)
        return jsonify(tokens)
    except AuthenticationError as e:
        return jsonify({'error': str(e)}), 401

@auth_bp.route("/verify-token", methods=["GET"])
def verify_token_endpoint():
    # The token is already verified in the middleware
    # Just return success if we get here
    return jsonify({"valid": True}), 200

