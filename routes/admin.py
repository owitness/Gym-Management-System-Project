from flask import Blueprint, jsonify, request, current_app
from db import get_db
from middleware import authenticate, admin_required
from datetime import datetime, timedelta

admin_bp = Blueprint("admin", __name__)

# 🔹 Get system overview
@admin_bp.route("/admin/overview", methods=["GET"])
@authenticate
@admin_required
def get_system_overview(user):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        
        # Get total active members
        cursor.execute("""
            SELECT COUNT(*) as total_members
            FROM users
            WHERE role = 'member'
        """)
        member_count = cursor.fetchone()["total_members"]
        
        # Get total trainers
        cursor.execute("""
            SELECT COUNT(*) as total_trainers
            FROM users
            WHERE role = 'trainer'
        """)
        trainer_count = cursor.fetchone()["total_trainers"]
        
        # Get today's attendance
        cursor.execute("""
            SELECT COUNT(DISTINCT member_id) as today_attendance
            FROM attendance
            WHERE DATE(check_in_time) = CURDATE()
        """)
        today_attendance = cursor.fetchone()["today_attendance"]
        
        # Get upcoming classes (next 24 hours)
        cursor.execute("""
            SELECT COUNT(*) as upcoming_classes
            FROM classes
            WHERE schedule_time BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 24 HOUR)
        """)
        upcoming_classes = cursor.fetchone()["upcoming_classes"]
        
        # Get recent payments (last 30 days)
        cursor.execute("""
            SELECT COUNT(*) as payment_count, SUM(amount) as total_amount
            FROM payments
            WHERE transaction_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """)
        payment_stats = cursor.fetchone()
        
        cursor.close()
        return jsonify({
            "active_members": member_count,
            "trainers": trainer_count,
            "today_attendance": today_attendance,
            "upcoming_classes": upcoming_classes,
            "recent_payments": {
                "count": payment_stats["payment_count"],
                "total": float(payment_stats["total_amount"] or 0)
            }
        })

# 🔹 Manage classes
@admin_bp.route("/admin/classes", methods=["GET", "POST"])
@authenticate
@admin_required
def manage_classes(user):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        
        if request.method == "GET":
            # Get all classes with trainer info and booking counts
            cursor.execute("""
                SELECT c.*, 
                       t.name as trainer_name,
                       COUNT(cb.id) as current_bookings
                FROM classes c
                LEFT JOIN users t ON c.trainer_id = t.id
                LEFT JOIN class_bookings cb ON c.id = cb.class_id
                GROUP BY c.id
                ORDER BY c.schedule_time ASC
            """)
            classes = cursor.fetchall()
            cursor.close()
            return jsonify(classes)
            
        else:  # POST
            data = request.json
            required_fields = ["class_name", "trainer_id", "schedule_time", "capacity"]
            
            if not all(field in data for field in required_fields):
                cursor.close()
                return jsonify({"error": "Missing required fields"}), 400
                
            cursor.execute("""
                INSERT INTO classes (class_name, trainer_id, schedule_time, capacity)
                VALUES (%s, %s, %s, %s)
            """, (data["class_name"], data["trainer_id"], 
                  data["schedule_time"], data["capacity"]))
            
            conn.commit()
            cursor.close()
            return jsonify({"message": "Class created successfully"})

# 🔹 Get class roster
@admin_bp.route("/admin/classes/<int:class_id>/roster", methods=["GET"])
@authenticate
@admin_required
def get_class_roster(user, class_id):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.name, u.email, cb.booking_date
            FROM class_bookings cb
            JOIN users u ON cb.member_id = u.id
            WHERE cb.class_id = %s
            ORDER BY cb.booking_date ASC
        """, (class_id,))
        
        roster = cursor.fetchall()
        cursor.close()
        return jsonify(roster)

# 🔹 Manage users
@admin_bp.route("/admin/users", methods=["GET"])
@authenticate
@admin_required
def get_users(user):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id, u.name, u.email, u.role, u.created_at,
                   m.status as membership_status,
                   m.expiry_date as membership_expiry
            FROM users u
            LEFT JOIN memberships m ON u.id = m.member_id AND m.status = 'active'
            ORDER BY u.created_at DESC
        """)
        
        users = cursor.fetchall()
        cursor.close()
        return jsonify(users)

# 🔹 Update user role
@admin_bp.route("/admin/users/<int:user_id>/role", methods=["PUT"])
@authenticate
@admin_required
def update_user_role(user, user_id):
    data = request.json
    new_role = data.get("role")
    
    if new_role not in ["admin", "trainer", "member", "non_member"]:
        return jsonify({"error": "Invalid role"}), 400
        
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET role = %s 
            WHERE id = %s
        """, (new_role, user_id))
        
        conn.commit()
        cursor.close()
        return jsonify({"message": f"User role updated to {new_role}"})

# 🔹 Get attendance report
@admin_bp.route("/admin/attendance", methods=["GET"])
@authenticate
@admin_required
def get_attendance_report(user):
    start_date = request.args.get("start_date", datetime.now().date().isoformat())
    end_date = request.args.get("end_date", datetime.now().date().isoformat())
    
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT DATE(a.check_in_time) as date,
                   COUNT(DISTINCT a.member_id) as unique_visits,
                   COUNT(*) as total_visits,
                   AVG(TIMESTAMPDIFF(MINUTE, a.check_in_time, a.check_out_time)) as avg_duration
            FROM attendance a
            WHERE DATE(a.check_in_time) BETWEEN %s AND %s
            GROUP BY DATE(a.check_in_time)
            ORDER BY date DESC
        """, (start_date, end_date))
        
        attendance_data = cursor.fetchall()
        cursor.close()
        return jsonify(attendance_data)

# 🔹 Get payment report
@admin_bp.route("/admin/payments", methods=["GET"])
@authenticate
@admin_required
def get_payment_report(user):
    start_date = request.args.get("start_date", 
        (datetime.now() - timedelta(days=30)).date().isoformat())
    end_date = request.args.get("end_date", datetime.now().date().isoformat())
    
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        
        # Daily revenue
        cursor.execute("""
            SELECT DATE(transaction_date) as date,
                   COUNT(*) as payment_count,
                   SUM(amount) as total_amount
            FROM payments
            WHERE DATE(transaction_date) BETWEEN %s AND %s
            GROUP BY DATE(transaction_date)
            ORDER BY date DESC
        """, (start_date, end_date))
        
        daily_revenue = cursor.fetchall()
        
        # Membership type breakdown
        cursor.execute("""
            SELECT membership_duration,
                   COUNT(*) as count,
                   SUM(amount) as total_amount
            FROM payments
            WHERE DATE(transaction_date) BETWEEN %s AND %s
            GROUP BY membership_duration
        """, (start_date, end_date))
        
        membership_stats = cursor.fetchall()
        
        cursor.close()
        return jsonify({
            "daily_revenue": daily_revenue,
            "membership_stats": membership_stats
        }) 