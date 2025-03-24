from flask import Blueprint, request, jsonify, current_app
from db import get_db_connection
import bcrypt
import jwt
import datetime
from config import SECRET_KEY
from middleware import authenticate, admin_required
from functools import wraps
import re

auth_bp = Blueprint("auth", __name__)

# Rate limiting decorator
def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        key = f"rate_limit:{ip}:{request.endpoint}"
        
        # Get current timestamp
        now = datetime.datetime.utcnow()
        
        # Get existing attempts from Redis or similar
        # For now, we'll use a simple in-memory solution
        if not hasattr(current_app, 'rate_limits'):
            current_app.rate_limits = {}
            
        if key in current_app.rate_limits:
            attempts, timestamp = current_app.rate_limits[key]
            if (now - timestamp).seconds < 300:  # 5 minutes window
                if attempts >= 5:  # Max 5 attempts
                    return jsonify({"error": "Too many attempts. Please try again later."}), 429
                current_app.rate_limits[key] = (attempts + 1, now)
            else:
                current_app.rate_limits[key] = (1, now)
        else:
            current_app.rate_limits[key] = (1, now)
            
        return f(*args, **kwargs)
    return decorated_function

# Input validation
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    # At least 8 characters, 1 uppercase, 1 lowercase, 1 number
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$'
    return re.match(pattern, password) is not None

# 🔹 Register New User (Always Starts as 'non_member')
@auth_bp.route("/register", methods=["POST"])
@rate_limit
def register_user():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    dob = data.get("dob")
    address = data.get("address")
    city = data.get("city")
    state = data.get("state")
    zipcode = data.get("zipcode")
    auto_payment = data.get("auto_payment", False)

    # Validate required fields
    if not all([name, email, password]):
        return jsonify({"error": "Missing required fields"}), 400

    # Validate email format
    if not validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    # Validate password strength
    if not validate_password(password):
        return jsonify({
            "error": "Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one number"
        }), 400

    # Hash the password with increased work factor for better security
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "Email already exists!"}), 400

        # Insert new user with all fields
        cursor.execute("""
            INSERT INTO users (name, email, password, role, dob, address, city, state, zipcode, auto_payment, created_at)
            VALUES (%s, %s, %s, 'non_member', %s, %s, %s, %s, %s, %s, NOW())
        """, (name, email, hashed_pw, dob, address, city, state, zipcode, auto_payment))
        
        conn.commit()
        return jsonify({"message": "User registered successfully! You need to pay for a membership to become a member."}), 201
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Registration failed: {str(e)}")
        return jsonify({"error": "Registration failed. Please try again later."}), 500
    finally:
        cursor.close()
        conn.close()

# 🔹 User Login (Returns JWT Token)
@auth_bp.route("/login", methods=["POST"])
@rate_limit
def login_user():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Validate email format
    if not validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get user with all necessary fields
        cursor.execute("""
            SELECT id, email, password, role, membership_expiry, auto_payment 
            FROM users 
            WHERE email = %s
        """, (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "Invalid email or password"}), 401

        # Verify password
        if not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
            return jsonify({"error": "Invalid email or password"}), 401

        # Check membership expiry
        if user["role"] == "member" and user["membership_expiry"]:
            expiry_date = user["membership_expiry"]
            if expiry_date < datetime.datetime.now():
                # Update role to non_member if membership expired
                cursor.execute("UPDATE users SET role = 'non_member' WHERE id = %s", (user["id"],))
                conn.commit()
                user["role"] = "non_member"

        # Generate JWT token with additional claims
        token = jwt.encode(
            {
                "id": user["id"],
                "role": user["role"],
                "email": user["email"],
                "auto_payment": user["auto_payment"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        # Log successful login
        current_app.logger.info(f"User {email} logged in successfully")

        return jsonify({
            "token": token,
            "role": user["role"],
            "message": "Login successful"
        }), 200

    except Exception as e:
        current_app.logger.error(f"Login failed: {str(e)}")
        return jsonify({"error": "Login failed. Please try again later."}), 500
    finally:
        cursor.close()
        conn.close()

# 🔹 Get User Profile (Requires Authentication)
@auth_bp.route("/profile", methods=["GET"])
@authenticate
def get_user_profile(user):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, name, email, role, dob, address, city, state, zipcode, 
                   membership_expiry, auto_payment, created_at 
            FROM users 
            WHERE id = %s
        """, (user["id"],))
        user_info = cursor.fetchone()

        if not user_info:
            return jsonify({"error": "User not found"}), 404

        # Remove sensitive information
        user_info.pop("password", None)
        return jsonify(user_info)

    except Exception as e:
        return jsonify({"error": f"Failed to fetch profile: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

# 🔹 Admin-Only: Change User Role
@auth_bp.route("/users/<int:user_id>/role", methods=["PUT"])
@authenticate
@admin_required
def update_user_role(user, user_id):
    data = request.json
    new_role = data.get("role")

    if not new_role or new_role not in ["admin", "member", "non_member"]:
        return jsonify({"error": "Invalid role"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
        conn.commit()
        return jsonify({"message": f"User {user_id} role updated to {new_role}."})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Failed to update role: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

