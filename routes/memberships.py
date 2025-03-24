from flask import Blueprint, jsonify
from db import get_db_connection

memberships_bp = Blueprint("memberships", __name__)

# 🔹 Get all memberships (Stored in DB)
@memberships_bp.route("/memberships", methods=["GET"])
def get_memberships():
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM memberships")
    memberships = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return jsonify(memberships)
