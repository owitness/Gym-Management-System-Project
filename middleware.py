import jwt
from flask import request, jsonify
from config import SECRET_KEY
from functools import wraps

# 🔹 Verify JWT Token
def authenticate(f):
    @wraps(f)  # ✅ Preserve the original function name
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"error": "Missing token"}), 401

        try:
            decoded_token = jwt.decode(token.split(" ")[1], SECRET_KEY, algorithms=["HS256"])
            return f(decoded_token, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

    return wrapper  # ✅ Function name is preserved

# 🔹 Admin-Only Access
def admin_required(f):
    @wraps(f)  # ✅ Preserve the function name
    def wrapper(user, *args, **kwargs):
        if user["role"] != "admin":
            return jsonify({"error": "Unauthorized - Admins Only"}), 403
        return f(user, *args, **kwargs)

    return wrapper  # ✅ Function name is preserved

# 🔹 Member-Only Access
def member_required(f):
    @wraps(f)  # ✅ Preserve the function name
    def wrapper(user, *args, **kwargs):
        if user["role"] not in ["member", "admin"]:
            return jsonify({"error": "Unauthorized - Members Only"}), 403
        return f(user, *args, **kwargs)

    return wrapper  # ✅ Function name is preserved
