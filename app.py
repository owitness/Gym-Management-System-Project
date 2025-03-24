from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_cors import CORS
from routes.auth import auth_bp
from routes.users import users_bp
from routes.memberships import memberships_bp
#from routes.attendance import attendance_bp
#from routes.bookings import bookings_bp
#from routes.classes import classes_bp
from routes.payments import payments_bp
from middleware import authenticate
import jwt
from config import SECRET_KEY

app = Flask(__name__)
CORS(app)  # ✅ Enable CORS to allow frontend access

# ✅ Register API Routes (Make Sure Each is Registered Only ONCE)
app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(users_bp, url_prefix="/api")
app.register_blueprint(memberships_bp, url_prefix="/api")
#app.register_blueprint(attendance_bp, url_prefix="/api")
#app.register_blueprint(bookings_bp, url_prefix="/api")
#app.register_blueprint(classes_bp, url_prefix="/api")
app.register_blueprint(payments_bp, url_prefix="/api")

@app.route("/")
def home():
    return render_template("home.html")  # Renders homepage

@app.route("/login")
def login():
    return render_template("signin.html")  # Renders login page

@app.route("/signup")
def register():
    return render_template("signup.html")  # Renders registration page

@app.route("/memberships")
def memberships():
    return render_template("memberships.html")

@app.route("/dashboard")
@authenticate
def dashboard(user):
    # Check user role and redirect accordingly
    if user["role"] == "admin":
        return redirect(url_for("admin_dashboard"))
    return render_template("dashboard.html")

@app.route("/admin/dashboard")
@authenticate
def admin_dashboard(user):
    if user["role"] != "admin":
        return redirect(url_for("dashboard"))
    return render_template("admin_dashboard.html")

# Error handlers
@app.errorhandler(401)
def unauthorized_error(error):
    return redirect(url_for("login"))

@app.errorhandler(403)
def forbidden_error(error):
    return jsonify({"error": "Access forbidden"}), 403

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
