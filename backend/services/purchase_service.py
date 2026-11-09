from ..database import execute_transaction_block, execute_query

def create_purchase_transaction(supplier_id, items):
    """
    Executes a purchase workflow inside a single ACID database transaction:
    1. Validates items and calculates total_amount
    2. Inserts Purchase header record
    3. Inserts each item into Purchase_Details
    4. Automatically increments available stock in Inventory
    """
    if not items or len(items) == 0:
        raise ValueError("Purchase must contain at least one product item.")
    
    total_amount = sum(float(item['quantity']) * float(item['unit_price']) for item in items)
    
    def transaction_work(cursor, engine):
        ph = "%s" if engine == "postgresql" else "?"
        
        # 1. Insert Purchase
        if engine == "postgresql":
            cursor.execute(
                f"INSERT INTO Purchase (supplier_id, total_amount) VALUES ({ph}, {ph}) RETURNING purchase_id;",
                (supplier_id, total_amount)
            )
            purchase_id = cursor.fetchone()['purchase_id']
        else:
            cursor.execute(
                f"INSERT INTO Purchase (supplier_id, total_amount) VALUES ({ph}, {ph});",
                (supplier_id, total_amount)
            )
            purchase_id = cursor.lastrowid

        # 2. Process items
        for item in items:
            product_id = int(item['product_id'])
            quantity = int(item['quantity'])
            unit_price = float(item['unit_price'])
            
            # Insert Line Item
            cursor.execute(
                f"INSERT INTO Purchase_Details (purchase_id, product_id, quantity, unit_price) VALUES ({ph}, {ph}, {ph}, {ph});",
                (purchase_id, product_id, quantity, unit_price)
            )
            
            # 3. Increase Inventory Stock
            if engine == "postgresql":
                cursor.execute(
                    """
                    INSERT INTO Inventory (product_id, quantity_available, last_updated)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (product_id) 
                    DO UPDATE SET 
                        quantity_available = Inventory.quantity_available + EXCLUDED.quantity_available,
                        last_updated = CURRENT_TIMESTAMP;
                    """,
                    (product_id, quantity)
                )
            else:
                # SQLite upsert
                cursor.execute(
                    """
                    INSERT INTO Inventory (product_id, quantity_available, last_updated)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT (product_id) 
                    DO UPDATE SET 
                        quantity_available = Inventory.quantity_available + excluded.quantity_available,
                        last_updated = CURRENT_TIMESTAMP;
                    """,
                    (product_id, quantity)
                )
                
        return {
            "purchase_id": purchase_id,
            "supplier_id": supplier_id,
            "total_amount": total_amount,
            "items_count": len(items),
            "status": "success"
        }

    return execute_transaction_block(transaction_work)

def get_all_purchases():
    """
    Retrieves purchase history with supplier information and item totals.
    """
    sql = """
    SELECT 
        p.purchase_id,
        p.supplier_id,
        s.supplier_name,
        p.purchase_date,
        p.total_amount,
        COUNT(pd.purchase_detail_id) AS total_items
    FROM Purchase p
    JOIN Supplier s ON p.supplier_id = s.supplier_id
    LEFT JOIN Purchase_Details pd ON p.purchase_id = pd.purchase_id
    GROUP BY p.purchase_id, p.supplier_id, s.supplier_name, p.purchase_date, p.total_amount
    ORDER BY p.purchase_date DESC;
    """
    return execute_query(sql, fetch="all")

def get_purchase_details(purchase_id):
    """
    Retrieves details for a specific purchase transaction.
    """
    sql_header = """
    SELECT p.purchase_id, p.purchase_date, p.total_amount, s.supplier_name, s.phone, s.email
    FROM Purchase p
    JOIN Supplier s ON p.supplier_id = s.supplier_id
    WHERE p.purchase_id = %s;
    """
    header = execute_query(sql_header, (purchase_id,), fetch="one")
    
    if not header:
        return None
        
    sql_items = """
    SELECT pd.purchase_detail_id, pd.product_id, pr.product_name, pd.quantity, pd.unit_price, (pd.quantity * pd.unit_price) AS subtotal
    FROM Purchase_Details pd
    JOIN Product pr ON pd.product_id = pr.product_id
    WHERE pd.purchase_id = %s;
    """
    items = execute_query(sql_items, (purchase_id,), fetch="all")
    header['items'] = items
    return header
