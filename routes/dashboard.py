from flask import Blueprint, jsonify, request, current_app
from db import get_db
from middleware import authenticate

dashboard_bp = Blueprint("dashboard", __name__)

# 🔹 Get user's dashboard data
@dashboard_bp.route("/dashboard/summary", methods=["GET"])
@authenticate
def get_dashboard_summary(user):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        
        # Get membership info
        cursor.execute("""
            SELECT m.*, u.auto_payment
            FROM memberships m
            JOIN users u ON m.member_id = u.id
            WHERE m.member_id = %s AND m.status = 'active'
        """, (user["id"],))
        membership = cursor.fetchone()
        
        # Get upcoming classes
        cursor.execute("""
            SELECT c.*, t.name as trainer_name
            FROM class_bookings cb
            JOIN classes c ON cb.class_id = c.id
            JOIN users t ON c.trainer_id = t.id
            WHERE cb.member_id = %s AND c.schedule_time > NOW()
            ORDER BY c.schedule_time ASC
            LIMIT 5
        """, (user["id"],))
        upcoming_classes = cursor.fetchall()
        
        # Get recent attendance
        cursor.execute("""
            SELECT check_in_time, check_out_time
            FROM attendance
            WHERE member_id = %s
            ORDER BY check_in_time DESC
            LIMIT 5
        """, (user["id"],))
        recent_attendance = cursor.fetchall()
        
        # Get payment methods
        cursor.execute("""
            SELECT id, card_number, exp, card_holder_name, saved
            FROM payment_methods
            WHERE user_id = %s AND saved = TRUE
        """, (user["id"],))
        payment_methods = cursor.fetchall()
        
        # Mask card numbers
        for pm in payment_methods:
            pm["card_number"] = "*" * 12 + pm["card_number"][-4:]
        
        cursor.close()
        return jsonify({
            "membership": membership,
            "upcoming_classes": upcoming_classes,
            "recent_attendance": recent_attendance,
            "payment_methods": payment_methods
        })


# 🔹 Update user profile
@dashboard_bp.route("/dashboard/profile", methods=["GET"])
@authenticate
def get_profile(user):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        
        # Query to fetch the user's profile information
        cursor.execute("""
            SELECT name, email, address, city, state, zipcode
            FROM users
            WHERE id = %s
        """, (user["id"],))
        
        # Fetch the result
        user_data = cursor.fetchone()
        
        if user_data:
            # Return the profile data as JSON
            profile = {
                "name": user_data["name"],
                "email": user["email"],  # Assuming email is stored in the user object
                "address": user_data["address"] or 'No address provided',
                "city": user_data["city"] or 'No city provided',
                "state": user_data["state"] or 'No state provided',
                "zipcode": user_data["zipcode"] or 'No zipcode provided',
            }
            return jsonify(profile)
        else:
            return jsonify({"error": "Profile not found"}), 404


# 🔹 Add/Update payment method
@dashboard_bp.route("/dashboard/payment-methods", methods=["POST"])
@authenticate
def add_payment_method(user):
    data = request.json
    required_fields = ["card_number", "exp", "cvv", "card_holder_name"]
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            # Insert payment method
            cursor.execute("""
                INSERT INTO payment_methods 
                    (user_id, card_number, exp, cvv, card_holder_name, saved)
                VALUES (%s, %s, %s, %s, %s, TRUE)
            """, (
                user["id"],
                data["card_number"],
                data["exp"],
                data["cvv"],
                data["card_holder_name"]
            ))
            
            payment_method_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            
            return jsonify({
                "message": "Payment method saved successfully",
                "id": payment_method_id
            })
            
        except Exception as e:
            current_app.logger.error(f"Error saving payment method: {str(e)}")
            return jsonify({"error": "Failed to save payment method"}), 500
        
@dashboard_bp.route("/my-membership", methods=["GET"])
@authenticate
def get_my_membership(user):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT m.*, u.auto_payment
            FROM memberships m
            JOIN users u ON m.member_id = u.id
            WHERE m.member_id = %s AND m.status = 'active'
        """, (user["id"],))

        membership = cursor.fetchone()
        cursor.close()

        if not membership:
            return jsonify({"error": "No active membership found"}), 404

        return jsonify(membership)
