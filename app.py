from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from routes.auth import auth_bp
from routes.users import users_bp
from routes.memberships import memberships_bp
from routes.dashboard import dashboard_bp
from routes.admin import admin_bp
from routes.trainer import trainer_bp
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

# Exempt API routes from CSRF protection
csrf.exempt(auth_bp)
csrf.exempt(users_bp)
csrf.exempt(memberships_bp)
csrf.exempt(dashboard_bp)
csrf.exempt(admin_bp)
csrf.exempt(trainer_bp)
csrf.exempt(payments_bp)

# Configure CORS with specific options
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5000", "http://127.0.0.1:5000", 
                   "http://localhost:5001", "http://127.0.0.1:5001"],
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

# ✅ Register API Routes
app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(users_bp, url_prefix="/api")
app.register_blueprint(memberships_bp, url_prefix="/api")
app.register_blueprint(dashboard_bp, url_prefix="/api")
app.register_blueprint(admin_bp, url_prefix="/api")
app.register_blueprint(trainer_bp, url_prefix="/api")
app.register_blueprint(payments_bp, url_prefix="/api")

# Add security headers to all responses
@app.after_request
def after_request(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "connect-src 'self' http://localhost:5001 http://127.0.0.1:5001;"
    )
    return add_security_headers(response)

# Public routes
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login")
def login():
    return render_template("signin.html")

@app.route("/signup")
def signup_page():
    return render_template("join.html")

@app.route("/memberships")
def memberships():
    return render_template("memberships.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/calendar")
def calendar():
    return render_template("calendar.html")

# Membership type routes
@app.route("/membership/monthly")
def monthly_membership():
    return render_template("monthly.html")

@app.route("/membership/annual")
def annual_membership():
    return render_template("annual.html")

@app.route("/membership/student")
def student_membership():
    return render_template("student.html")

# Protected routes
@app.route("/dashboard")
@authenticate
def dashboard(user):
    if user.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    elif user.get("role") == "trainer":
        return redirect(url_for("trainer_dashboard"))
    return render_template("dashboard.html", user=user)

@app.route("/admin/dashboard")
@authenticate
def admin_dashboard(user):
    if user.get("role") != "admin":
        return redirect(url_for("dashboard"))
    return render_template("admin.html", user=user)

@app.route("/trainer/dashboard")
@authenticate
def trainer_dashboard(user):
    if user.get("role") != "trainer":
        return redirect(url_for("dashboard"))
    return render_template("trainer_dashboard.html", user=user)

@app.route("/profile")
@authenticate
def profile(user):
    return render_template("profile.html", user=user)

@app.route("/classes")
@authenticate
def classes(user):
    return render_template("classes.html", user=user)

@app.route("/payment-methods")
@authenticate
def payment_methods(user):
    return render_template("payment_methods.html", user=user)

@app.route("/attendance")
@authenticate
def attendance(user):
    return render_template("attendance.html", user=user)

@app.route("/health")
def health_check():
    return jsonify({"status": "healthy"}), 200

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
