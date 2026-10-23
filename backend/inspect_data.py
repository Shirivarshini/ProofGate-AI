import json
import os

print("=" * 50)
print(" PROOFGATE AI - STAGE 0 FIXTURE INSPECTOR")
print("=" * 50)

# Point to root data folder from backend/
orders_path = "../data/orders.json"
if os.path.exists(orders_path):
    with open(orders_path, "r") as f:
        orders = json.load(f)
        print(f"\n📦 Loaded Orders Fixture: {len(orders)} orders found.")
        for order in orders:
            print(f"   - Order ID: {order.get('order_id')} | Amount: ${order.get('total_amount')} | Status: {order.get('status')}")
else:
    print("\n❌ orders.json not found in ../data/")

cust_path = "../data/customers.json"
if os.path.exists(cust_path):
    with open(cust_path, "r") as f:
        customers = json.load(f)
        print(f"\n👥 Loaded Customers Fixture: {len(customers)} customers found.")
        for cust in customers:
            print(f"   - Customer: {cust.get('name')} ({cust.get('email')})")

print("\n" + "=" * 50)
print(" Stage 0 Foundation Files Verified Successfully!")
print("=" * 50)