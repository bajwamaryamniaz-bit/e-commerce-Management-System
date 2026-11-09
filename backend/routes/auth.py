from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from ..database import execute_query

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required"}), 400

    user = execute_query(
        "SELECT user_id, username, email, password_hash, role FROM Users WHERE username = %s OR email = %s;",
        (username, username),
        fetch="one"
    )

    if not user:
        return jsonify({"success": False, "message": "Invalid username or password"}), 401

    if not check_password_hash(user['password_hash'], password):
        return jsonify({"success": False, "message": "Invalid username or password"}), 401

    # Store user in session or return token info
    user_data = {
        "user_id": user['user_id'],
        "username": user['username'],
        "email": user['email'],
        "role": user['role']
    }
    return jsonify({"success": True, "message": "Login successful", "user": user_data})

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'admin')

    if not username or not email or not password:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    hashed_pw = generate_password_hash(password)

    try:
        execute_query(
            "INSERT INTO Users (username, email, password_hash, role) VALUES (%s, %s, %s, %s);",
            (username, email, hashed_pw, role)
        )
        return jsonify({"success": True, "message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"success": False, "message": "Username or email already exists"}), 409
