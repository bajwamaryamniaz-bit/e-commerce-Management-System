import os
import re
from datetime import datetime
from ..database import execute_query
from .inventory_service import get_dashboard_summary, get_low_stock_items
from .purchase_service import get_all_purchases
from .sale_service import get_all_sales

# Check for Gemini API key if user wants to plug in live LLM
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_live_db_context():
    """
    Gathers real-time snapshot of the database for the AI assistant.
    """
    summary = get_dashboard_summary()
    low_stock = get_low_stock_items() or []
    
    # Query top selling products
    top_prods_sql = """
    SELECT p.product_name, SUM(sd.quantity) AS units_sold, SUM(sd.quantity * sd.unit_price) AS revenue
    FROM Sale_Details sd
    JOIN Product p ON sd.product_id = p.product_id
    GROUP BY p.product_name
    ORDER BY revenue DESC
    LIMIT 3;
    """
    top_products = execute_query(top_prods_sql, fetch="all") or []

    # Query out of stock products
    out_of_stock_sql = """
    SELECT p.product_name, COALESCE(i.quantity_available, 0) as stock
    FROM Product p
    JOIN Inventory i ON p.product_id = i.product_id
    WHERE COALESCE(i.quantity_available, 0) <= 0;
    """
    out_of_stock = execute_query(out_of_stock_sql, fetch="all") or []

    return {
        "summary": summary,
        "low_stock": low_stock,
        "top_products": top_products,
        "out_of_stock": out_of_stock
    }

