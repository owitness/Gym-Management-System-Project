from flask import Blueprint, jsonify, request, current_app
from db import get_db
from middleware import authenticate
from datetime import datetime

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
@dashboard_bp.route("/dashboard/profile", methods=["PUT"])
@authenticate
def update_profile(user):
    data = request.json
    allowed_fields = ["name", "address", "city", "state", "zipcode", "auto_payment"]
    
    # Filter out non-allowed fields
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    if not update_data:
        return jsonify({"error": "No valid fields to update"}), 400
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Build dynamic update query
        fields = ", ".join([f"{k} = %s" for k in update_data.keys()])
        values = list(update_data.values())
        values.append(user["id"])
        
        cursor.execute(f"""
            UPDATE users 
            SET {fields}
            WHERE id = %s
        """, values)
        
        conn.commit()
        cursor.close()
        return jsonify({"message": "Profile updated successfully"})

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
                user["id"],  # Using id from the token
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

# 🔹 Book a class
@dashboard_bp.route("/dashboard/book-class/<int:class_id>", methods=["POST"])
@authenticate
def book_class(user, class_id):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if class exists and has capacity
        cursor.execute("""
            SELECT c.*, 
                   (SELECT COUNT(*) FROM class_bookings WHERE class_id = c.id) as current_bookings
            FROM classes c
            WHERE c.id = %s AND c.schedule_time > NOW()
        """, (class_id,))
        
        class_info = cursor.fetchone()
        if not class_info:
            cursor.close()
            return jsonify({"error": "Class not found or already started"}), 404
            
        if class_info["current_bookings"] >= class_info["capacity"]:
            cursor.close()
            return jsonify({"error": "Class is full"}), 400
        
        # Check if user already booked this class
        cursor.execute("""
            SELECT id FROM class_bookings 
            WHERE member_id = %s AND class_id = %s
        """, (user["id"], class_id))
        
        if cursor.fetchone():
            cursor.close()
            return jsonify({"error": "You have already booked this class"}), 400
        
        # Book the class
        cursor.execute("""
            INSERT INTO class_bookings (member_id, class_id)
            VALUES (%s, %s)
        """, (user["id"], class_id))
        
        conn.commit()
        cursor.close()
        return jsonify({"message": "Class booked successfully"})

# 🔹 Cancel class booking
@dashboard_bp.route("/dashboard/book-class/<int:class_id>", methods=["DELETE"])
@authenticate
def cancel_class_booking(user, class_id):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if class hasn't started yet
        cursor.execute("""
            SELECT c.schedule_time
            FROM class_bookings cb
            JOIN classes c ON cb.class_id = c.id
            WHERE cb.member_id = %s AND cb.class_id = %s
        """, (user["id"], class_id))
        
        class_info = cursor.fetchone()
        if not class_info:
            cursor.close()
            return jsonify({"error": "Booking not found"}), 404
            
        if class_info["schedule_time"] <= datetime.now():
            cursor.close()
            return jsonify({"error": "Cannot cancel a class that has already started"}), 400
        
        # Cancel the booking
        cursor.execute("""
            DELETE FROM class_bookings 
            WHERE member_id = %s AND class_id = %s
        """, (user["id"], class_id))
        
        conn.commit()
        cursor.close()
        return jsonify({"message": "Class booking cancelled successfully"}) 