from ..database import execute_transaction_block, execute_query

def create_sale_transaction(customer_id, items):
    """
    Executes a sale workflow inside an ACID transaction:
    1. Validates all line items.
    2. Checks current stock in Inventory for each item. If insufficient, rolls back and raises an error!
    3. Inserts Sale header record.
    4. Inserts Sale_Details line items.
    5. Deducts sold quantities safely from Inventory.
    """
    if not items or len(items) == 0:
        raise ValueError("Sale must contain at least one product item.")

    def transaction_work(cursor, engine):
        ph = "%s" if engine == "postgresql" else "?"

        # Step 1: Pre-check stock for all items
        for item in items:
            product_id = int(item['product_id'])
            requested_qty = int(item['quantity'])

            cursor.execute(
                f"""
                SELECT p.product_name, COALESCE(i.quantity_available, 0) AS stock
                FROM Product p
                LEFT JOIN Inventory i ON p.product_id = i.product_id
                WHERE p.product_id = {ph};
                """,
                (product_id,)
            )
            prod_row = cursor.fetchone()
            if not prod_row:
                raise ValueError(f"Product ID {product_id} not found in catalog.")
            
            # Extract values based on driver dictionary or sqlite row
            stock = prod_row['stock'] if isinstance(prod_row, dict) else prod_row[1]
            prod_name = prod_row['product_name'] if isinstance(prod_row, dict) else prod_row[0]

            if stock < requested_qty:
                raise ValueError(
                    f"Insufficient stock for '{prod_name}'. Requested: {requested_qty}, Available in Inventory: {stock}."
                )

        # Step 2: Calculate total amount
        total_amount = sum(float(item['quantity']) * float(item['unit_price']) for item in items)

        # Step 3: Insert Sale Header
        if engine == "postgresql":
            cursor.execute(
                f"INSERT INTO Sale (customer_id, total_amount) VALUES ({ph}, {ph}) RETURNING sale_id;",
                (customer_id, total_amount)
            )
            sale_id = cursor.fetchone()['sale_id']
        else:
            cursor.execute(
                f"INSERT INTO Sale (customer_id, total_amount) VALUES ({ph}, {ph});",
                (customer_id, total_amount)
            )
            sale_id = cursor.lastrowid

        # Step 4: Insert Line Items and Deduct Inventory
        for item in items:
            product_id = int(item['product_id'])
            quantity = int(item['quantity'])
            unit_price = float(item['unit_price'])

            # Insert Sale_Details
            cursor.execute(
                f"INSERT INTO Sale_Details (sale_id, product_id, quantity, unit_price) VALUES ({ph}, {ph}, {ph}, {ph});",
                (sale_id, product_id, quantity, unit_price)
            )

            # Deduct from Inventory
            cursor.execute(
                f"""
                UPDATE Inventory 
                SET quantity_available = quantity_available - {ph},
                    last_updated = CURRENT_TIMESTAMP
                WHERE product_id = {ph};
                """,
                (quantity, product_id)
            )

        return {
            "sale_id": sale_id,
            "customer_id": customer_id,
            "total_amount": total_amount,
            "items_count": len(items),
            "status": "success",
            "message": "Sale transaction completed and inventory updated successfully."
        }

    return execute_transaction_block(transaction_work)

def get_all_sales():
    """
    Retrieves sales history with customer names and calculated totals.
    """
    sql = """
    SELECT 
        s.sale_id,
        s.customer_id,
        c.name AS customer_name,
        c.phone AS customer_phone,
        s.sale_date,
        s.total_amount,
        COUNT(sd.sale_detail_id) AS total_items
    FROM Sale s
    JOIN Customer c ON s.customer_id = c.customer_id
    LEFT JOIN Sale_Details sd ON s.sale_id = sd.sale_id
    GROUP BY s.sale_id, s.customer_id, c.name, c.phone, s.sale_date, s.total_amount
    ORDER BY s.sale_date DESC;
    """
    return execute_query(sql, fetch="all")

def get_sale_details(sale_id):
    """
    Retrieves full invoice details for a specific sale.
    """
    sql_header = """
    SELECT s.sale_id, s.sale_date, s.total_amount, c.name AS customer_name, c.phone, c.email, c.address
    FROM Sale s
    JOIN Customer c ON s.customer_id = c.customer_id
    WHERE s.sale_id = %s;
    """
    header = execute_query(sql_header, (sale_id,), fetch="one")
    if not header:
        return None
        
    sql_items = """
    SELECT sd.sale_detail_id, sd.product_id, pr.product_name, sd.quantity, sd.unit_price, (sd.quantity * sd.unit_price) AS subtotal
    FROM Sale_Details sd
    JOIN Product pr ON sd.product_id = pr.product_id
    WHERE sd.sale_id = %s;
    """
    items = execute_query(sql_items, (sale_id,), fetch="all")
    header['items'] = items
    return header
