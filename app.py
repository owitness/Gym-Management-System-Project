from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_cors import CORS
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
import json
from datetime import datetime

app = Flask(__name__)

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
    os.makedirs('logs')

# Create separate log files for different purposes
def setup_logger(name, log_file, level=logging.INFO):
    handler = RotatingFileHandler(
        f'logs/{log_file}',
        maxBytes=10240,
        backupCount=10
    )
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]'
    )
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger

# Set up different loggers for different purposes
app.logger = setup_logger('app', 'gym_management.log')
auth_logger = setup_logger('auth', 'auth.log')
error_logger = setup_logger('error', 'error.log', level=logging.ERROR)
security_logger = setup_logger('security', 'security.log')

# Log application startup with system information
app.logger.info('Gym Management System startup')
app.logger.info(f'Environment: {app.env}')
app.logger.info(f'Debug Mode: {app.debug}')
app.logger.info(f'Testing Mode: {app.testing}')

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
    # Log request details
    request_data = {
        'timestamp': datetime.now().isoformat(),
        'method': request.method,
        'path': request.path,
        'ip': request.remote_addr,
        'user_agent': request.user_agent.string,
        'status_code': response.status_code
    }
    app.logger.info(f'Request: {json.dumps(request_data)}')
    return add_security_headers(response)

@app.route("/")
def home():
    app.logger.info('Home page accessed')
    return render_template("home.html")  # Renders homepage

@app.route("/login")
def login():
    app.logger.info('Login page accessed')
    return render_template("signin.html")  # Renders login page

@app.route("/signup")
def register():
    app.logger.info('Registration page accessed')
    return render_template("signup.html")  # Renders registration page

@app.route("/memberships")
def memberships():
    app.logger.info('Memberships page accessed')
    return render_template("memberships.html")

@app.route("/dashboard")
@authenticate
def dashboard(user):
    app.logger.info(f'Dashboard accessed by user: {user.get("email")}')
    # Check user role and redirect accordingly
    if user.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    return render_template("dashboard.html")

@app.route("/admin/dashboard")
@authenticate
def admin_dashboard(user):
    app.logger.info(f'Admin dashboard accessed by user: {user.get("email")}')
    if user.get("role") != "admin":
        return redirect(url_for("dashboard"))
    return render_template("admin_dashboard.html")

# Error handlers with enhanced logging
@app.errorhandler(401)
def unauthorized_error(error):
    security_logger.warning(f"Unauthorized access attempt from IP: {request.remote_addr}")
    security_logger.warning(f"Request details: {json.dumps({
        'method': request.method,
        'path': request.path,
        'user_agent': request.user_agent.string
    })}")
    return redirect(url_for("login"))

@app.errorhandler(403)
def forbidden_error(error):
    security_logger.warning(f"Forbidden access attempt from IP: {request.remote_addr}")
    security_logger.warning(f"Request details: {json.dumps({
        'method': request.method,
        'path': request.path,
        'user_agent': request.user_agent.string
    })}")
    return jsonify({"error": "Access forbidden"}), 403

@app.errorhandler(404)
def not_found_error(error):
    error_logger.warning(f"404 error for URL: {request.url}")
    error_logger.warning(f"Request details: {json.dumps({
        'method': request.method,
        'path': request.path,
        'user_agent': request.user_agent.string
    })}")
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(429)
def too_many_requests_error(error):
    security_logger.warning(f"Rate limit exceeded for IP: {request.remote_addr}")
    security_logger.warning(f"Request details: {json.dumps({
        'method': request.method,
        'path': request.path,
        'user_agent': request.user_agent.string
    })}")
    return jsonify({"error": "Too many requests. Please try again later."}), 429

@app.errorhandler(500)
def internal_error(error):
    error_logger.error(f"Internal server error: {str(error)}")
    error_logger.error(f"Request details: {json.dumps({
        'method': request.method,
        'path': request.path,
        'user_agent': request.user_agent.string
    })}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
