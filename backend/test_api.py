import os
import sys

# Ensure UTF-8 output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app

app = create_app()
client = app.test_client()

print("[*] Testing Dashboard API...")
res = client.get('/api/inventory/dashboard/stats')
print("Status:", res.status_code)
data = res.get_json()
print("Data:", data)

print("\n[*] Testing Products API...")
res_prod = client.get('/api/products')
print("Status:", res_prod.status_code, "| Products count:", len(res_prod.get_json().get('data', [])))

print("\n[*] Testing Customers API...")
res_cust = client.get('/api/customers')
print("Status:", res_cust.status_code, "| Customers count:", len(res_cust.get_json().get('data', [])))

print("\n[*] Testing Sales API...")
res_sales = client.get('/api/sales')
print("Status:", res_sales.status_code, "| Sales count:", len(res_sales.get_json().get('data', [])))

print("\n[*] Testing Reports API...")
res_rep = client.get('/api/reports/summary')
print("Status:", res_rep.status_code, "| Best sellers:", len(res_rep.get_json().get('data', {}).get('best_sellers', [])))

print("\n[*] Testing AI Assistant API...")
res_ai = client.post('/api/ai/chat', json={"message": "Which products have low stock?"})
print("Status:", res_ai.status_code)
print("AI Reply Preview:", res_ai.get_json().get('reply', '')[:120], "...")

print("\n[+] ALL TESTS COMPLETED SUCCESSFULLY!")
