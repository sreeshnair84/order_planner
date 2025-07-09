# Test script for retailer information extraction functionality
import json

def test_retailer_extraction():
    """Test the retailer information extraction functionality"""
    
    # Sample order data that might contain retailer information
    sample_order_data = {
        "customer_info": {
            "company": "ABC Retail Store",
            "contact": "John Smith",
            "email": "john@abcretail.com",
            "phone": "+1-555-123-4567"
        },
        "billing_address": {
            "street": "123 Main Street",
            "city": "Springfield",
            "state": "IL",
            "zip": "62701"
        },
        "delivery_address": {
            "street": "456 Oak Avenue",
            "city": "Springfield", 
            "state": "IL",
            "zip": "62702",
            "special_instructions": "Loading dock on north side"
        },
        "items": [
            {
                "sku": "ABC123",
                "description": "Product A",
                "quantity": 100,
                "unit_price": 12.50
            },
            {
                "sku": "DEF456", 
                "description": "Product B",
                "quantity": 50,
                "unit_price": 25.00
            }
        ]
    }
    
    print("Sample Order Data for Retailer Extraction:")
    print(json.dumps(sample_order_data, indent=2))
    
    # Expected retailer info extraction
    expected_retailer_info = {
        "name": "ABC Retail Store",
        "contact_person": "John Smith",
        "email": "john@abcretail.com",
        "phone": "+1-555-123-4567",
        "address": {
            "street": "123 Main Street",
            "city": "Springfield",
            "state": "IL",
            "postal_code": "62701",
            "country": "USA"
        },
        "business_type": "RETAIL"
    }
    
    print("\nExpected Retailer Info Extraction:")
    print(json.dumps(expected_retailer_info, indent=2))
    
    # Expected delivery address extraction
    expected_delivery_address = {
        "street": "456 Oak Avenue",
        "city": "Springfield",
        "state": "IL", 
        "postal_code": "62702",
        "country": "USA",
        "delivery_instructions": "Loading dock on north side",
        "address_type": "BUSINESS"
    }
    
    print("\nExpected Delivery Address Extraction:")
    print(json.dumps(expected_delivery_address, indent=2))
    
    print("\n" + "="*50)
    print("Azure Function Endpoints to Test:")
    print("="*50)
    print("1. Extract Retailer Info:")
    print("   POST /api/extract_retailer_info")
    print("   Body: {'order_id': 'uuid-of-order'}")
    print()
    print("2. Search Retailers:")
    print("   POST /api/search_retailers")
    print("   Body:", json.dumps(expected_retailer_info))
    print()
    print("3. Assign Retailer:")
    print("   POST /api/assign_retailer")
    print("   Body: {'order_id': 'uuid-of-order', 'retailer_id': 123, 'notes': 'Manual assignment'}")
    print()
    
    # Sample API response structures
    print("Expected API Response Structure:")
    print("-"*30)
    
    sample_response = {
        "success": True,
        "order_id": "12345678-1234-1234-1234-123456789012",
        "order_number": "ORD-2025-001",
        "extraction_results": {
            "retailer_info": expected_retailer_info,
            "delivery_address": expected_delivery_address
        },
        "retailer_search": {
            "total_matches": 2,
            "matches": [
                {
                    "retailer_id": 1,
                    "name": "ABC Retail Store",
                    "code": "ABC001",
                    "contact_email": "john@abcretail.com",
                    "confidence_score": 0.95,
                    "match_criteria": ["email_exact", "name_exact"]
                },
                {
                    "retailer_id": 2,
                    "name": "ABC Retail Chain",
                    "code": "ABC002", 
                    "contact_email": "info@abcretailchain.com",
                    "confidence_score": 0.65,
                    "match_criteria": ["name_partial"]
                }
            ],
            "best_match": {
                "retailer_id": 1,
                "name": "ABC Retail Store",
                "confidence_score": 0.95
            }
        },
        "update_result": {
            "success": True,
            "match_status": "matched_high_confidence",
            "retailer_id": 1,
            "processing_note": "Retailer matched with high confidence"
        },
        "recommendations": [
            "High confidence retailer match found and assigned automatically"
        ]
    }
    
    print(json.dumps(sample_response, indent=2))

if __name__ == "__main__":
    test_retailer_extraction()
