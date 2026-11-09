from flask import Blueprint, request, jsonify
from ..services.inventory_service import get_inventory_status, get_low_stock_items, adjust_stock, get_dashboard_summary

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('', methods=['GET'])
def list_inventory():
    try:
        data = get_inventory_status()
        return jsonify({"success": True, "data": data or []})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@inventory_bp.route('/low-stock', methods=['GET'])
def list_low_stock():
    try:
        data = get_low_stock_items()
        return jsonify({"success": True, "data": data or []})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@inventory_bp.route('/<int:product_id>', methods=['PUT'])
def update_stock(product_id):
    data = request.get_json() or {}
    new_quantity = data.get('quantity_available')
    low_stock_threshold = data.get('low_stock_threshold', 10)

    if new_quantity is None:
        return jsonify({"success": False, "message": "Quantity available is required."}), 400

    try:
        new_quantity = int(new_quantity)
        if new_quantity < 0:
            return jsonify({"success": False, "message": "Quantity cannot be negative."}), 400
        adjust_stock(product_id, new_quantity, int(low_stock_threshold))
        return jsonify({"success": True, "message": "Inventory updated successfully."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@inventory_bp.route('/dashboard/stats', methods=['GET'])
def get_stats():
    try:
        stats = get_dashboard_summary()
        return jsonify({"success": True, "data": stats})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
