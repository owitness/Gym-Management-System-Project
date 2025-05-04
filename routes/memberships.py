from flask import Blueprint, jsonify, request, current_app
from db import get_db
from middleware import authenticate, admin_required
from datetime import datetime, timedelta
import logging

memberships_bp = Blueprint("memberships", __name__)
logger = logging.getLogger(__name__)

# Membership configurations
MEMBERSHIP_TYPES = {
    'monthly': {
        'price': 30.00,
        'duration': 1,  # months
        'description': 'Monthly membership with full gym access'
    },
    'annual': {
        'price': 300.00,
        'duration': 12,  # months
        'description': 'Annual membership with full gym access (save $100!)'
    },
    'student': {
        'price': 20.00,
        'duration': 1,  # months
        'description': 'Student membership with full gym access (valid student ID required)'
    }
}

# 🔹 Get all membership types and pricing
@memberships_bp.route("/membership-types", methods=["GET"])
def get_membership_types():
    """Get all membership types"""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM membership_types 
            ORDER BY price ASC
        """)
        
        membership_types = cursor.fetchall()
        cursor.close()
        
        return jsonify(membership_types)

    except Exception as e:
        logger.error(f"Error in get_membership_types: {str(e)}")
        return jsonify({"error": "Failed to fetch membership types"}), 500

# 🔹 Get user's current membership
@memberships_bp.route("/memberships/my-membership", methods=["GET"])
@authenticate
def get_my_membership(user):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        # For regular users, get their membership
        cursor.execute("""
            SELECT * FROM memberships 
            WHERE user_id = %s 
            ORDER BY start_date DESC 
            LIMIT 1
        """, (user["id"],))
        
        membership = cursor.fetchone()
        cursor.close()

        if not membership:
            return jsonify({"message": "No active membership found"}), 404

        return jsonify(membership)

    except Exception as e:
        logger.error(f"Error in get_my_membership: {str(e)}")
        return jsonify({"error": "Failed to fetch membership"}), 500

# 🔹 Purchase new membership
@memberships_bp.route("/memberships/purchase", methods=["POST"])
@authenticate
def purchase_membership(user):
    data = request.json
    membership_type = data.get("membership_type")
    payment_method_id = data.get("payment_method_id")
    
    if membership_type not in MEMBERSHIP_TYPES:
        return jsonify({"error": "Invalid membership type"}), 400
        
    membership_info = MEMBERSHIP_TYPES[membership_type]
    expiry_date = datetime.now() + timedelta(days=30 * membership_info['duration'])
    
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            # Start transaction
            conn.start_transaction()
            
            # Create payment record
            cursor.execute("""
                INSERT INTO payments (user_id, amount, status, payment_method_id, 
                                    membership_duration, membership_expiry)
                VALUES (%s, %s, 'Completed', %s, %s, %s)
            """, (user["id"], membership_info["price"], payment_method_id, 
                  membership_info["duration"], expiry_date))
            
            # Update or create membership
            cursor.execute("""
                INSERT INTO memberships (member_id, start_date, expiry_date, status)
                VALUES (%s, NOW(), %s, 'active')
                ON DUPLICATE KEY UPDATE 
                    expiry_date = %s,
                    status = 'active'
            """, (user["id"], expiry_date, expiry_date))
            
            # Update user role to member and set membership_expiry
            cursor.execute("""
                UPDATE users 
                SET role = 'member', membership_expiry = %s, auto_payment = 1
                WHERE id = %s
            """, (expiry_date, user["id"]))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Membership purchased successfully for user {user['id']}: {membership_type} until {expiry_date}")
            
            return jsonify({
                "message": "Membership purchased successfully!",
                "expiry_date": expiry_date.strftime("%Y-%m-%d"),
                "amount_paid": membership_info["price"]
            })
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Membership purchase failed: {str(e)}")
            return jsonify({"error": "Failed to process membership purchase"}), 500

# 🔹 Admin: Get all memberships
@memberships_bp.route("/admin/memberships", methods=["GET"])
@authenticate
@admin_required
def get_all_memberships(user):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.*, u.name, u.email, u.role
            FROM memberships m
            JOIN users u ON m.member_id = u.id
            ORDER BY m.start_date DESC
        """)
        memberships = cursor.fetchall()
        cursor.close()
        return jsonify(memberships)

    except Exception as e:
        logger.error(f"Error in get_all_memberships: {str(e)}")
        return jsonify({"error": "Failed to fetch memberships"}), 500

