from flask import Flask, render_template, redirect, url_for, request, jsonify, g, send_from_directory, session
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from routes.auth import auth_bp
from routes.users import users_bp
from routes.memberships import memberships_bp
from routes.dashboard import dashboard_bp
from routes.admin import admin_bp
from routes.trainer import trainer_bp
from routes.payments import payments_bp
from routes.classes import class_schedule_bp
from middleware import (
    authenticate, add_security_headers, verify_token, get_user_data, 
    create_token, AuthenticationError, refresh_token as refresh_token_func
)
import jwt
from config import SECRET_KEY
import logging
from logging.handlers import RotatingFileHandler
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from generate_weekly_classes import generate_weekly_classes  # import your function
from routes.attendance import attendance_bp
from routes.equipment import equipment_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Track if this is the first request to the app
app.config['FIRST_REQUEST'] = True

csrf = CSRFProtect(app)

# Exempt API routes from CSRF protection
csrf.exempt(auth_bp)
csrf.exempt(users_bp)
csrf.exempt(memberships_bp)
csrf.exempt(dashboard_bp)
csrf.exempt(admin_bp)
csrf.exempt(trainer_bp)
csrf.exempt(payments_bp)
csrf.exempt(class_schedule_bp)
csrf.exempt(attendance_bp)
csrf.exempt(equipment_bp)
csrf.exempt(admin_bp)

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

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# ✅ Register API Routes
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(users_bp, url_prefix="/api")
app.register_blueprint(memberships_bp, url_prefix="/api")
app.register_blueprint(dashboard_bp, url_prefix="/api")
app.register_blueprint(trainer_bp, url_prefix="/api")
app.register_blueprint(payments_bp, url_prefix="/api")
app.register_blueprint(class_schedule_bp, url_prefix="/api")
app.register_blueprint(attendance_bp, url_prefix="/api")
app.register_blueprint(equipment_bp, url_prefix="/api/equipment")
app.register_blueprint(admin_bp, url_prefix="/api")


# Add security headers to all responses
@app.after_request
def after_request(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self' http://localhost:5001 http://127.0.0.1:5001; "
        "font-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none';"
    )
    return response


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
    token = request.args.get('token', '')
    return render_template("calendar.html", token=token)

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
def dashboard():
    # Get token using the utility function
    token = get_token_from_request()
    
    # If no token, redirect to login
    if not token:
        app.logger.warning("No token found for dashboard access - redirecting to login")
        return redirect(url_for("login"))
    
    try:
        # Verify token and get user data
        decoded = verify_token(token)
        user = get_user_data(decoded["user_id"])
        
        # Redirect based on role for special users
        if user.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        elif user.get("role") == "trainer":
            return redirect(url_for("trainer_dashboard"))
            
        # Regular member dashboard
        # Pass token to template so it's available
        return render_template("dashboard.html", user=user, token=token)
    
    except Exception as e:
        app.logger.error(f"Dashboard access error: {str(e)}")
        return redirect(url_for("login"))

@app.route("/admin/dashboard")
def admin_dashboard():
    # Get token using the utility function
    token = get_token_from_request()
    
    if not token:
        app.logger.warning("No token found for admin dashboard access - redirecting to login")
        return redirect(url_for("login"))
    
    try:
        decoded = verify_token(token)
        user = get_user_data(decoded["user_id"])
        if user.get("role") != "admin":
            return redirect(url_for("dashboard"))
        return render_template("admin.html", user=user, token=token)
    except Exception as e:
        app.logger.error(f"Admin dashboard access error: {str(e)}")
        return redirect(url_for("login"))

@app.route("/trainer/dashboard")
def trainer_dashboard():
    # Get token using the utility function
    token = get_token_from_request()
    
    if not token:
        app.logger.warning("No token found for trainer dashboard access - redirecting to login")
        return redirect(url_for("login"))
    
    try:
        decoded = verify_token(token)
        user = get_user_data(decoded["user_id"])
        
        # Ensure user is a trainer
        if user.get("role") != "trainer":
            return redirect(url_for("dashboard"))
            
        return render_template("trainer_dashboard.html", user=user, token=token)
    
    except Exception as e:
        app.logger.error(f"Trainer dashboard access error: {str(e)}")
        return redirect(url_for("login"))

@app.route("/profile")
def profile():
    # Get token using the utility function
    token = get_token_from_request()
    
    if not token:
        app.logger.warning("No token found for profile access - redirecting to login")
        return redirect(url_for("login"))
    
    try:
        # Verify token and get user data
        decoded = verify_token(token)
        user = get_user_data(decoded["user_id"])
        
        # Render profile template
        return render_template("profile.html", user=user, token=token)
    
    except Exception as e:
        app.logger.error(f"Profile access error: {str(e)}")
        return redirect(url_for("login"))

@app.route("/classes")
def classes():
    # Get token using the utility function
    token = get_token_from_request()
    
    if not token:
        app.logger.warning("No token found for classes access - redirecting to login")
        return redirect(url_for("login"))
    
    try:
        # Verify token and get user data
        decoded = verify_token(token)
        user = get_user_data(decoded["user_id"])
        
        # Render classes template
        return render_template("classes.html", user=user, token=token)
    
    except Exception as e:
        app.logger.error(f"Classes access error: {str(e)}")
        return redirect(url_for("login"))

