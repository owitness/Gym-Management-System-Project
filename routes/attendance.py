from flask import Blueprint, jsonify, request
from middleware import authenticate
from db import get_db
from datetime import datetime, timedelta

attendance_bp = Blueprint("attendance", __name__)

@attendance_bp.route("/attendance/current", methods=["GET"])
@authenticate
def get_current_attendance(user):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, check_in_time, check_out_time 
            FROM attendance 
            WHERE member_id = %s 
            ORDER BY check_in_time DESC 
            LIMIT 1
        """, (user["id"],))
        record = cursor.fetchone()

        if record and not record["check_out_time"]:
            return jsonify({
                "checked_in": True,
                "check_in_time": record["check_in_time"]
            })

        return jsonify({
            "checked_in": False,
            "last_visit": record["check_in_time"] if record else None
        })

@attendance_bp.route("/attendance/history", methods=["GET"])
@authenticate
def get_attendance_history(user):
    days = request.args.get("days", default=7, type=int)
    cutoff = datetime.now() - timedelta(days=days)

    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT check_in_time, check_out_time 
            FROM attendance 
            WHERE member_id = %s AND check_in_time >= %s
            ORDER BY check_in_time DESC
        """, (user["id"], cutoff))
        return jsonify(cursor.fetchall())

@attendance_bp.route("/attendance/check-in", methods=["POST"])
@authenticate
def check_in(user):
    with get_db() as conn:
        cursor = conn.cursor()
        # Check if user is already checked in
        cursor.execute("""
            SELECT id FROM attendance 
            WHERE member_id = %s AND check_out_time IS NULL
        """, (user["id"],))
        if cursor.fetchone():
            return jsonify({"error": "Already checked in"}), 400

        # Insert new check-in
        cursor.execute("""
            INSERT INTO attendance (member_id, check_in_time)
            VALUES (%s, NOW())
        """, (user["id"],))
        conn.commit()
        return jsonify({"message": "Check-in successful"})
    
@attendance_bp.route("/attendance/check-out", methods=["POST"])
@authenticate
def check_out(user):
    with get_db() as conn:
        cursor = conn.cursor()

        # Find active check-in (no check-out time yet)
        cursor.execute("""
            SELECT id FROM attendance 
            WHERE member_id = %s AND check_out_time IS NULL 
            ORDER BY check_in_time DESC 
            LIMIT 1
        """, (user["id"],))
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": "No active check-in found"}), 400

        # Update the record with check-out time
        attendance_id = row[0]
        cursor.execute("""
            UPDATE attendance 
            SET check_out_time = NOW() 
            WHERE id = %s
        """, (attendance_id,))
        
        conn.commit()
        return jsonify({"message": "Check-out successful"})

