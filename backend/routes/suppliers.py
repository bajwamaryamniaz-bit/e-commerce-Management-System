from flask import Blueprint, request, jsonify
from ..database import execute_query

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('', methods=['GET'])
def get_suppliers():
    search = request.args.get('search', '').strip()
    query = """
    SELECT 
        s.supplier_id,
        s.supplier_name,
        s.phone,
        s.email,
        s.address,
        s.created_at,
        COUNT(p.purchase_id) AS total_purchases
    FROM Supplier s
    LEFT JOIN Purchase p ON s.supplier_id = p.supplier_id
    WHERE 1=1
    """
    params = []
    if search:
        query += " AND (LOWER(s.supplier_name) LIKE LOWER(%s) OR LOWER(s.email) LIKE LOWER(%s) OR s.phone LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query += " GROUP BY s.supplier_id, s.supplier_name, s.phone, s.email, s.address, s.created_at ORDER BY s.supplier_id DESC;"
    suppliers = execute_query(query, tuple(params) if params else None, fetch="all")
    return jsonify({"success": True, "data": suppliers or []})

@suppliers_bp.route('/<int:supplier_id>', methods=['GET'])
def get_supplier(supplier_id):
    supplier = execute_query("SELECT * FROM Supplier WHERE supplier_id = %s;", (supplier_id,), fetch="one")
    if not supplier:
        return jsonify({"success": False, "message": "Supplier not found."}), 404
    return jsonify({"success": True, "data": supplier})

@suppliers_bp.route('', methods=['POST'])
def add_supplier():
    data = request.get_json() or {}
    name = data.get('supplier_name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()
    address = data.get('address', '').strip()

    if not name:
        return jsonify({"success": False, "message": "Supplier name is required."}), 400

    try:
        sql = "INSERT INTO Supplier (supplier_name, phone, email, address) VALUES (%s, %s, %s, %s);"
        execute_query(sql, (name, phone, email, address))
        return jsonify({"success": True, "message": "Supplier added successfully."}), 201
    except Exception as e:
        return jsonify({"success": False, "message": f"Error saving supplier: {str(e)}"}), 400

@suppliers_bp.route('/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    data = request.get_json() or {}
    name = data.get('supplier_name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()
    address = data.get('address', '').strip()

    if not name:
        return jsonify({"success": False, "message": "Supplier name is required."}), 400

    sql = "UPDATE Supplier SET supplier_name = %s, phone = %s, email = %s, address = %s WHERE supplier_id = %s;"
    execute_query(sql, (name, phone, email, address, supplier_id))
    return jsonify({"success": True, "message": "Supplier updated successfully."})

@suppliers_bp.route('/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    try:
        execute_query("DELETE FROM Supplier WHERE supplier_id = %s;", (supplier_id,))
        return jsonify({"success": True, "message": "Supplier deleted successfully."})
    except Exception as e:
        return jsonify({"success": False, "message": f"Cannot delete supplier (linked purchases exist): {str(e)}"}), 400