def process_ai_query(user_message):
    """
    Processes natural language user requests.
    Hybrid engine:
    1. If GEMINI_API_KEY is provided in .env, calls Google Gemini.
    2. Otherwise, runs 100% locally with built-in DBMS intelligence (NO API key required!).
    """
    msg = user_message.lower().strip()

    # Special handler if user asks about API Key
    if any(k in msg for k in ['api_key', 'api key', 'gemini key', 'key error', 'key chaiye', 'key kahan']):
        return (
            "🔑 **API Key Information**:\n\n"
            "• **Is AI Assistant ko chalane ke liye kisi API_KEY ki zaroorat NAHI hai!**\n"
            "  Yeh bilkul free aur offline aap ke local database se direct connect ho kar kaam karta hai.\n\n"
            "• **Agar aap Google Gemini connect karna chahtay hain (Optional):**\n"
            "  1. `.env` file open karein.\n"
            "  2. Apni key add karein: `GEMINI_API_KEY=AIzaSy...`\n"
            "  3. Server restart karein.\n\n"
            "Bina kisi key ke bhi aap Low Stock, Sales, Top Customers, aur 3NF Normalization jaise tamaam sawalat pooch saktay hain!"
        )

    # If GEMINI_API_KEY is configured in .env, try Google Gemini
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if gemini_key and len(gemini_key) > 10 and not gemini_key.startswith("your_"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            db_ctx = get_live_db_context()
            prompt = f"""
            You are an expert AI Assistant embedded inside an E-Commerce Relational DBMS application.
            Current Live Database Context:
            - Products in catalog: {db_ctx['summary'].get('total_products', 0)}
            - Total Sales: ${db_ctx['summary'].get('total_sales', 0)}
            - Low Stock Items: {len(db_ctx['low_stock'])} items ({[i['product_name'] for i in db_ctx['low_stock']]})
            - Total Customers: {db_ctx['summary'].get('total_customers', 0)}

            User Question: {user_message}
            Provide a helpful, well-formatted response with bullet points and emojis. If asked about DBMS topics (1NF, 2NF, 3NF, ER diagram, ACID transactions), explain accurately for a university DBMS presentation.
            """
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception:
            # Fallback gracefully to built-in rule engine
            pass

    # Built-in standalone engine (Works 100% offline without any API key)
    db_ctx = get_live_db_context()
    summary = db_ctx['summary']
    low_stock = db_ctx['low_stock']
    top_products = db_ctx['top_products']

    # 1. Low stock / Out of stock questions
    if any(k in msg for k in ['low stock', 'out of stock', 'stock', 'inventory', 'reorder', 'kam stock']):
        if not low_stock:
            return "Good news! All products currently have healthy inventory levels above their minimum thresholds."
        
        items_list = "\n".join([f"• **{item['product_name']}**: Current Stock = `{item['quantity_available']}` (Minimum Threshold: {item['low_stock_threshold']})" for item in low_stock])
        return (
            f"⚠️ **Low Stock Alert ({len(low_stock)} Items Require Attention)**:\n\n"
            f"{items_list}\n\n"
            f"💡 **Recommendation**: Please navigate to the **Purchases** tab to place a restocking purchase order with your verified suppliers."
        )

    # 2. Sales / Revenue / Financials
    elif any(k in msg for k in ['sale', 'revenue', 'earning', 'kamai', 'total sale', 'money', 'profit', 'dollar']):
        total_sales = summary.get('total_sales', 0.0)
        recent_count = len(summary.get('recent_sales', []))
        top_str = ""
        if top_products:
            top_str = "\n".join([f"• **{p['product_name']}**: ${p['revenue']:,.2f} ({p['units_sold']} units sold)" for p in top_products])
        
        return (
            f"💰 **Financial & Sales Overview**:\n\n"
            f"• **Total Sales Revenue**: `${total_sales:,.2f}`\n"
            f"• **Recent Transactions Recorded**: `{recent_count}`\n\n"
            f"🏆 **Top Revenue Generating Products**:\n"
            f"{top_str}\n\n"
            f"All transaction line items are tracked in the `Sale` and `Sale_Details` relational tables."
        )

    # 3. Customer questions
    elif any(k in msg for k in ['customer', 'client', 'top customer', 'buyer', 'grahak', 'user']):
        cust_sql = """
        SELECT c.name, c.phone, c.email, COUNT(s.sale_id) AS orders, COALESCE(SUM(s.total_amount), 0) AS spent
        FROM Customer c
        LEFT JOIN Sale s ON c.customer_id = s.customer_id
        GROUP BY c.customer_id, c.name, c.phone, c.email
        ORDER BY spent DESC
        LIMIT 3;
        """
        top_custs = execute_query(cust_sql, fetch="all") or []
        cust_list = "\n".join([f"• **{c['name']}** ({c['phone'] or c['email']}): {c['orders']} orders, Total Spent: `${c['spent']:,.2f}`" for c in top_custs])
        
        return (
            f"👥 **Customer Analytics**:\n\n"
            f"Total Registered Customers: `{summary.get('total_customers', 0)}`\n\n"
            f"🌟 **Top Spending Customers**:\n"
            f"{cust_list}\n\n"
            f"Each customer record has a 1-to-many relationship with their respective sales orders."
        )

    # 4. Supplier questions
    elif any(k in msg for k in ['supplier', 'vendor', 'wholesale', 'distributor', 'supply']):
        supp_sql = """
        SELECT s.supplier_name, s.phone, COUNT(p.purchase_id) as purchases, COALESCE(SUM(p.total_amount), 0) as spent
        FROM Supplier s
        LEFT JOIN Purchase p ON s.supplier_id = p.supplier_id
        GROUP BY s.supplier_id, s.supplier_name, s.phone
        ORDER BY spent DESC;
        """
        supps = execute_query(supp_sql, fetch="all") or []
        supp_list = "\n".join([f"• **{s['supplier_name']}**: `{s['purchases']}` purchase orders, Total Spent: `${s['spent']:,.2f}`" for s in supps])
        return (
            f"🚚 **Supplier & Procurement Directory**:\n\n"
            f"{supp_list}\n\n"
            f"Supplier purchases update inventory stock levels automatically upon receipt."
        )

    # 5. DBMS & Viva Questions: 3NF Normalization
    elif any(k in msg for k in ['normalization', '3nf', '2nf', '1nf', 'normal form']):
        return (
            "📐 **DBMS Normalization Architecture (1NF to 3NF)**:\n\n"
            "1. **1NF (First Normal Form)**:\n"
            "   - Every cell contains single, atomic values.\n"
            "   - Repeating groups of purchased/sold items are isolated into separate relational detail tables (`Sale_Details`, `Purchase_Details`).\n\n"
            "2. **2NF (Second Normal Form)**:\n"
            "   - Meets 1NF.\n"
            "   - No partial dependencies on composite primary keys. Attributes depend on the whole primary key.\n\n"
            "3. **3NF (Third Normal Form)**:\n"
            "   - Meets 2NF.\n"
            "   - Eliminates transitive dependencies. For example, product details (name, price) are stored in the `Product` table and referenced by `product_id` foreign keys, preventing duplicate attribute storage."
        )

    # 6. DBMS & Viva Questions: ER Diagram & Relationships
    elif any(k in msg for k in ['er diagram', 'erd', 'relationship', 'foreign key', 'schema', 'tables']):
        return (
            "🗂️ **Database Schema & Relationships (9 Core Tables)**:\n\n"
            "• **Customer 1 : M Sale**: One customer places many sales.\n"
            "• **Sale 1 : M Sale_Details**: One sale contains multiple purchased line items.\n"
            "• **Product 1 : M Sale_Details**: A product can appear across multiple sales.\n"
            "• **Supplier 1 : M Purchase**: One supplier supplies multiple purchase batches.\n"
            "• **Purchase 1 : M Purchase_Details**: Purchase order comprises multiple products.\n"
            "• **Category 1 : M Product**: Categorizes catalog items.\n"
            "• **Product 1 : 1 Inventory**: Strict 1-to-1 tracking of current warehouse stock."
        )

    # 7. DBMS & Viva Questions: Transactions & ACID properties
    elif any(k in msg for k in ['transaction', 'acid', 'consistency', 'rollback', 'commit']):
        return (
            "🛡️ **ACID Transactions Implementation**:\n\n"
            "In this project, critical operations like **Sales Checkout** and **Purchase Restocking** are wrapped inside atomic database transactions (`BEGIN` ... `COMMIT` / `ROLLBACK`):\n\n"
            "• **Pre-validation**: When a sale is initiated, the system queries the `Inventory` table in real-time. If `quantity_available < requested_quantity`, the transaction is aborted.\n"
            "• **Atomicity**: The `Sale` header, `Sale_Details` lines, and `Inventory` deductions either ALL succeed together or none of them are saved."
        )

    # 8. Project Help & General Introduction
    elif any(k in msg for k in ['hello', 'hi', 'hey', 'help', 'salam', 'kya kar sakte ho', 'who are you', 'assistant']):
        return (
            "👋 **Hello! I am your E-Commerce DBMS AI Assistant.**\n\n"
            "I have real-time access to your relational database. Here is what you can ask me:\n\n"
            "• 📦 *'Which products are low on stock?'*\n"
            "• 💰 *'What is our total sales revenue?'*\n"
            "• 👥 *'Who is our top spending customer?'*\n"
            "• 🚚 *'Show supplier procurement statistics'* \n"
            "• 📐 *'Explain 3NF Normalization for this project'*\n"
            "• 🗂️ *'Explain the ER Diagram and relationships'*\n"
            "• 🛡️ *'How do ACID transactions prevent duplicate or negative stock?'*"
        )

    # Default fallback with helpful query options
    else:
        return (
            f"🤖 I analyzed your query: *\"{user_message}\"*\n\n"
            f"Here is your current live store status:\n"
            f"• **Products**: `{summary.get('total_products', 0)}` items in catalog\n"
            f"• **Total Sales**: `${summary.get('total_sales', 0):,.2f}`\n"
            f"• **Low Stock Items**: `{summary.get('low_stock_count', 0)}` items below threshold\n"
            f"• **Registered Customers**: `{summary.get('total_customers', 0)}`\n\n"
            f"Try asking:\n"
            f"- *'Show low stock items'* \n"
            f"- *'Who are top customers?'*\n"
            f"- *'Explain 3NF normalization'* \n"
            f"- *'How does the sales stock check work?'*"
        )
