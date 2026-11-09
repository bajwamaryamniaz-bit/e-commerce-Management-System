import os
import sys

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from dotenv import load_dotenv

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.config import Config

load_dotenv()

def setup_postgresql():
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("[!] psycopg2 is not installed! Please run: pip install psycopg2-binary")
        return False

    print("\n--- Connecting to PostgreSQL ---")
    try:
        if Config.DATABASE_URL:
            print("[*] Connecting via DATABASE_URL...")
            target_conn = psycopg2.connect(Config.DATABASE_URL)
        else:
            print(f"[*] Connecting to PostgreSQL (host={Config.DB_HOST}, port={Config.DB_PORT}, user={Config.DB_USER})...")
            # Connect to default postgres DB first to create ecommerce_db if needed
            server_conn = psycopg2.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database="postgres"
            )
            server_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = server_conn.cursor()
            
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (Config.DB_NAME,))
            exists = cur.fetchone()
            if not exists:
                print(f"[*] Creating PostgreSQL database '{Config.DB_NAME}'...")
                cur.execute(f'CREATE DATABASE "{Config.DB_NAME}";')
            else:
                print(f"[+] Database '{Config.DB_NAME}' already exists.")
            cur.close()
            server_conn.close()

            target_conn = psycopg2.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME
            )

        # Run schema.sql
        schema_path = os.path.join(os.path.dirname(__file__), "backend", "schema.sql")
        seed_path = os.path.join(os.path.dirname(__file__), "backend", "seed_data.sql")

        print("[*] Executing schema.sql (tables, constraints, views, indexes)...")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        
        cur = target_conn.cursor()
        cur.execute(schema_sql)
        target_conn.commit()
        print("[+] PostgreSQL Schema created successfully.")

        print("[*] Executing seed_data.sql (sample data)...")
        with open(seed_path, "r", encoding="utf-8") as f:
            seed_sql = f.read()

        cur.execute(seed_sql)
        target_conn.commit()
        cur.close()
        target_conn.close()
        print("[+] Seed data inserted into PostgreSQL successfully.")
        print("\n=======================================================")
        print("  SUCCESS: PostgreSQL Database Setup Complete!")
        print("=======================================================")
        return True

    except Exception as e:
        print(f"[!] PostgreSQL connection note: {e}")
        print("[!] To connect to your local PostgreSQL, update your password in .env (DB_PASSWORD=your_password).")
        return False

