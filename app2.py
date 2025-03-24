from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

# MySQL Connection
def get_db_connection():
    return mysql.connector.connect(
        host="gym-database.clqqsuqke2sz.us-east-2.rds.amazonaws.com",
        user="root",
        password="COSCAdmin",
        database="gym_management"
    )

# Register a new user
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    db = get_db_connection()
    cursor = db.cursor()

    sql = """
	INSERT INTO users (role, name, dob, email, password, address, city, state, zipcode, membership_expiry, auto_payment)
	VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
	"""

    try:
        cursor.execute(sql, (
		data.get('role', 'non_member'),
		data['name'],
		data['dob'],
		data['email'],
		data['password'],
		data['address'],
		data['city'],
		data['state'],
		data['zipcode'],
		data.get('membership_expiry'),
		data.get('auto_payment', 0)
	))
        db.commit()
        return jsonify({"message": "User registered successfully!"})

    except mysql.connector.IntegrityError:
        return jsonify({"error": "Username already exists!"}), 400

    finally:
        db.close()

# Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    sql = "SELECT * FROM users WHERE email = %s AND password = %s"
    cursor.execute(sql, (data['email'], data['password']))

    user = cursor.fetchone()
    db.close()

    if user:
        return jsonify({
		"message": "Login successful!",
		"user": {
			"id": user['id'],
			"role": user['role'],
			"name": user['name'],
			"dob": user['dob'],
			"email": user['email'],
		}
	})

    else:
        return jsonify({"error": "Invalid email or password"}), 401


# Route: Home
@app.route('/')
def home():
    return "Gym Management System API Running!"

# Route: Get all memberships
@app.route('/memberships', methods=['GET'])
def get_memberships():
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM memberships")
    memberships = cursor.fetchall()
    return jsonify(memberships)

# Route: Add a new membership
@app.route('/membership', methods=['POST'])
def add_membership():
    data = request.json
    db = get_db_connection()
    cursor = db.cursor()

    sql = "INSERT INTO memberships (name, price, duration) VALUES (%s, %s, %s)"
    cursor.execute(sql, (data['name'], data['price'], data['duration']))
    db.commit()
    return jsonify({"message": "Membership added!"})

# Get Available Classes
@app.route('/classes', methods=['GET'])
def get_classes():
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM classes")
    classes = cursor.fetchall()
    return jsonify(classes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
