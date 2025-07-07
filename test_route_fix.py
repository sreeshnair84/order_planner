#!/usr/bin/env python3
"""
Test script to verify the route API fix for SQLAlchemy async issues.
"""

import requests
import json

def test_routes_api():
    """Test the routes API endpoint to verify it works without async issues."""
    base_url = "http://localhost:8000"
    
    # First, try to get an auth token (you might need to adjust this)
    # For now, we'll just test the endpoint directly
    
    try:
        # Test the routes endpoint
        response = requests.get(f"{base_url}/api/management/routes")
        
        if response.status_code == 200:
            print("✅ Routes API is working successfully!")
            data = response.json()
            print(f"   - Total routes: {data.get('total', 0)}")
            print(f"   - Routes returned: {len(data.get('routes', []))}")
            
            # Print first route for debugging
            routes = data.get('routes', [])
            if routes:
                first_route = routes[0]
                print(f"   - First route: {first_route.get('name', 'Unknown')}")
                print(f"   - Manufacturer: {first_route.get('manufacturer', {}).get('name', 'Unknown')}")
                print(f"   - Retailer count: {len(first_route.get('manufacturer', {}).get('retailers', []))}")
        else:
            print(f"❌ Routes API failed with status {response.status_code}")
            print(f"   Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API. Make sure the backend is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error testing routes API: {e}")

if __name__ == "__main__":
    print("Testing Routes API fix...")
    test_routes_api()
