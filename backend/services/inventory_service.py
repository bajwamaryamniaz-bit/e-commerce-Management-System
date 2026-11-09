from ..database import execute_query

def get_inventory_status():
    """
    Retrieves full inventory listing with product and category info,
    calculating stock status (In Stock, Low Stock, Out of Stock).
    """
    sql = """
    SELECT 
        p.product_id,
        p.product_name,
        c.category_name,
        p.price,
        COALESCE(i.inventory_id, 0) AS inventory_id,
        COALESCE(i.quantity_available, 0) AS quantity_available,
        COALESCE(i.low_stock_threshold, 10) AS low_stock_threshold,
        CASE 
            WHEN COALESCE(i.quantity_available, 0) <= 0 THEN 'Out of Stock'
            WHEN COALESCE(i.quantity_available, 0) <= COALESCE(i.low_stock_threshold, 10) THEN 'Low Stock'
            ELSE 'In Stock'
        END AS stock_status,
        i.last_updated
    FROM Product p
    LEFT JOIN Category c ON p.category_id = c.category_id
    LEFT JOIN Inventory i ON p.product_id = i.product_id
    ORDER BY p.product_id ASC;
    """
    return execute_query(sql, fetch="all")

def get_low_stock_items():
    """
    Retrieves only items that are below or equal to the low stock threshold.
    """
    sql = """
    SELECT 
        p.product_id,
        p.product_name,
        c.category_name,
        p.price,
        COALESCE(i.quantity_available, 0) AS quantity_available,
        COALESCE(i.low_stock_threshold, 10) AS low_stock_threshold
    FROM Product p
    LEFT JOIN Category c ON p.category_id = c.category_id
    LEFT JOIN Inventory i ON p.product_id = i.product_id
    WHERE COALESCE(i.quantity_available, 0) <= COALESCE(i.low_stock_threshold, 10)
    ORDER BY quantity_available ASC;
    """
    return execute_query(sql, fetch="all")

def adjust_stock(product_id, new_quantity, low_stock_threshold=10):
    """
    Adjusts stock level for a product.
    """
    sql = """
    INSERT INTO Inventory (product_id, quantity_available, low_stock_threshold, last_updated)
    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (product_id) 
    DO UPDATE SET 
        quantity_available = EXCLUDED.quantity_available,
        low_stock_threshold = EXCLUDED.low_stock_threshold,
        last_updated = CURRENT_TIMESTAMP;
    """
    return execute_query(sql, (product_id, new_quantity, low_stock_threshold))

def get_dashboard_summary():
    """
    Gathers key performance indicators for the main dashboard:
    - Total Products
    - Total Sales Revenue
    - Low Stock Count
    - Total Customers
    - Recent Sales
    - Monthly/Weekly Sales overview chart data
    """
    # 1. Product count
    prod_row = execute_query("SELECT COUNT(*) AS total_products FROM Product;", fetch="one")
    total_products = prod_row['total_products'] if prod_row else 0

    # 2. Total Sales amount
    sales_row = execute_query("SELECT COALESCE(SUM(total_amount), 0) AS total_sales FROM Sale;", fetch="one")
    total_sales = float(sales_row['total_sales']) if sales_row else 0.0

    # 3. Low stock count
    low_stock_row = execute_query(
        """
        SELECT COUNT(*) AS low_stock_count 
        FROM Inventory i 
        WHERE i.quantity_available <= i.low_stock_threshold;
        """,
        fetch="one"
    )
    low_stock_count = low_stock_row['low_stock_count'] if low_stock_row else 0

    # 4. Total Customers
    cust_row = execute_query("SELECT COUNT(*) AS total_customers FROM Customer;", fetch="one")
    total_customers = cust_row['total_customers'] if cust_row else 0

    # 5. Recent Sales list
    recent_sales_sql = """
    SELECT 
        s.sale_id,
        c.name AS customer_name,
        s.sale_date,
        s.total_amount
    FROM Sale s
    JOIN Customer c ON s.customer_id = c.customer_id
    ORDER BY s.sale_date DESC
    LIMIT 5;
    """
    recent_sales = execute_query(recent_sales_sql, fetch="all") or []

    # 6. Sales overview chart points (last 7 recorded sales or aggregated)
    chart_sql = """
    SELECT 
        TO_CHAR(sale_date, 'Mon DD') AS date_label,
        SUM(total_amount) AS daily_total
    FROM Sale
    GROUP BY TO_CHAR(sale_date, 'Mon DD'), DATE(sale_date)
    ORDER BY DATE(sale_date) ASC
    LIMIT 7;
    """
    chart_data = execute_query(chart_sql, fetch="all") or []

    return {
        "total_products": total_products,
        "total_sales": total_sales,
        "low_stock_count": low_stock_count,
        "total_customers": total_customers,
        "recent_sales": recent_sales,
        "chart_data": chart_data
    }
