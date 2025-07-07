import requests
import uuid
import time

BASE_URL = "http://localhost:8000"

# Helper to print responses

def print_response(resp):
    print(f"URL: {resp.request.method} {resp.url}")
    print(f"Status: {resp.status_code}")
    try:
        print(resp.json())
    except Exception:
        print(resp.text)
    print("-" * 60)

# 1. Register a user
user_email = f"testuser_{uuid.uuid4().hex[:6]}@example.com"
user_password = "TestPassword123!"
register_data = {
    "email": user_email,
    "password": user_password,
    "company_name": "Test Company",
    "contact_person": "Test User",
    "phone": "1234567890"
}
r = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
print_response(r)

# 2. Login
login_data = {"email": user_email, "password": user_password}
r = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
print_response(r)
token = r.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# 3. Create Retailer
retailer_data = {
    "name": "Retailer A",
    "code": f"RET{uuid.uuid4().hex[:4]}",
    "contact_email": "retailer@example.com",
    "contact_phone": "1112223333",
    "address": "123 Main St",
    "city": "CityA",
    "state": "StateA",
    "zip_code": "12345",
    "country": "CountryA",
    "notes": "Test retailer",
    "manufacturer_ids": []
}
r = requests.post(f"{BASE_URL}/api/management/retailers", json=retailer_data, headers=headers)
print_response(r)
retailer_id = r.json().get("id") or r.json().get("retailer", {}).get("id")

# 4. Create Manufacturer
manufacturer_data = {
    "name": "Manufacturer A",
    "code": f"MAN{uuid.uuid4().hex[:4]}",
    "contact_email": "manufacturer@example.com",
    "contact_phone": "4445556666",
    "address": "456 Factory Rd",
    "city": "CityB",
    "state": "StateB",
    "zip_code": "67890",
    "country": "CountryB",
    "notes": "Test manufacturer",
    "lead_time_days": 5,
    "min_order_value": 1000,
    "preferred_payment_terms": "Net 30"
}
r = requests.post(f"{BASE_URL}/api/management/manufacturers", json=manufacturer_data, headers=headers)
print_response(r)
manufacturer_id = r.json().get("id") or r.json().get("manufacturer", {}).get("id")

# 5. Create Route
route_data = {
    "name": "Route 1",
    "manufacturer_id": manufacturer_id,
    "origin_city": "CityB",
    "origin_state": "StateB",
    "origin_country": "CountryB",
    "destination_city": "CityA",
    "destination_state": "StateA",
    "destination_country": "CountryA",
    "distance_km": 100,
    "estimated_transit_days": 2,
    "transport_mode": "truck",
    "cost_per_km": 10,
    "max_weight_kg": 10000,
    "max_volume_m3": 100,
    "is_active": True,
    "notes": "Test route"
}
r = requests.post(f"{BASE_URL}/api/management/routes", json=route_data, headers=headers)
print_response(r)
route_id = r.json().get("id") or r.json().get("route", {}).get("id")

# 6. Upload Order (with dummy file)
with open("dummy_order.txt", "w") as f:
    f.write("SKU,Qty\nSKU1,10\nSKU2,20\n")
with open("dummy_order.txt", "rb") as f:
    files = {"file": ("dummy_order.txt", f, "text/plain")}
    data = {"priority": "NORMAL", "special_instructions": "Test order"}
    r = requests.post(f"{BASE_URL}/api/orders/upload", files=files, data=data, headers=headers)
    print_response(r)
    order_id = r.json().get("id") or r.json().get("order", {}).get("id")

# 7. Get Orders
r = requests.get(f"{BASE_URL}/api/orders", headers=headers)
print_response(r)

# 8. Get Order Details
if order_id:
    r = requests.get(f"{BASE_URL}/api/orders/{order_id}", headers=headers)
    print_response(r)

# 9. Trigger Order Processing
if order_id:
    r = requests.post(f"{BASE_URL}/api/email/orders/{order_id}/trigger-processing", headers=headers)
    print_response(r)
    time.sleep(2)

# 10. Get Order Tracking
if order_id:
    r = requests.get(f"{BASE_URL}/api/orders/{order_id}/tracking", headers=headers)
    print_response(r)

# 11. List Files
r = requests.get(f"{BASE_URL}/api/files", headers=headers)
print_response(r)

# 12. List Emails
r = requests.get(f"{BASE_URL}/api/email/emails", headers=headers)
print_response(r)

# 13. Logistics Optimization (dummy)
logistics_data = {
    "manufacturing_location_ids": [str(uuid.uuid4())],
    "date_range": {"start": "2025-07-01T00:00:00", "end": "2025-07-31T23:59:59"},
    "optimization_scope": "full",
    "business_objectives": ["minimize_cost"],
    "constraints": {}
}
r = requests.post(f"{BASE_URL}/api/logistics/optimize-logistics", json=logistics_data, headers=headers)
print_response(r)

print("API test script completed.")
