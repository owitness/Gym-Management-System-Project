from flask import Blueprint, jsonify, request, current_app
from db import get_db
from middleware import authenticate
from datetime import datetime

class_schedule_bp = Blueprint("class_schedule", __name__)

# ✅ Get all upcoming classes
@class_schedule_bp.route("/classes", methods=["GET"])
@authenticate
def get_classes(user):
    print("Connected to DB and running class fetch...")

    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.id, 
                   c.class_name, 
                   c.trainer_id, 
                   u.name AS trainer_name, 
                   c.schedule_time, 
                   c.capacity,
                   COUNT(cb.id) AS current_bookings
            FROM classes c
            LEFT JOIN users u ON c.trainer_id = u.id
            LEFT JOIN class_bookings cb ON c.id = cb.class_id
            WHERE c.schedule_time >= NOW()
            GROUP BY c.id
            ORDER BY c.schedule_time
        """)
        return jsonify(cursor.fetchall())


# Book a class
# Book a class
@class_schedule_bp.route("/classes/<int:class_id>/book", methods=["POST"])
@authenticate
def book_class(user, class_id):
    print("IM IN HERE")
    try:
        print(f"Booking request received for class {class_id} by user {user['id']}")

        with get_db() as conn:
            cursor = conn.cursor()

            # Check for existing booking
            cursor.execute("""
                SELECT COUNT(*) FROM class_bookings 
                WHERE member_id = %s AND class_id = %s
            """, (user["id"], class_id))
            already_booked = cursor.fetchone()[0]
            print(f"Existing bookings found: {already_booked}")
            if already_booked > 0:
                print("User already booked this class")
                return jsonify({"error": "You already booked this class"}), 400

            # Check if class exists and has space
            cursor.execute("SELECT capacity FROM classes WHERE id = %s", (class_id,))
            result = cursor.fetchone()
            print(f"Class lookup result: {result}")
            if not result:
                print("Class not found")
                return jsonify({"error": "Class not found"}), 404

            capacity = result[0]
            cursor.execute("SELECT COUNT(*) FROM class_bookings WHERE class_id = %s", (class_id,))
            booked = cursor.fetchone()[0]
            print(f"Booked seats: {booked} / {capacity}")
            if booked >= capacity:
                print("Class is full")
                return jsonify({"error": "Class is full"}), 400

            # Insert booking
            cursor.execute("""
                INSERT INTO class_bookings (member_id, class_id, booking_date) 
                VALUES (%s, %s, NOW())
            """, (user["id"], class_id))

            conn.commit()
            print("Booking successful")
            return jsonify({"message": "Class booked successfully!"}), 200

    except Exception as e:
        print(f"Unexpected error during booking: {e}")
        return jsonify({"error": "Booking failed due to an unexpected error."}), 500




#  Cancel class booking
@class_schedule_bp.route("/classes/<int:class_id>/cancel", methods=["DELETE"])
@authenticate
def cancel_class_booking(user, class_id):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)

        # Check if class hasn't started yet
        cursor.execute("""
            SELECT c.schedule_time
            FROM class_bookings cb
            JOIN classes c ON cb.class_id = c.id
            WHERE cb.member_id = %s AND cb.class_id = %s
        """, (user["id"], class_id))
        
        class_info = cursor.fetchone()
        if not class_info:
            return jsonify({"error": "Booking not found"}), 404
            
        if class_info["schedule_time"] <= datetime.now():
            return jsonify({"error": "Cannot cancel a class that has already started"}), 400
        
        # Cancel the booking
        cursor.execute("""
            DELETE FROM class_bookings 
            WHERE member_id = %s AND class_id = %s
        """, (user["id"], class_id))
        
        conn.commit()
        return jsonify({"message": "Class booking cancelled successfully"})
