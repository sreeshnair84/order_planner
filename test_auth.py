import requests
import json

# Test the auth endpoints
BASE_URL = "http://localhost:8000"

# Register a test user
register_data = {
    "email": "test@example.com",
    "password": "test123",
    "company_name": "Test Company"
}

print("Testing registration...")
try:
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    print(f"Register response: {response.status_code}")
    print(f"Register content: {response.text}")
except Exception as e:
    print(f"Register error: {e}")

# Login to get token
login_data = {
    "email": "test@example.com",
    "password": "test123"
}

print("\nTesting login...")
try:
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"Login response: {response.status_code}")
    print(f"Login content: {response.text}")
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        # Test the dropdown endpoint
        print("\nTesting dropdown endpoint...")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/api/management/retailers/dropdown", headers=headers)
        print(f"Dropdown response: {response.status_code}")
        print(f"Dropdown content: {response.text}")
        
except Exception as e:
    print(f"Login error: {e}")
