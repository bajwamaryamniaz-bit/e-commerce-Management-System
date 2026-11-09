from flask import Blueprint, request, jsonify
from ..database import execute_query, execute_transaction_block

products_bp = Blueprint('products', __name__)

@products_bp.route('', methods=['GET'])
def get_products():
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id')

    query = """
    SELECT 
        p.product_id,
        p.product_name,
        p.category_id,
        c.category_name,
        p.price,
        p.description,
        COALESCE(i.quantity_available, 0) AS stock_quantity,
        COALESCE(i.low_stock_threshold, 10) AS low_stock_threshold,
        CASE 
            WHEN COALESCE(i.quantity_available, 0) <= 0 THEN 'Out of Stock'
            WHEN COALESCE(i.quantity_available, 0) <= COALESCE(i.low_stock_threshold, 10) THEN 'Low Stock'
            ELSE 'In Stock'
        END AS stock_status
    FROM Product p
    LEFT JOIN Category c ON p.category_id = c.category_id
    LEFT JOIN Inventory i ON p.product_id = i.product_id
    WHERE 1=1
    """
    params = []
    if search:
        query += " AND (LOWER(p.product_name) LIKE LOWER(%s) OR LOWER(p.description) LIKE LOWER(%s))"
        params.extend([f"%{search}%", f"%{search}%"])
    if category_id:
        query += " AND p.category_id = %s"
        params.append(category_id)

    query += " ORDER BY p.product_id DESC;"
    products = execute_query(query, tuple(params) if params else None, fetch="all")
    return jsonify({"success": True, "data": products or []})

@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    query = """
    SELECT p.*, c.category_name, COALESCE(i.quantity_available, 0) AS stock_quantity
    FROM Product p
    LEFT JOIN Category c ON p.category_id = c.category_id
    LEFT JOIN Inventory i ON p.product_id = i.product_id
    WHERE p.product_id = %s;
    """
    product = execute_query(query, (product_id,), fetch="one")
    if not product:
        return jsonify({"success": False, "message": "Product not found"}), 404
    return jsonify({"success": True, "data": product})

@products_bp.route('', methods=['POST'])
def add_product():
    data = request.get_json() or {}
    product_name = data.get('product_name', '').strip()
    category_id = data.get('category_id')
    price = data.get('price')
    description = data.get('description', '').strip()
    initial_stock = int(data.get('initial_stock', 0))

    if not product_name or price is None:
        return jsonify({"success": False, "message": "Product name and price are required."}), 400

    try:
        price = float(price)
        if price < 0:
            return jsonify({"success": False, "message": "Price must be non-negative."}), 400
    except ValueError:
        return jsonify({"success": False, "message": "Price must be a valid number."}), 400

    def create_product_tx(cursor, engine):
        ph = "%s" if engine == "postgresql" else "?"
        if engine == "postgresql":
            cursor.execute(
                f"""
                INSERT INTO Product (product_name, category_id, price, description)
                VALUES ({ph}, {ph}, {ph}, {ph})
                RETURNING product_id;
                """,
                (product_name, category_id, price, description)
            )
            new_id = cursor.fetchone()['product_id']
        else:
            cursor.execute(
                f"""
                INSERT INTO Product (product_name, category_id, price, description)
                VALUES ({ph}, {ph}, {ph}, {ph});
                """,
                (product_name, category_id, price, description)
            )
            new_id = cursor.lastrowid

        # Initialize corresponding Inventory row (1-to-1 relationship)
        cursor.execute(
            f"""
            INSERT INTO Inventory (product_id, quantity_available, low_stock_threshold)
            VALUES ({ph}, {ph}, 10);
            """,
            (new_id, initial_stock)
        )
        return new_id

    try:
        new_product_id = execute_transaction_block(create_product_tx)
        return jsonify({
            "success": True, 
            "message": "Product and initial inventory created successfully.",
            "product_id": new_product_id
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": f"Error adding product: {str(e)}"}), 500

@products_bp.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json() or {}
    product_name = data.get('product_name', '').strip()
    category_id = data.get('category_id')
    price = data.get('price')
    description = data.get('description', '').strip()

    if not product_name or price is None:
        return jsonify({"success": False, "message": "Product name and price are required."}), 400

    sql = """
    UPDATE Product
    SET product_name = %s, category_id = %s, price = %s, description = %s
    WHERE product_id = %s;
    """
    execute_query(sql, (product_name, category_id, price, description, product_id))
    return jsonify({"success": True, "message": "Product updated successfully."})

@products_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        execute_query("DELETE FROM Product WHERE product_id = %s;", (product_id,))
        return jsonify({"success": True, "message": "Product deleted successfully."})
    except Exception as e:
        return jsonify({"success": False, "message": f"Cannot delete product (it may be linked in sales or purchases): {str(e)}"}), 400

@products_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = execute_query("SELECT * FROM Category ORDER BY category_name ASC;", fetch="all")
    return jsonify({"success": True, "data": categories or []})

@products_bp.route('/categories', methods=['POST'])
def add_category():
    data = request.get_json() or {}
    category_name = data.get('category_name', '').strip()
    description = data.get('description', '').strip()

    if not category_name:
        return jsonify({"success": False, "message": "Category name is required."}), 400

    try:
        execute_query(
            "INSERT INTO Category (category_name, description) VALUES (%s, %s);",
            (category_name, description)
        )
        return jsonify({"success": True, "message": "Category created successfully."}), 201
    except Exception as e:
        return jsonify({"success": False, "message": f"Category already exists or error: {str(e)}"}), 400
