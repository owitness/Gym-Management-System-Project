from flask import Blueprint, request, jsonify
from db import get_db_connection
from middleware import authenticate, admin_required

users_bp = Blueprint("users", __name__)

@users_bp.route("/users/me", methods=["GET"])
@authenticate
def get_user_info(user):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, role FROM users WHERE id=%s", (user["id"],))
    user_info = cursor.fetchone()
    cursor.close()
    conn.close()

    return jsonify(user_info)

# 🔹 Admin Can Change User Roles
@users_bp.route("/users/<int:user_id>/role", methods=["PUT"])
@authenticate
@admin_required
def update_user_role(user, user_id):
    data = request.json
    new_role = data["role"]

    if new_role not in ["admin", "member", "non_member"]:
        return jsonify({"error": "Invalid role"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": f"User {user_id} role updated to {new_role}."})
