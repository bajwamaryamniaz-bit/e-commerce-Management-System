from flask import Blueprint, request, jsonify
from ..database import execute_query

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('', methods=['GET'])
def get_customers():
    search = request.args.get('search', '').strip()
    query = """
    SELECT 
        c.customer_id,
        c.name,
        c.phone,
        c.email,
        c.address,
        c.created_at,
        COUNT(s.sale_id) AS total_orders,
        COALESCE(SUM(s.total_amount), 0) AS total_spent
    FROM Customer c
    LEFT JOIN Sale s ON c.customer_id = s.customer_id
    WHERE 1=1
    """
    params = []
    if search:
        query += " AND (LOWER(c.name) LIKE LOWER(%s) OR LOWER(c.email) LIKE LOWER(%s) OR c.phone LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query += " GROUP BY c.customer_id, c.name, c.phone, c.email, c.address, c.created_at ORDER BY c.customer_id DESC;"
    customers = execute_query(query, tuple(params) if params else None, fetch="all")
    return jsonify({"success": True, "data": customers or []})

@customers_bp.route('/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    customer = execute_query("SELECT * FROM Customer WHERE customer_id = %s;", (customer_id,), fetch="one")
    if not customer:
        return jsonify({"success": False, "message": "Customer not found."}), 404
    return jsonify({"success": True, "data": customer})

@customers_bp.route('', methods=['POST'])
def add_customer():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip() or None
    address = data.get('address', '').strip()

    if not name:
        return jsonify({"success": False, "message": "Customer name is required."}), 400

    try:
        sql = "INSERT INTO Customer (name, phone, email, address) VALUES (%s, %s, %s, %s);"
        execute_query(sql, (name, phone, email, address))
        return jsonify({"success": True, "message": "Customer registered successfully."}), 201
    except Exception as e:
        return jsonify({"success": False, "message": f"Error saving customer: {str(e)}"}), 400

@customers_bp.route('/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip() or None
    address = data.get('address', '').strip()

    if not name:
        return jsonify({"success": False, "message": "Customer name is required."}), 400

    sql = "UPDATE Customer SET name = %s, phone = %s, email = %s, address = %s WHERE customer_id = %s;"
    execute_query(sql, (name, phone, email, address, customer_id))
    return jsonify({"success": True, "message": "Customer updated successfully."})

@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    try:
        execute_query("DELETE FROM Customer WHERE customer_id = %s;", (customer_id,))
        return jsonify({"success": True, "message": "Customer removed successfully."})
    except Exception as e:
        return jsonify({"success": False, "message": f"Cannot delete customer (linked sales exist): {str(e)}"}), 400
