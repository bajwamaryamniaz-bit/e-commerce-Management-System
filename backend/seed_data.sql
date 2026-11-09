-- ====================================================================
-- E-COMMERCE MANAGEMENT SYSTEM - SEED DATA
-- Sample data matching the project mockup & testing needs
-- ====================================================================

-- 1. Insert Default Admin User (Password: admin123)
-- PBKDF2 hash of 'admin123'
INSERT INTO Users (username, email, password_hash, role)
VALUES 
('admin', 'admin@ecommerce.com', 'scrypt:32768:8:1$3chB5gCTFNstaLgi$888ddd725e37306fc629baaf797bf5e4289f3ebfde3a9ec00b7dab976acd1520b12575158030735d73df065e15b9dae8d43ebc664f0bf87c73123ead7395cd89', 'admin'),
('staff1', 'staff@ecommerce.com', 'scrypt:32768:8:1$3chB5gCTFNstaLgi$888ddd725e37306fc629baaf797bf5e4289f3ebfde3a9ec00b7dab976acd1520b12575158030735d73df065e15b9dae8d43ebc664f0bf87c73123ead7395cd89', 'staff')
ON CONFLICT (username) DO NOTHING;

-- 2. Insert Categories
INSERT INTO Category (category_id, category_name, description) VALUES
(1, 'Electronics', 'Smartphones, laptops, monitors, accessories and electronics gadgets'),
(2, 'Apparel & Fashion', 'Men and women casual and formal clothing, sportswear, accessories'),
(3, 'Home & Living', 'Furniture, lighting, kitchen appliances and home decors'),
(4, 'Health & Personal Care', 'Skincare, wellness essentials, vitamins and fitness gear'),
(5, 'Office Supplies', 'Stationery, ergonomic desk equipment, organizers')
ON CONFLICT (category_id) DO NOTHING;
SELECT setval('category_category_id_seq', (SELECT MAX(category_id) FROM Category));

-- 3. Insert Suppliers
INSERT INTO Supplier (supplier_id, supplier_name, phone, email, address) VALUES
(1, 'Global Tech Logistics', '+1-555-019-2831', 'supply@globaltech.com', '742 Evergreen Terrace, Tech Park, CA'),
(2, 'Apex Apparel Wholesale', '+1-555-024-8842', 'orders@apexapparel.com', '124 Fashion Ave, New York, NY'),
(3, 'Nordic Home Living Ltd', '+1-555-037-4491', 'contact@nordichome.com', '88 Design Way, Seattle, WA'),
(4, 'EcoCare Health Distributors', '+1-555-048-9120', 'sales@ecocarehealth.com', '500 Wellness Blvd, Austin, TX')
ON CONFLICT (supplier_id) DO NOTHING;
SELECT setval('supplier_supplier_id_seq', (SELECT MAX(supplier_id) FROM Supplier));

-- 4. Insert Customers
INSERT INTO Customer (customer_id, name, phone, email, address) VALUES
(1, 'Muhammad Ali', '+92-300-1234567', 'ali.muhammad@example.com', 'House 42, Street 8, F-7/2, Islamabad'),
(2, 'Sara Ahmed', '+92-321-9876543', 'sara.ahmed@example.com', 'Apartment 5B, Gulberg III, Lahore'),
(3, 'Hamza Tariq', '+92-333-4567890', 'hamza.tariq@example.com', 'Plot 18, Block 4, Clifton, Karachi'),
(4, 'Ayesha Khan', '+92-312-5551234', 'ayesha.khan@example.com', 'Lane 6, DHA Phase 5, Lahore'),
(5, 'Zainab Fatima', '+92-345-6789012', 'zainab.f@example.com', 'Sector G-10/4, Islamabad')
ON CONFLICT (customer_id) DO NOTHING;
SELECT setval('customer_customer_id_seq', (SELECT MAX(customer_id) FROM Customer));

-- 5. Insert Products
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
(10, 'Wireless Ergonomic Vertical Mouse', 1, 49.99, 'Reduces wrist strain with natural handshake grip')
ON CONFLICT (product_id) DO NOTHING;
SELECT setval('product_product_id_seq', (SELECT MAX(product_id) FROM Product));

-- 6. Insert Inventory (Matching product_id)
INSERT INTO Inventory (inventory_id, product_id, quantity_available, low_stock_threshold) VALUES
(1, 1, 45, 10),
(2, 2, 8, 10),   -- Low stock item (<= 10)
(3, 3, 32, 10),
(4, 4, 5, 8),    -- Low stock item (<= 8)
(5, 5, 60, 15),
(6, 6, 85, 20),
(7, 7, 6, 8),    -- Low stock item (<= 8)
(8, 8, 40, 10),
(9, 9, 110, 25),
(10, 10, 3, 10)  -- Low stock item (<= 10)
ON CONFLICT (inventory_id) DO NOTHING;
SELECT setval('inventory_inventory_id_seq', (SELECT MAX(inventory_id) FROM Inventory));

-- 7. Insert Purchases & Purchase Details
INSERT INTO Purchase (purchase_id, supplier_id, purchase_date, total_amount) VALUES
(1, 1, CURRENT_TIMESTAMP - INTERVAL '15 days', 4500.00),
(2, 3, CURRENT_TIMESTAMP - INTERVAL '8 days', 2400.00)
ON CONFLICT (purchase_id) DO NOTHING;
SELECT setval('purchase_purchase_id_seq', (SELECT MAX(purchase_id) FROM Purchase));

INSERT INTO Purchase_Details (purchase_detail_id, purchase_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 30, 70.00),
(2, 1, 2, 4, 380.00),
(3, 1, 5, 20, 44.00),
(4, 2, 7, 8, 200.00),
(5, 2, 8, 20, 40.00)
ON CONFLICT (purchase_detail_id) DO NOTHING;
SELECT setval('purchase_details_purchase_detail_id_seq', (SELECT MAX(purchase_detail_id) FROM Purchase_Details));

-- 8. Insert Sales & Sale Details (Matching $8,420+ total sales)
INSERT INTO Sale (sale_id, customer_id, sale_date, total_amount) VALUES
(1, 1, CURRENT_TIMESTAMP - INTERVAL '5 days', 1747.98),
(2, 2, CURRENT_TIMESTAMP - INTERVAL '3 days', 1197.98),
(3, 3, CURRENT_TIMESTAMP - INTERVAL '2 days', 2146.00),
(4, 4, CURRENT_TIMESTAMP - INTERVAL '1 day', 1598.00),
(5, 5, CURRENT_TIMESTAMP - INTERVAL '6 hours', 1730.04)
ON CONFLICT (sale_id) DO NOTHING;
SELECT setval('sale_sale_id_seq', (SELECT MAX(sale_id) FROM Sale));

INSERT INTO Sale_Details (sale_detail_id, sale_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 2, 99.99),
(2, 1, 2, 2, 549.00),
(3, 1, 3, 3, 129.50),
(4, 2, 4, 2, 249.99),
(5, 2, 7, 2, 299.00),
(6, 2, 9, 4, 24.50),
(7, 3, 2, 3, 549.00),
(8, 3, 4, 2, 249.99),
(9, 4, 7, 4, 299.00),
(10, 4, 8, 6, 59.99),
(11, 4, 6, 1, 45.00),
(12, 5, 1, 4, 99.99),
(13, 5, 3, 4, 129.50),
(14, 5, 5, 5, 79.99),
(15, 5, 10, 8, 49.99)
ON CONFLICT (sale_detail_id) DO NOTHING;
SELECT setval('sale_details_sale_detail_id_seq', (SELECT MAX(sale_detail_id) FROM Sale_Details));
