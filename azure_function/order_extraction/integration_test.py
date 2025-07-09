#!/usr/bin/env python3
"""
Integration test script for retailer extraction Azure Functions
"""

import requests
import json
import sys
import uuid
from datetime import datetime

class RetailerExtractionTester:
    def __init__(self, function_base_url):
        """Initialize the tester with Azure Function base URL"""
        self.base_url = function_base_url.rstrip('/')
        
    def test_retailer_extraction(self, order_id):
        """Test retailer extraction for a specific order"""
        print(f"Testing retailer extraction for order: {order_id}")
        
        # Test the dedicated retailer extraction endpoint
        url = f"{self.base_url}/api/extract_retailer_info"
        
        payload = {"order_id": order_id}
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Retailer extraction successful!")
                print(f"Order Number: {result.get('order_number')}")
                
                extraction = result.get('retailer_extraction', {})
                print(f"Retailer Extracted: {extraction.get('retailer_extracted')}")
                print(f"Confidence Score: {extraction.get('confidence_score')}")
                
                if extraction.get('retailer_extracted'):
                    extracted_info = extraction.get('extracted_info', {})
                    print(f"Retailer Name: {extracted_info.get('retailer_name')}")
                    print(f"Contact Email: {extracted_info.get('contact_email')}")
                    
                    delivery = extracted_info.get('delivery_address', {})
                    if delivery:
                        print(f"Delivery City: {delivery.get('city')}")
                        print(f"Delivery State: {delivery.get('state')}")
                
                search = result.get('database_search', {})
                print(f"Database Match Found: {search.get('found')}")
                if search.get('found'):
                    retailer = search.get('retailer', {})
                    print(f"Matched Retailer: {retailer.get('name')} (ID: {retailer.get('id')})")
                    print(f"Search Method: {search.get('search_method')}")
                
                print(f"Message: {result.get('message')}")
                
                return True
            else:
                print(f"❌ Error: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return False
    
    def test_manual_retailer_mapping(self, order_id, retailer_id, delivery_address=None):
        """Test manual retailer mapping"""
        print(f"Testing manual retailer mapping for order: {order_id}")
        
        url = f"{self.base_url}/api/update_retailer_mapping"
        
        payload = {
            "order_id": order_id,
            "retailer_id": retailer_id
        }
        
        if delivery_address:
            payload["delivery_address"] = delivery_address
            
        try:
            response = requests.post(url, json=payload, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Manual retailer mapping successful!")
                print(f"Order Number: {result.get('order_number')}")
                print(f"Assigned Retailer ID: {result.get('retailer_id')}")
                
                retailer_info = result.get('retailer_info')
                if retailer_info:
                    print(f"Retailer Name: {retailer_info.get('name')}")
                    print(f"Retailer Code: {retailer_info.get('code')}")
                
                print(f"Message: {result.get('message')}")
                return True
            else:
                print(f"❌ Error: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return False
    
    def test_health_check(self):
        """Test the health check endpoint"""
        print("Testing health check...")
        
        url = f"{self.base_url}/api/health"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Health check passed!")
                print(f"Status: {result.get('status')}")
                print(f"Azure OpenAI Configured: {result.get('azure_openai_configured')}")
                return True
            else:
                print(f"❌ Health check failed: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Health check request failed: {e}")
            return False

def main():
    """Main test function"""
    if len(sys.argv) < 2:
        print("Usage: python integration_test.py <azure_function_url> [order_id] [retailer_id]")
        print("Example: python integration_test.py https://myapp.azurewebsites.net")
        sys.exit(1)
    
    function_url = sys.argv[1]
    order_id = sys.argv[2] if len(sys.argv) > 2 else None
    retailer_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    tester = RetailerExtractionTester(function_url)
    
    print("=== Retailer Extraction Integration Test ===")
    print(f"Function URL: {function_url}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Test health check first
    if not tester.test_health_check():
        print("❌ Health check failed, aborting tests")
        sys.exit(1)
    
    print()
    
    # Test retailer extraction if order_id provided
    if order_id:
        if not tester.test_retailer_extraction(order_id):
            print("❌ Retailer extraction test failed")
        print()
        
        # Test manual mapping if retailer_id also provided
        if retailer_id:
            sample_address = {
                "street": "123 Test Street",
                "city": "Test City", 
                "state": "TS",
                "postal_code": "12345",
                "country": "USA"
            }
            
            if not tester.test_manual_retailer_mapping(order_id, retailer_id, sample_address):
                print("❌ Manual retailer mapping test failed")
    else:
        print("No order_id provided, skipping extraction tests")
        print("To test extraction: python integration_test.py <url> <order_id>")
        print("To test mapping: python integration_test.py <url> <order_id> <retailer_id>")
    
    print()
    print("=== Integration Test Complete ===")

if __name__ == "__main__":
    main()
