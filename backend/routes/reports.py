from flask import Blueprint, jsonify
from ..database import execute_query

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/summary', methods=['GET'])
def get_reports_summary():
    """
    Returns aggregated metrics for analytical reporting:
    - Best-selling products by quantity and revenue
    - Customer spending leaderboards
    - Supplier procurement breakdown
    - Monthly sales trend
    """
    try:
        # Best-selling products
        best_sellers_sql = """
        SELECT 
            p.product_id,
            p.product_name,
            c.category_name,
            SUM(sd.quantity) AS total_units_sold,
            SUM(sd.quantity * sd.unit_price) AS total_revenue
        FROM Sale_Details sd
        JOIN Product p ON sd.product_id = p.product_id
        LEFT JOIN Category c ON p.category_id = c.category_id
        GROUP BY p.product_id, p.product_name, c.category_name
        ORDER BY total_revenue DESC
        LIMIT 5;
        """
        best_sellers = execute_query(best_sellers_sql, fetch="all") or []

        # Customer leaderboard
        customers_sql = """
        SELECT 
            c.customer_id,
            c.name,
            c.email,
            COUNT(s.sale_id) as total_orders,
            COALESCE(SUM(s.total_amount), 0) as total_spent
        FROM Customer c
        JOIN Sale s ON c.customer_id = s.customer_id
        GROUP BY c.customer_id, c.name, c.email
        ORDER BY total_spent DESC
        LIMIT 5;
        """
        top_customers = execute_query(customers_sql, fetch="all") or []

        # Purchases summary by supplier
        suppliers_sql = """
        SELECT 
            s.supplier_name,
            COUNT(p.purchase_id) as total_purchases,
            COALESCE(SUM(p.total_amount), 0) as total_amount
        FROM Supplier s
        LEFT JOIN Purchase p ON s.supplier_id = p.supplier_id
        GROUP BY s.supplier_name
        ORDER BY total_amount DESC;
        """
        suppliers_summary = execute_query(suppliers_sql, fetch="all") or []

        return jsonify({
            "success": True,
            "data": {
                "best_sellers": best_sellers,
                "top_customers": top_customers,
                "suppliers_summary": suppliers_summary
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
