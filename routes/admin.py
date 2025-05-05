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
            SELECT id, name, email, role, membership_expiry, auto_payment
            FROM users
            WHERE role IN ('member', 'non_member')
            ORDER BY name
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
    if not data or 'role' not in data:
        return jsonify({"error": "Role is required"}), 400
        
    new_role = data['role']
    if new_role not in ['admin', 'trainer', 'member', 'non_member']:
        return jsonify({"error": f"Invalid role: {new_role}. Must be one of: admin, trainer, member, non_member"}), 400
        
    with get_db() as conn:
        cursor = conn.cursor()
        # First check if user exists and get current role in one query
        cursor.execute("""
            SELECT role FROM users WHERE id = %s
        """, (user_id,))
        
        existing_user = cursor.fetchone()
        if not existing_user:
            cursor.close()
            return jsonify({"error": f"User with ID {user_id} not found"}), 404
            
        current_role = existing_user[0]
            
        # Update the role directly without additional verification
        cursor.execute("""
            UPDATE users SET role = %s WHERE id = %s
        """, (new_role, user_id))
        
        conn.commit()
        cursor.close()
        return jsonify({"message": f"Role updated successfully to {new_role}", "old_role": current_role, "new_role": new_role})

# 🔹 Delete user
@admin_bp.route("/admin/users/<int:user_id>", methods=["DELETE"])
@authenticate
@admin_required
def delete_user(user, user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE id = %s AND role IN ('member', 'non_member')", (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            cursor.close()
            return jsonify({"error": f"User with ID {user_id} not found or cannot be deleted"}), 404
            
        # Delete the user
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        
        return jsonify({"message": "User deleted successfully"})

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
        
@admin_bp.route("/admin/equipment-reports", methods=["GET"])
@authenticate
@admin_required
def get_equipment_reports(user):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT er.id, er.equipment_name, er.issue_description, er.reported_at, u.name AS reporter_name
            FROM equipment_reports er
            JOIN users u ON er.user_id = u.id
            ORDER BY er.reported_at DESC
        """)
        reports = cursor.fetchall()
        return jsonify(reports)

# Get membership statistics
@admin_bp.route("/admin/membership-stats", methods=["GET"])
@authenticate
@admin_required
def get_membership_stats(user):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        
        # Get current month's stats
        current_month = datetime.now().strftime('%Y-%m')
        
        # New members this month
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM users
            WHERE role = 'member'
            AND DATE_FORMAT(created_at, '%Y-%m') = %s
        """, (current_month,))
        new_members = cursor.fetchone()['count']
        
        # Total active members (members with valid membership_expiry)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM users
            WHERE role = 'member'
            AND membership_expiry > NOW()
        """)
        total_members = cursor.fetchone()['count']
        
        # Financial stats from payments table
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN status = 'Completed' THEN amount ELSE 0 END), 0) as membership_revenue,
                5000 as class_revenue,  -- Hardcoded value
                2000 as merchandise_sales  -- Hardcoded value
            FROM payments
            WHERE DATE_FORMAT(transaction_date, '%Y-%m') = %s
        """, (current_month,))
        financial = cursor.fetchone()
        
        stats = {
            'new_members': new_members,
            'renewals': 0,  # Since we don't track renewals separately
            'total_members': total_members,
            'membership_revenue': financial['membership_revenue'],
            'class_revenue': financial['class_revenue'],
            'merchandise_sales': financial['merchandise_sales'],
            'total_revenue': (financial['membership_revenue'] + 
                            financial['class_revenue'] + 
                            financial['merchandise_sales'])
        }
        
        cursor.close()
        return jsonify(stats)

# Get all employees
@admin_bp.route("/admin/employees", methods=["GET"])
@authenticate
@admin_required
def get_employees(user):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, name, email, role,
                   TIMESTAMPDIFF(MONTH, created_at, NOW()) as tenure_months
            FROM users
            WHERE role NOT IN ('member', 'non_member')
            ORDER BY name
        """)
        employees = cursor.fetchall()
        
        # Format tenure
        for emp in employees:
            months = emp['tenure_months']
            if months < 12:
                emp['tenure'] = f"{months} months"
            else:
                years = months // 12
                remaining_months = months % 12
                emp['tenure'] = f"{years} years, {remaining_months} months"
            del emp['tenure_months']
        
        cursor.close()
        return jsonify(employees)

# Update employee role
@admin_bp.route("/admin/employees/<int:employee_id>/role", methods=["PUT"])
@authenticate
@admin_required
def update_employee_role(user, employee_id):
    data = request.json
    if not data or 'role' not in data:
        return jsonify({"error": "Role is required"}), 400
        
    new_role = data['role']
    if new_role not in ['admin', 'trainer', 'member', 'non_member']:
        return jsonify({"error": f"Invalid role: {new_role}. Must be one of: admin, trainer, member, non_member"}), 400
        
    with get_db() as conn:
        cursor = conn.cursor()
        
        # First check if employee exists and get current role in one query
        cursor.execute("""
            SELECT role FROM users WHERE id = %s
        """, (employee_id,))
        
        existing_user = cursor.fetchone()
        if not existing_user:
            cursor.close()
            return jsonify({"error": f"Employee with ID {employee_id} not found"}), 404
            
        current_role = existing_user[0]
            
        # Update the role directly without additional verification
        cursor.execute("""
            UPDATE users SET role = %s WHERE id = %s
        """, (new_role, employee_id))
        
        conn.commit()
        cursor.close()
        return jsonify({"message": f"Role updated successfully to {new_role}", "old_role": current_role, "new_role": new_role})

# Delete employee
@admin_bp.route("/admin/employees/<int:employee_id>", methods=["DELETE"])
@authenticate
@admin_required
def delete_employee(user, employee_id):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if employee exists
        cursor.execute("SELECT id FROM users WHERE id = %s AND role NOT IN ('member', 'non_member')", (employee_id,))
        employee = cursor.fetchone()
        
        if not employee:
            cursor.close()
            return jsonify({"error": f"Employee with ID {employee_id} not found or cannot be deleted"}), 404
        
        # Delete the employee
        cursor.execute("DELETE FROM users WHERE id = %s", (employee_id,))
        conn.commit()
        cursor.close()
        return jsonify({"message": "Employee deleted successfully"})

