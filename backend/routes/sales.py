from flask import Blueprint, request, jsonify
from ..services.sale_service import create_sale_transaction, get_all_sales, get_sale_details

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('', methods=['GET'])
def list_sales():
    try:
        data = get_all_sales()
        return jsonify({"success": True, "data": data or []})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@sales_bp.route('/<int:sale_id>', methods=['GET'])
def get_sale(sale_id):
    try:
        data = get_sale_details(sale_id)
        if not data:
            return jsonify({"success": False, "message": "Sale transaction not found."}), 404
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@sales_bp.route('', methods=['POST'])
def add_sale():
    data = request.get_json() or {}
    customer_id = data.get('customer_id')
    items = data.get('items', [])

    if not customer_id:
        return jsonify({"success": False, "message": "Customer must be selected."}), 400
    if not items or not isinstance(items, list) or len(items) == 0:
        return jsonify({"success": False, "message": "At least one product item is required for the sale."}), 400

    try:
        result = create_sale_transaction(int(customer_id), items)
        return jsonify({
            "success": True,
            "message": "Sale completed successfully. Stock updated.",
            "data": result
        }), 201
    except ValueError as ve:
        # Handles business logic violation (e.g., insufficient stock)
        return jsonify({"success": False, "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Sale transaction failed: {str(e)}"}), 500