@app.route("/payment-methods")
def payment_methods():
    # Get token using the utility function
    token = get_token_from_request()
    
    if not token:
        app.logger.warning("No token found for payment methods access - redirecting to login")
        return redirect(url_for("login"))
    
    try:
        # Verify token and get user data
        decoded = verify_token(token)
        user = get_user_data(decoded["user_id"])
        
        # Render payment_methods template
        return render_template("payment_methods.html", user=user, token=token)
    
    except Exception as e:
        app.logger.error(f"Payment methods access error: {str(e)}")
        return redirect(url_for("login"))

@app.route("/attendance")
def attendance():
    # Get token using the utility function
    token = get_token_from_request()
    
    if not token:
        app.logger.warning("No token found for attendance access - redirecting to login")
        return redirect(url_for("login"))
    
    try:
        # Verify token and get user data
        decoded = verify_token(token)
        user = get_user_data(decoded["user_id"])
        
        # Render attendance template
        return render_template("attendance.html", user=user, token=token)
    
    except Exception as e:
        app.logger.error(f"Attendance access error: {str(e)}")
        return redirect(url_for("login"))

@app.route("/health")
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/redirect-dashboard')
def redirect_dashboard_with_token():
    token = get_token_from_request()
    if not token:
        return jsonify({'error': 'Missing token'}), 400
    try:
        decoded = verify_token(token)
        user = get_user_data(decoded["user_id"])
        return render_template("dashboard.html", user=user, token=token)
    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.before_request
def before_request():
    # Clear sessions on the first request after server restart
    if app.config.get('FIRST_REQUEST', True):
        session.clear()
        app.config['FIRST_REQUEST'] = False
        app.logger.info("Server restarted: Cleared all sessions")
    
    # List of public routes that don't require authentication
    public_routes = [
        'home', 'login', 'signup_page', 'memberships', 'contact', 'calendar',
        'monthly_membership', 'annual_membership', 'student_membership',
        'health_check', 'static', 'register_user', 'dashboard', 'admin_dashboard', 
        'trainer_dashboard', 'redirect_dashboard_with_token'  # Added dashboard routes
    ]
    
    # Public API routes that don't require authentication
    public_api_routes = [
        '/api/auth/register',
        '/api/auth/login',
        '/api/auth/refresh-token'
    ]
    
    # Skip token verification for public routes, static files, and auth endpoints
    if (request.endpoint in public_routes or 
        request.path.startswith('/static/') or 
        request.path == '/favicon.ico' or
        request.path in public_api_routes):
        return
    
    # Skip token verification for OPTIONS requests (CORS preflight)
    if request.method == 'OPTIONS':
        return
    
    # Check if user is authenticated in the session
    if 'user_id' in session:
        try:
            user = get_user_data(session['user_id'])
            g.user = {
                'user_id': user['id'],
                'email': user['email'],
                'role': user['role']
            }
            return
        except Exception:
            # If session is invalid, clear it completely
            session.clear()
            # Continue to check token
    
    # Get token from Authorization header or query parameter
    token = request.headers.get('Authorization')
    if not token:
        token = request.args.get('token')
    
    if token:
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Verify token
            decoded = verify_token(token)
            g.user = decoded
            
            # Store user in session for future requests
            session['user_id'] = decoded['user_id']
            session['email'] = decoded.get('email')
            session['role'] = decoded.get('role')
            session.permanent = True
            
        except AuthenticationError as e:
            return jsonify({'error': str(e)}), 401
    else:
        # Only require token for protected endpoints
        if request.path.startswith('/api/'):
            return jsonify({'error': 'No token provided'}), 401

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
    # Check if the request wants JSON
    if request.path.startswith('/api/') or request.headers.get('Accept', '').find('application/json') != -1:
        return jsonify({"error": "Resource not found"}), 404
    # For HTML requests, redirect to a user-friendly page or the login page
    return redirect(url_for("login"))

@app.errorhandler(429)
def too_many_requests_error(error):
    app.logger.warning(f"Rate limit exceeded for IP: {request.remote_addr}")
    return jsonify({"error": "Too many requests. Please try again later."}), 429

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

def start_scheduler():
    scheduler = BackgroundScheduler()
    
    # Schedule it to run every Sunday at 12:00 AM
    scheduler.add_job(
        func=generate_weekly_classes,
        trigger="cron",
        day_of_week="sun",
        hour=0,
        minute=0,
        id="weekly_class_generator",
        replace_existing=True
    )
    scheduler.start()
    print("Scheduler started: weekly class generator active.")

# Start it
start_scheduler()

def get_token_from_request():
    """Extract token from request in order of: cookies, URL query param, Authorization header"""
    token = None
    
    # 1. Check cookies first (most reliable for page refreshes)
    if request.cookies:
        token = request.cookies.get('token')
        if not token:
            token = request.cookies.get('gym_token')
    
    # 2. If not in cookies, check URL parameters
    if not token:
        token = request.args.get('token')
    
    # 3. If still not found, check Authorization header
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
    
    return token

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/clear-session')
def clear_session():
    # Clear session data
    session.clear()
    app.logger.info(f"Session cleared by user request from IP: {request.remote_addr}")
    
    # Redirect to home page
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