def setup_sqlite():
    import sqlite3
    db_path = Config.SQLITE_PATH
    print(f"\n--- Initializing Local Database Preview ({db_path}) ---")
    
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    sqlite_schema = """
    DROP TABLE IF EXISTS Sale_Details;
    DROP TABLE IF EXISTS Sale;
    DROP TABLE IF EXISTS Purchase_Details;
    DROP TABLE IF EXISTS Purchase;
    DROP TABLE IF EXISTS Inventory;
    DROP TABLE IF EXISTS Product;
    DROP TABLE IF EXISTS Supplier;
    DROP TABLE IF EXISTS Category;
    DROP TABLE IF EXISTS Customer;
    DROP TABLE IF EXISTS Users;

    CREATE TABLE Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'admin',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE Customer (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT UNIQUE,
        address TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE Category (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT NOT NULL UNIQUE,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE Supplier (
        supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        address TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE Product (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        category_id INTEGER REFERENCES Category(category_id) ON DELETE SET NULL,
        price REAL NOT NULL CHECK (price >= 0),
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE Inventory (
        inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL UNIQUE REFERENCES Product(product_id) ON DELETE CASCADE,
        quantity_available INTEGER NOT NULL DEFAULT 0 CHECK (quantity_available >= 0),
        low_stock_threshold INTEGER NOT NULL DEFAULT 10,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE Purchase (
        purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id INTEGER NOT NULL REFERENCES Supplier(supplier_id) ON DELETE RESTRICT,
        purchase_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        total_amount REAL NOT NULL DEFAULT 0.00
    );

    CREATE TABLE Purchase_Details (
        purchase_detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
        purchase_id INTEGER NOT NULL REFERENCES Purchase(purchase_id) ON DELETE CASCADE,
        product_id INTEGER NOT NULL REFERENCES Product(product_id) ON DELETE RESTRICT,
        quantity INTEGER NOT NULL CHECK (quantity > 0),
        unit_price REAL NOT NULL CHECK (unit_price >= 0)
    );

    CREATE TABLE Sale (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL REFERENCES Customer(customer_id) ON DELETE RESTRICT,
        sale_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        total_amount REAL NOT NULL DEFAULT 0.00
    );

    CREATE TABLE Sale_Details (
        sale_detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER NOT NULL REFERENCES Sale(sale_id) ON DELETE CASCADE,
        product_id INTEGER NOT NULL REFERENCES Product(product_id) ON DELETE RESTRICT,
        quantity INTEGER NOT NULL CHECK (quantity > 0),
        unit_price REAL NOT NULL CHECK (unit_price >= 0)
    );
    """
    cur.executescript(sqlite_schema)

    cur.execute("""
    INSERT INTO Users (username, email, password_hash, role)
    VALUES ('admin', 'admin@ecommerce.com', 'scrypt:32768:8:1$xP5D8qf2vR0i6mN7$b336ef10ec252ca913d94191be86dfc9aece0ee693526017bbdca81313493010471b403487c6532d56c0e3532c15ea49bf2f74e6f40b25e7144e056aa13759ad', 'admin');
    """)

    cur.executescript("""
    INSERT INTO Category (category_id, category_name, description) VALUES
    (1, 'Electronics', 'Smartphones, laptops, monitors, accessories and electronics gadgets'),
    (2, 'Apparel & Fashion', 'Men and women casual and formal clothing, sportswear, accessories'),
    (3, 'Home & Living', 'Furniture, lighting, kitchen appliances and home decors'),
    (4, 'Health & Personal Care', 'Skincare, wellness essentials, vitamins and fitness gear'),
    (5, 'Office Supplies', 'Stationery, ergonomic desk equipment, organizers');

    INSERT INTO Supplier (supplier_id, supplier_name, phone, email, address) VALUES
    (1, 'Global Tech Logistics', '+1-555-019-2831', 'supply@globaltech.com', '742 Evergreen Terrace, Tech Park, CA'),
    (2, 'Apex Apparel Wholesale', '+1-555-024-8842', 'orders@apexapparel.com', '124 Fashion Ave, New York, NY'),
    (3, 'Nordic Home Living Ltd', '+1-555-037-4491', 'contact@nordichome.com', '88 Design Way, Seattle, WA'),
    (4, 'EcoCare Health Distributors', '+1-555-048-9120', 'sales@ecocarehealth.com', '500 Wellness Blvd, Austin, TX');

    INSERT INTO Customer (customer_id, name, phone, email, address) VALUES
    (1, 'Muhammad Ali', '+92-300-1234567', 'ali.muhammad@example.com', 'House 42, Street 8, F-7/2, Islamabad'),
    (2, 'Sara Ahmed', '+92-321-9876543', 'sara.ahmed@example.com', 'Apartment 5B, Gulberg III, Lahore'),
    (3, 'Hamza Tariq', '+92-333-4567890', 'hamza.tariq@example.com', 'Plot 18, Block 4, Clifton, Karachi'),
    (4, 'Ayesha Khan', '+92-312-5551234', 'ayesha.khan@example.com', 'Lane 6, DHA Phase 5, Lahore'),
    (5, 'Zainab Fatima', '+92-345-6789012', 'zainab.f@example.com', 'Sector G-10/4, Islamabad');

    INSERT INTO Product (product_id, product_name, category_id, price, description) VALUES
    (1, 'Logitech MX Master 3S Wireless Mouse', 1, 99.99, 'Ergonomic performance wireless mouse with 8K DPI sensor'),
    (2, 'Dell UltraSharp 27" 4K Monitor', 1, 549.00, 'IPS Black technology display with 98% DCI-P3 color gamut'),
    (3, 'Mechanical Gaming Keyboard RGB', 1, 129.50, 'Hot-swappable tactile switches with RGB per-key illumination'),
    (4, 'Active Noise Cancelling Headphones', 1, 249.99, 'Wireless Bluetooth 5.3 headphones with 40-hour battery'),
    (5, 'USB-C Multiport Docking Station', 1, 79.99, '10-in-1 dual HDMI 4K hub with 100W Power Delivery'),
    (6, 'Classic Oxford Cotton Shirt', 2, 45.00, 'Tailored breathable pure cotton business shirt'),
    (7, 'Ergonomic Mesh Office Chair', 3, 299.00, 'Adjustable lumbar support and 3D armrests'),
    (8, 'Smart LED Desk Lamp with Qi Charger', 3, 59.99, 'Dimmable color temperature lamp with wireless phone charging'),
    (9, 'Insulated Stainless Steel Water Bottle', 4, 24.50, 'Vacuum insulated 32oz bottle keeping drinks cold 24hrs'),
    (10, 'Wireless Ergonomic Vertical Mouse', 1, 49.99, 'Reduces wrist strain with natural handshake grip');

    INSERT INTO Inventory (inventory_id, product_id, quantity_available, low_stock_threshold) VALUES
    (1, 1, 45, 10),
    (2, 2, 8, 10),
    (3, 3, 32, 10),
    (4, 4, 5, 8),
    (5, 5, 60, 15),
    (6, 6, 85, 20),
    (7, 7, 6, 8),
    (8, 8, 40, 10),
    (9, 9, 110, 25),
    (10, 10, 3, 10);

    INSERT INTO Sale (sale_id, customer_id, total_amount) VALUES
    (1, 1, 1747.98),
    (2, 2, 1197.98),
    (3, 3, 2146.00),
    (4, 4, 1598.00),
    (5, 5, 1730.04);

    INSERT INTO Sale_Details (sale_detail_id, sale_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 2, 99.99),
    (2, 1, 2, 2, 549.00),
    (3, 2, 4, 2, 249.99),
    (4, 3, 2, 3, 549.00),
    (5, 4, 7, 4, 299.00),
    (6, 5, 10, 8, 49.99);

    INSERT INTO Purchase (purchase_id, supplier_id, total_amount) VALUES
    (1, 1, 4500.00),
    (2, 3, 2400.00);

    INSERT INTO Purchase_Details (purchase_id, product_id, quantity, unit_price) VALUES
    (1, 1, 30, 70.00),
    (1, 2, 4, 380.00),
    (2, 7, 8, 200.00);
    """)
    conn.commit()
    conn.close()
    print("[+] Local preview database initialized with sample records.")

if __name__ == "__main__":
    success = False
    if Config.DB_ENGINE == "postgresql":
        success = setup_postgresql()
    
    if not success:
        print("\n[*] Initializing local database so the application can be tested immediately...")
        setup_sqlite()
