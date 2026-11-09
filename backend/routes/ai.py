from flask import Blueprint, request, jsonify
from ..services.ai_service import process_ai_query, get_live_db_context

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/chat', methods=['POST'])
def chat():
    """
    Handles natural language queries from the AI Assistant interface.
    """
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    message = data.get('message', '').strip()
    if not message:
        raw_text = request.get_data(as_text=True)
        if raw_text and not raw_text.startswith('{'):
            message = raw_text.strip()

    if not message:
        return jsonify({"success": False, "message": "Message is required."}), 400

    try:
        reply = process_ai_query(message)
        return jsonify({
            "success": True,
            "reply": reply,
            "timestamp": None
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@ai_bp.route('/quick-stats', methods=['GET'])
def quick_stats():
    """
    Returns live database context for the AI panel.
    """
    try:
        ctx = get_live_db_context()
        return jsonify({"success": True, "data": ctx})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
