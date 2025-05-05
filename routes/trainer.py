from flask import Blueprint, jsonify, request, current_app
from db import get_db
from middleware import authenticate
from datetime import datetime, timedelta
from functools import wraps

trainer_bp = Blueprint("trainer", __name__)

def trainer_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not kwargs.get('user') or kwargs['user'].get('role') != 'trainer':
            return jsonify({"error": "Trainer access required"}), 403
        return f(*args, **kwargs)
    return wrapper

# 🔹 Get trainer's classes
@trainer_bp.route("/trainer/classes", methods=["GET"])
@authenticate
@trainer_required
def get_trainer_classes(user):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.*, 
                   COUNT(cb.id) as current_bookings,
                   c.capacity - COUNT(cb.id) as available_spots
            FROM classes c
            LEFT JOIN class_bookings cb ON c.id = cb.class_id
            WHERE c.trainer_id = %s AND c.schedule_time >= NOW()
            GROUP BY c.id
            ORDER BY c.schedule_time ASC
        """, (user["id"],))
        
        classes = cursor.fetchall()
        cursor.close()
        return jsonify(classes)

# 🔹 Create a class
@trainer_bp.route("/classes", methods=["POST"])
@authenticate
@trainer_required
def create_class(user):
    data = request.json
    required_fields = ["class_name", "schedule_time", "capacity"]
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
        
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check for time slot conflicts
        cursor.execute("""
            SELECT id FROM classes
            WHERE trainer_id = %s 
            AND ABS(TIMESTAMPDIFF(MINUTE, schedule_time, %s)) < 60
        """, (user["id"], data["schedule_time"]))
        
        if cursor.fetchone():
            cursor.close()
            return jsonify({
                "error": "You already have a class scheduled within an hour of this time"
            }), 400
        
        cursor.execute("""
            INSERT INTO classes (class_name, trainer_id, schedule_time, capacity)
            VALUES (%s, %s, %s, %s)
        """, (data["class_name"], user["id"], 
              data["schedule_time"], data["capacity"]))
        
        conn.commit()
        cursor.close()
        return jsonify({"message": "Class created successfully"})

# 🔹 Update a class
@trainer_bp.route("/classes/<int:class_id>", methods=["PUT"])
@authenticate
@trainer_required
def update_class(user, class_id):
    data = request.json
    allowed_fields = ["class_name", "schedule_time", "capacity"]
    
    # Filter out non-allowed fields
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    if not update_data:
        return jsonify({"error": "No valid fields to update"}), 400
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify trainer owns the class
        cursor.execute("""
            SELECT id FROM classes
            WHERE id = %s AND trainer_id = %s
        """, (class_id, user["id"]))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Class not found or not authorized"}), 404
        
        # Check if class has started
        cursor.execute("""
            SELECT schedule_time FROM classes
            WHERE id = %s AND schedule_time <= NOW()
        """, (class_id,))
        
        if cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Cannot modify a class that has already started"}), 400
        
        # Build dynamic update query
        fields = ", ".join([f"{k} = %s" for k in update_data.keys()])
        values = list(update_data.values())
        values.append(class_id)
        values.append(user["id"])
        
        cursor.execute(f"""
            UPDATE classes 
            SET {fields}
            WHERE id = %s AND trainer_id = %s
        """, values)
        
        conn.commit()
        cursor.close()
        return jsonify({"message": "Class updated successfully"})

# 🔹 Delete a class
@trainer_bp.route("/classes/<int:class_id>", methods=["DELETE"])
@authenticate
@trainer_required
def delete_class(user, class_id):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify trainer owns the class and it hasn't started
        cursor.execute("""
            SELECT id FROM classes
            WHERE id = %s 
            AND trainer_id = %s
            AND schedule_time > NOW()
        """, (class_id, user["id"]))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({
                "error": "Class not found, not authorized, or already started"
            }), 404
        
        # Delete class bookings first
        cursor.execute("DELETE FROM class_bookings WHERE class_id = %s", (class_id,))
        
        # Delete the class
        cursor.execute("DELETE FROM classes WHERE id = %s", (class_id,))
        
        conn.commit()
        cursor.close()
        return jsonify({"message": "Class deleted successfully"})

# 🔹 Get class roster
@trainer_bp.route("/classes/<int:class_id>/roster", methods=["GET"])
@authenticate
@trainer_required
def get_class_roster(user, class_id):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        
        # Verify trainer owns the class
        cursor.execute("""
            SELECT id FROM classes
            WHERE id = %s AND trainer_id = %s
        """, (class_id, user["id"]))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Class not found or not authorized"}), 404
        
        cursor.execute("""
            SELECT u.name, u.email, cb.booking_date,
                   COUNT(a.id) as past_attendance
            FROM class_bookings cb
            JOIN users u ON cb.member_id = u.id
            LEFT JOIN attendance a ON u.id = a.member_id
            WHERE cb.class_id = %s
            GROUP BY u.id
            ORDER BY u.name ASC
        """, (class_id,))
        
        roster = cursor.fetchall()
        cursor.close()
        return jsonify(roster)

# 🔹 Get trainer's schedule
@trainer_bp.route("/schedule", methods=["GET"])
@authenticate
@trainer_required
def get_schedule(user):
    start_date = request.args.get("start_date", datetime.now().date().isoformat())
    end_date = request.args.get("end_date", 
        (datetime.now() + timedelta(days=30)).date().isoformat())
    
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT c.*, 
                   COUNT(cb.id) as current_bookings,
                   c.capacity - COUNT(cb.id) as available_spots
            FROM classes c
            LEFT JOIN class_bookings cb ON c.id = cb.class_id
            WHERE c.trainer_id = %s 
            AND DATE(c.schedule_time) BETWEEN %s AND %s
            GROUP BY c.id
            ORDER BY c.schedule_time ASC
        """, (user["id"], start_date, end_date))
        
        schedule = cursor.fetchall()
        
        # Group by date for easier frontend rendering
        schedule_by_date = {}
        for class_info in schedule:
            date = class_info["schedule_time"].date().isoformat()
            if date not in schedule_by_date:
                schedule_by_date[date] = []
            schedule_by_date[date].append(class_info)
        
        cursor.close()
        return jsonify(schedule_by_date)

# 🔹 Get single class by ID
@trainer_bp.route("/trainer/classes/<int:class_id>", methods=["GET"])
@authenticate
@trainer_required
def get_class_by_id(user, class_id):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        
        # Verify trainer owns the class
        cursor.execute("""
            SELECT c.*, 
                   COUNT(cb.id) as current_bookings,
                   c.capacity - COUNT(cb.id) as available_spots
            FROM classes c
            LEFT JOIN class_bookings cb ON c.id = cb.class_id
            WHERE c.id = %s AND c.trainer_id = %s
            GROUP BY c.id
        """, (class_id, user["id"]))
        
        class_info = cursor.fetchone()
        
        if not class_info:
            cursor.close()
            return jsonify({"error": "Class not found or not authorized"}), 404
            
        cursor.close()
        return jsonify(class_info) 