from flask import Blueprint, request, jsonify
from db import get_db_connection
from middleware import authenticate

payments_bp = Blueprint("payments", __name__)

# 🔹 Process Membership Payment
@payments_bp.route("/payments", methods=["POST"])
@authenticate
def process_payment(user):
    data = request.json
    amount = data["amount"]

    if amount < 0:
        return jsonify({"error": "Invalid payment amount"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Store payment details
    cursor.execute("INSERT INTO payments (member_id, amount, status, transaction_date) VALUES (%s, %s, 'completed', NOW())",
                   (user["id"], amount))
    
    # ✅ Upgrade user to 'member' after successful payment
    cursor.execute("UPDATE users SET role = 'member' WHERE id = %s", (user["id"],))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Payment successful! Your account has been upgraded to 'member'."})
