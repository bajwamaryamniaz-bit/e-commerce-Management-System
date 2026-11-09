from flask import Blueprint, request, jsonify
from ..services.purchase_service import create_purchase_transaction, get_all_purchases, get_purchase_details

purchases_bp = Blueprint('purchases', __name__)

@purchases_bp.route('', methods=['GET'])
def list_purchases():
    try:
        data = get_all_purchases()
        return jsonify({"success": True, "data": data or []})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@purchases_bp.route('/<int:purchase_id>', methods=['GET'])
def get_purchase(purchase_id):
    try:
        data = get_purchase_details(purchase_id)
        if not data:
            return jsonify({"success": False, "message": "Purchase order not found"}), 404
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@purchases_bp.route('', methods=['POST'])
def add_purchase():
    data = request.get_json() or {}
    supplier_id = data.get('supplier_id')
    items = data.get('items', [])

    if not supplier_id:
        return jsonify({"success": False, "message": "Supplier must be selected."}), 400
    if not items or not isinstance(items, list) or len(items) == 0:
        return jsonify({"success": False, "message": "At least one product item is required."}), 400

    try:
        result = create_purchase_transaction(int(supplier_id), items)
        return jsonify({
            "success": True, 
            "message": "Purchase order created and inventory stock incremented successfully.",
            "data": result
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": f"Purchase transaction failed: {str(e)}"}), 400
