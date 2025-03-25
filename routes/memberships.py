from flask import Blueprint, jsonify, request, current_app
from db import get_db
from middleware import authenticate, admin_required
from datetime import datetime, timedelta

memberships_bp = Blueprint("memberships", __name__)

# Membership configurations
MEMBERSHIP_TYPES = {
    'monthly': {
        'price': 50.00,
        'duration': 1,  # months
        'description': 'Monthly membership with full gym access'
    },
    'annual': {
        'price': 500.00,
        'duration': 12,  # months
        'description': 'Annual membership with full gym access (save $100!)'
    },
    'student': {
        'price': 40.00,
        'duration': 1,  # months
        'description': 'Student membership with full gym access (valid student ID required)'
    }
}

# 🔹 Get all membership types and pricing
@memberships_bp.route("/membership-types", methods=["GET"])
def get_membership_types():
    return jsonify(MEMBERSHIP_TYPES)

# 🔹 Get user's current membership
@memberships_bp.route("/memberships/my-membership", methods=["GET"])
@authenticate
def get_my_membership(user):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.*, u.role, u.auto_payment
            FROM memberships m
            JOIN users u ON m.member_id = u.id
            WHERE m.member_id = %s AND m.status = 'active'
        """, (user["id"],))
        
        membership = cursor.fetchone()
        cursor.close()
        return jsonify(membership if membership else {"error": "No active membership found"})

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
            
            # Update user role to member
            cursor.execute("""
                UPDATE users 
                SET role = 'member', membership_expiry = %s 
                WHERE id = %s
            """, (expiry_date, user["id"]))
            
            conn.commit()
            cursor.close()
            return jsonify({
                "message": "Membership purchased successfully!",
                "expiry_date": expiry_date.strftime("%Y-%m-%d"),
                "amount_paid": membership_info["price"]
            })
            
        except Exception as e:
            conn.rollback()
            current_app.logger.error(f"Membership purchase failed: {str(e)}")
            return jsonify({"error": "Failed to process membership purchase"}), 500

# 🔹 Admin: Get all memberships
@memberships_bp.route("/admin/memberships", methods=["GET"])
@authenticate
@admin_required
def get_all_memberships(user):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.*, u.name, u.email, u.role
            FROM memberships m
            JOIN users u ON m.member_id = u.id
            ORDER BY m.start_date DESC
        """)
        memberships = cursor.fetchall()
        cursor.close()
        return jsonify(memberships)

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
