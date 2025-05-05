from flask import Blueprint, request, jsonify
from db import get_db, get_db_connection
from middleware import authenticate
from datetime import datetime, timedelta
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

        # Format expiration date from MM/YY to YYYY-MM-DD
        try:
            exp_parts = data['exp'].split('/')
            if len(exp_parts) != 2:
                return jsonify({"error": "Invalid expiration date format. Use MM/YY"}), 400
                
            month = int(exp_parts[0])
            year = int(exp_parts[1])
            
            # Convert 2-digit year to 4-digit year (assuming 20xx)
            if year < 100:
                year += 2000
                
            # Set day to last day of the month
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year
                
            exp_date = (datetime(next_year, next_month, 1) - timedelta(days=1)).date()
            
        except ValueError:
            return jsonify({"error": "Invalid expiration date format. Use MM/YY"}), 400

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

# 🔹 Get Payment Methods
@payments_bp.route("/payment-methods", methods=["GET"])
@authenticate
def get_payment_methods(user):
    try:
        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id, card_number, exp, card_holder_name
                FROM payment_methods
                WHERE user_id = %s AND saved = TRUE
                ORDER BY id DESC
            """, (user["id"],))
            
            payment_methods = cursor.fetchall()
            cursor.close()
            
            return jsonify(payment_methods)
            
    except Exception as e:
        logger.error(f"Error getting payment methods: {str(e)}")
        return jsonify({"error": "Failed to get payment methods"}), 500

# 🔹 Delete Payment Method
@payments_bp.route("/payment-methods/<int:method_id>", methods=["DELETE"])
@authenticate
def delete_payment_method(user, method_id):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Verify the payment method belongs to the user
            cursor.execute("""
                SELECT id FROM payment_methods
                WHERE id = %s AND user_id = %s
            """, (method_id, user["id"]))
            
            if not cursor.fetchone():
                return jsonify({"error": "Payment method not found"}), 404
            
            # Delete the payment method
            cursor.execute("""
                DELETE FROM payment_methods
                WHERE id = %s AND user_id = %s
            """, (method_id, user["id"]))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Payment method {method_id} deleted for user {user['id']}")
            
            return jsonify({"message": "Payment method deleted successfully"})
            
    except Exception as e:
        logger.error(f"Error deleting payment method: {str(e)}")
        return jsonify({"error": "Failed to delete payment method"}), 500

# 🔹 Get Payment History
@payments_bp.route("/payments/history", methods=["GET"])
@authenticate
def get_payment_history(user):
    try:
        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Get payment history with payment method details
            cursor.execute("""
                SELECT p.id, p.amount, p.status, p.transaction_date,
                       pm.card_number, pm.card_holder_name
                FROM payments p
                LEFT JOIN payment_methods pm ON p.payment_method_id = pm.id
                WHERE p.user_id = %s
                ORDER BY p.transaction_date DESC
            """, (user["id"],))
            
            payments = cursor.fetchall()
            cursor.close()
            
            # Format dates and amounts
            for payment in payments:
                payment["transaction_date"] = payment["transaction_date"].strftime("%Y-%m-%d")
                payment["amount"] = float(payment["amount"])
            
            return jsonify(payments)
            
    except Exception as e:
        logger.error(f"Error getting payment history: {str(e)}")
        return jsonify({"error": "Failed to get payment history"}), 500
