from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from routes.auth import auth_bp
from routes.users import users_bp
from routes.memberships import memberships_bp
#from routes.attendance import attendance_bp
#from routes.bookings import bookings_bp
#from routes.classes import classes_bp
from routes.payments import payments_bp
from middleware import authenticate, add_security_headers
import jwt
from config import SECRET_KEY
import logging
from logging.handlers import RotatingFileHandler
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
csrf = CSRFProtect(app)

# Configure CORS with specific options
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/gym_management.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Gym Management System startup')

# ✅ Register API Routes (Make Sure Each is Registered Only ONCE)
app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(users_bp, url_prefix="/api")
app.register_blueprint(memberships_bp, url_prefix="/api")
#app.register_blueprint(attendance_bp, url_prefix="/api")
#app.register_blueprint(bookings_bp, url_prefix="/api")
#app.register_blueprint(classes_bp, url_prefix="/api")
app.register_blueprint(payments_bp, url_prefix="/api")

# Add security headers to all responses
@app.after_request
def after_request(response):
    return add_security_headers(response)

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
    if user.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    return render_template("dashboard.html")

@app.route("/admin/dashboard")
@authenticate
def admin_dashboard(user):
    if user.get("role") != "admin":
        return redirect(url_for("dashboard"))
    return render_template("admin_dashboard.html")

# Error handlers
@app.errorhandler(401)
def unauthorized_error(error):
    app.logger.warning(f"Unauthorized access attempt from IP: {request.remote_addr}")
    return redirect(url_for("login"))

@app.errorhandler(403)
def forbidden_error(error):
    app.logger.warning(f"Forbidden access attempt from IP: {request.remote_addr}")
    return jsonify({"error": "Access forbidden"}), 403

@app.errorhandler(404)
def not_found_error(error):
    app.logger.warning(f"404 error for URL: {request.url}")
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(429)
def too_many_requests_error(error):
    app.logger.warning(f"Rate limit exceeded for IP: {request.remote_addr}")
    return jsonify({"error": "Too many requests. Please try again later."}), 429

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