# 🔹 Admin: Update membership status
@memberships_bp.route("/admin/memberships/<int:membership_id>", methods=["PUT"])
@authenticate
@admin_required
def update_membership_status(user, membership_id):
    data = request.json
    new_status = data.get("status")
    
    if new_status not in ["active", "expired", "cancelled"]:
        return jsonify({"error": "Invalid status"}), 400
        
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE memberships 
            SET status = %s 
            WHERE id = %s
        """, (new_status, membership_id))
        
        if new_status != "active":
            cursor.execute("""
                UPDATE users u
                JOIN memberships m ON u.id = m.member_id
                SET u.role = 'non_member'
                WHERE m.id = %s
            """, (membership_id,))
            
        conn.commit()
        cursor.close()
        
        return jsonify({"message": f"Membership status updated to {new_status}"})

@memberships_bp.route("/memberships", methods=["GET"])
@authenticate
def get_memberships(user):
    """Get all memberships for admin or a specific user's membership"""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        if user.get("role") == "admin":
            cursor.execute("""
                SELECT m.*, u.email, u.first_name, u.last_name 
                FROM memberships m 
                JOIN users u ON m.user_id = u.id
                ORDER BY m.start_date DESC
            """)
            memberships = cursor.fetchall()
            cursor.close()
            return jsonify(memberships)

        # For regular users, get their membership
        cursor.execute("""
            SELECT * FROM memberships 
            WHERE user_id = %s 
            ORDER BY start_date DESC 
            LIMIT 1
        """, (user["id"],))
        
        membership = cursor.fetchone()
        cursor.close()

        if not membership:
            return jsonify({"message": "No active membership found"}), 404

        return jsonify(membership)

    except Exception as e:
        logger.error(f"Error in get_memberships: {str(e)}")
        return jsonify({"error": "Failed to fetch memberships"}), 500

@memberships_bp.route("/memberships", methods=["POST"])
@authenticate
def create_membership(user):
    """Create a new membership"""
    try:
        data = request.get_json()
        required_fields = ["type", "duration", "price", "user_id"]
        
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)

        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE id = %s", (data["user_id"],))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "User not found"}), 404

        # Check if user already has an active membership
        cursor.execute("""
            SELECT * FROM memberships 
            WHERE user_id = %s AND end_date > CURDATE()
        """, (data["user_id"],))
        
        if cursor.fetchone():
            cursor.close()
            return jsonify({"error": "User already has an active membership"}), 400

        # Create new membership
        cursor.execute("""
            INSERT INTO memberships (user_id, type, duration, price, start_date, end_date)
            VALUES (%s, %s, %s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL %s DAY))
        """, (data["user_id"], data["type"], data["duration"], data["price"], data["duration"]))
        
        db.commit()
        membership_id = cursor.lastrowid

        # Fetch the created membership
        cursor.execute("SELECT * FROM memberships WHERE id = %s", (membership_id,))
        new_membership = cursor.fetchone()
        cursor.close()

        return jsonify(new_membership), 201

    except Exception as e:
        logger.error(f"Error in create_membership: {str(e)}")
        return jsonify({"error": "Failed to create membership"}), 500

@memberships_bp.route("/memberships/<int:membership_id>", methods=["DELETE"])
@authenticate
def delete_membership(user, membership_id):
    """Delete a membership (admin only)"""
    if user.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    try:
        db = get_db()
        cursor = db.cursor()

        # Check if membership exists
        cursor.execute("SELECT id FROM memberships WHERE id = %s", (membership_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Membership not found"}), 404

        # Delete membership
        cursor.execute("DELETE FROM memberships WHERE id = %s", (membership_id,))
        db.commit()
        cursor.close()

        return jsonify({"message": "Membership deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error in delete_membership: {str(e)}")
        return jsonify({"error": "Failed to delete membership"}), 500
    
@memberships_bp.route("/memberships/cancel", methods=["POST"])
@authenticate
def cancel_and_delete_user(user):
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # 🛠 1. Delete class bookings
            cursor.execute("""
                DELETE FROM class_bookings
                WHERE member_id = %s
            """, (user["id"],))

            # 🛠 2. Delete attendance records
            cursor.execute("""
                DELETE FROM attendance
                WHERE member_id = %s
            """, (user["id"],))

            # 🛠 3. Delete payments (FIRST, before payment methods)
            cursor.execute("""
                DELETE FROM payments
                WHERE user_id = %s
            """, (user["id"],))

            # 🛠 4. Delete payment methods (now safe)
            cursor.execute("""
                DELETE FROM payment_methods
                WHERE user_id = %s
            """, (user["id"],))

            # 🛠 5. Delete memberships
            cursor.execute("""
                DELETE FROM memberships
                WHERE member_id = %s
            """, (user["id"],))

            # 🛠 6. Delete user account
            cursor.execute("""
                DELETE FROM users
                WHERE id = %s
            """, (user["id"],))

            conn.commit()

            return jsonify({"message": "Membership and user account deleted successfully."})

    except Exception as e:
        current_app.logger.error(f"Error deleting user {user['id']}: {str(e)}")
        return jsonify({"error": "Failed to delete account"}), 500


    
