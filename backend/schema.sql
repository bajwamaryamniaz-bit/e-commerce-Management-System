-- ====================================================================
-- E-COMMERCE MANAGEMENT SYSTEM (DBMS PROJECT)
-- Database: PostgreSQL
-- Blueprint Compliant: Relational Schema, 3NF Normalization & Integrity
-- ====================================================================

-- 1. Drop tables if they already exist (in reverse dependency order)
DROP VIEW IF EXISTS view_low_stock CASCADE;
DROP VIEW IF EXISTS view_sales_summary CASCADE;
DROP VIEW IF EXISTS view_product_inventory CASCADE;

DROP TABLE IF EXISTS Sale_Details CASCADE;
DROP TABLE IF EXISTS Sale CASCADE;
DROP TABLE IF EXISTS Purchase_Details CASCADE;
DROP TABLE IF EXISTS Purchase CASCADE;
DROP TABLE IF EXISTS Inventory CASCADE;
DROP TABLE IF EXISTS Product CASCADE;
DROP TABLE IF EXISTS Supplier CASCADE;
DROP TABLE IF EXISTS Category CASCADE;
DROP TABLE IF EXISTS Customer CASCADE;
DROP TABLE IF EXISTS Users CASCADE;

-- ====================================================================
-- 2. USERS TABLE (Admin & Staff Authentication)
-- ====================================================================
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'admin' CHECK (role IN ('admin', 'staff', 'manager')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- 3. CUSTOMER TABLE
-- Stores customer personal & contact information.
-- ====================================================================
CREATE TABLE Customer (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    phone VARCHAR(25),
    email VARCHAR(150) UNIQUE,
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- 4. CATEGORY TABLE
-- Organizes products into unique categories.
-- ====================================================================
CREATE TABLE Category (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- 5. SUPPLIER TABLE
-- Maintains vendor & supplier records for wholesale purchases.
-- ====================================================================
CREATE TABLE Supplier (
    supplier_id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(150) NOT NULL,
    phone VARCHAR(25),
    email VARCHAR(150),
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- 6. PRODUCT TABLE
-- Stores product specifications, unit selling price, and category link.
-- ====================================================================
CREATE TABLE Product (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    category_id INT REFERENCES Category(category_id) ON UPDATE CASCADE ON DELETE SET NULL,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- 7. INVENTORY TABLE
-- Real-time stock tracking for each product (1-to-1 relationship with Product).
-- ====================================================================
CREATE TABLE Inventory (
    inventory_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL UNIQUE REFERENCES Product(product_id) ON UPDATE CASCADE ON DELETE CASCADE,
    quantity_available INT NOT NULL DEFAULT 0 CHECK (quantity_available >= 0),
    low_stock_threshold INT NOT NULL DEFAULT 10 CHECK (low_stock_threshold >= 0),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- 8. PURCHASE TABLE (Header)
-- Records incoming procurement orders from suppliers.
-- ====================================================================
CREATE TABLE Purchase (
    purchase_id SERIAL PRIMARY KEY,
    supplier_id INT NOT NULL REFERENCES Supplier(supplier_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    purchase_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (total_amount >= 0)
);

-- ====================================================================
-- 9. PURCHASE_DETAILS TABLE (Line Items)
-- Detailed breakdown of items, quantities, and purchase prices in a purchase.
-- ====================================================================
CREATE TABLE Purchase_Details (
    purchase_detail_id SERIAL PRIMARY KEY,
    purchase_id INT NOT NULL REFERENCES Purchase(purchase_id) ON UPDATE CASCADE ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES Product(product_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    subtotal NUMERIC(12, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED
);

-- ====================================================================
-- 10. SALE TABLE (Header)
-- Records outbound customer sales transactions.
-- ====================================================================
CREATE TABLE Sale (
    sale_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES Customer(customer_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    sale_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (total_amount >= 0)
);

-- ====================================================================
-- 11. SALE_DETAILS TABLE (Line Items)
-- Detailed breakdown of products sold, quantities, and actual selling price.
-- ====================================================================
CREATE TABLE Sale_Details (
    sale_detail_id SERIAL PRIMARY KEY,
    sale_id INT NOT NULL REFERENCES Sale(sale_id) ON UPDATE CASCADE ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES Product(product_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    subtotal NUMERIC(12, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED
);

-- ====================================================================
-- 12. PERFORMANCE INDEXES
-- Optimizes query execution time for joins, filters, and searches.
-- ====================================================================
CREATE INDEX idx_product_category ON Product(category_id);
CREATE INDEX idx_inventory_product ON Inventory(product_id);
CREATE INDEX idx_purchase_supplier ON Purchase(supplier_id);
CREATE INDEX idx_purchase_details_purchase ON Purchase_Details(purchase_id);
CREATE INDEX idx_purchase_details_product ON Purchase_Details(product_id);
CREATE INDEX idx_sale_customer ON Sale(customer_id);
CREATE INDEX idx_sale_details_sale ON Sale_Details(sale_id);
CREATE INDEX idx_sale_details_product ON Sale_Details(product_id);
CREATE INDEX idx_customer_email ON Customer(email);

-- ====================================================================
-- 13. ANALYTICAL VIEWS FOR REPORTING & DASHBOARDS
-- ====================================================================

-- View 1: Complete Product Inventory Details
CREATE OR REPLACE VIEW view_product_inventory AS
SELECT 
    p.product_id,
    p.product_name,
    c.category_name,
    p.price,
    COALESCE(i.quantity_available, 0) AS stock_quantity,
    COALESCE(i.low_stock_threshold, 10) AS low_stock_threshold,
    CASE 
        WHEN COALESCE(i.quantity_available, 0) <= 0 THEN 'Out of Stock'
        WHEN COALESCE(i.quantity_available, 0) <= COALESCE(i.low_stock_threshold, 10) THEN 'Low Stock'
        ELSE 'In Stock'
    END AS stock_status,
    i.last_updated
FROM Product p
LEFT JOIN Category c ON p.category_id = c.category_id
LEFT JOIN Inventory i ON p.product_id = i.product_id;

-- View 2: Low Stock Alert View
CREATE OR REPLACE VIEW view_low_stock AS
SELECT * 
FROM view_product_inventory
WHERE stock_quantity <= low_stock_threshold;

-- View 3: Sales Performance Summary View
CREATE OR REPLACE VIEW view_sales_summary AS
SELECT 
    s.sale_id,
    s.sale_date,
    c.name AS customer_name,
    s.total_amount,
    COUNT(sd.sale_detail_id) AS total_items_sold
FROM Sale s
JOIN Customer c ON s.customer_id = c.customer_id
LEFT JOIN Sale_Details sd ON s.sale_id = sd.sale_id
GROUP BY s.sale_id, s.sale_date, c.name, s.total_amount;
