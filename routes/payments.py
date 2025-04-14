from flask import Blueprint, request, jsonify
from db import get_db, get_db_connection
from middleware import authenticate
from datetime import datetime
import logging

payments_bp = Blueprint("payments", __name__)
logger = logging.getLogger(__name__)

# 🔹 Add Payment Method
@payments_bp.route("/payment-methods", methods=["POST"])
@authenticate
def add_payment_method(user):
    try:
        data = request.json
        required_fields = ['card_number', 'exp', 'cvv', 'card_holder_name']
        
        # Validate required fields
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        # Format expiration date
        exp_date = datetime.strptime(data['exp'], '%Y-%m-%d').date()

        with get_db() as conn:
            cursor = conn.cursor()

            # Insert payment method
            cursor.execute("""
                INSERT INTO payment_methods (
                    user_id, card_number, exp, cvv, card_holder_name, saved
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user["id"], data['card_number'], exp_date, 
                data['cvv'], data['card_holder_name'], True
            ))

            payment_method_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Payment method added for user {user['id']}")
            
            return jsonify({
                "message": "Payment method added successfully",
                "id": payment_method_id
            }), 201

    except Exception as e:
        logger.error(f"Error adding payment method: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 🔹 Process Membership Payment
@payments_bp.route("/payments", methods=["POST"])
@authenticate
def process_payment(user):
    try:
        data = request.json
        amount = data["amount"]

        if amount < 0:
            return jsonify({"error": "Invalid payment amount"}), 400

        with get_db() as conn:
            cursor = conn.cursor()

            # Store payment details
            cursor.execute("""
                INSERT INTO payments (user_id, amount, status, transaction_date) 
                VALUES (%s, %s, 'Completed', NOW())
            """, (user["id"], amount))
            
            # Upgrade user to 'member' after successful payment
            cursor.execute("""
                UPDATE users 
                SET role = 'member', auto_payment = 1 
                WHERE id = %s
            """, (user["id"],))

            conn.commit()
            
            logger.info(f"Payment processed for user {user['id']}: ${amount}")
            
            return jsonify({"message": "Payment successful! Your account has been upgraded to 'member'."})
            
    except Exception as e:
        logger.error(f"Error processing payment: {str(e)}")
        return jsonify({"error": "Payment processing failed"}), 500
