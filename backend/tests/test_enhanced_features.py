#!/usr/bin/env python3
"""
Tests for enhanced order management system features
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import OrderCreate, OrderSKUItemCreate, OrderStatus

client = TestClient(app)

# Test data
@pytest.fixture
def auth_headers():
    """Get authentication headers for tests"""
    # Register a test user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "company_name": "Test Company",
        "contact_person": "John Doe",
        "phone": "1234567890"
    }
    
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 200
    
    # Login to get token
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_order_data():
    """Sample order data for testing"""
    return {
        "order_id": "ORD-2024-001",
        "customer_id": "CUST-001",
        "customer_name": "ABC Retail Store",
        "customer_email": "orders@abcretail.com",
        "order_date": "2024-01-15T10:30:00Z",
        "status": "PENDING",
        "priority": "HIGH",
        "special_instructions": "Handle with care - fragile items",
        "requested_delivery_date": "2024-01-20T14:00:00Z",
        "delivery_address": {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "postal_code": "12345",
            "country": "USA"
        },
        "retailer_info": {
            "store_type": "Supermarket",
            "chain": "ABC Retail",
            "location_id": "LOC-001"
        }
    }

@pytest.fixture
def sample_sku_data():
    """Sample SKU data for testing"""
    return [
        {
            "sku_code": "SKU-001",
            "product_name": "Premium Coffee Beans",
            "category": "Beverages",
            "brand": "CoffeeCorp",
            "quantity_ordered": 50,
            "unit_of_measure": "bags",
            "unit_price": 12.99,
            "weight_kg": 0.5,
            "volume_m3": 0.001,
            "temperature_requirement": "AMBIENT",
            "fragile": False,
            "product_attributes": {
                "organic": True,
                "fair_trade": True
            }
        },
        {
            "sku_code": "SKU-002",
            "product_name": "Glass Bottles",
            "category": "Containers",
            "brand": "GlassCorp",
            "quantity_ordered": 100,
            "unit_of_measure": "units",
            "unit_price": 2.50,
            "weight_kg": 0.3,
            "volume_m3": 0.0005,
            "temperature_requirement": "AMBIENT",
            "fragile": True,
            "product_attributes": {
                "recyclable": True,
                "color": "clear"
            }
        }
    ]

def test_create_order_with_enhanced_features(auth_headers, sample_order_data):
    """Test creating an order with enhanced features"""
    response = client.post("/api/orders/", json=sample_order_data, headers=auth_headers)
    assert response.status_code == 200
    
    order = response.json()
    assert order["order_id"] == sample_order_data["order_id"]
    assert order["priority"] == sample_order_data["priority"]
    assert order["special_instructions"] == sample_order_data["special_instructions"]
    assert order["delivery_address"] == sample_order_data["delivery_address"]
    assert order["retailer_info"] == sample_order_data["retailer_info"]

def test_add_sku_items_to_order(auth_headers, sample_order_data, sample_sku_data):
    """Test adding SKU items to an order"""
    # First create an order
    order_response = client.post("/api/orders/", json=sample_order_data, headers=auth_headers)
    assert order_response.status_code == 200
    order_id = order_response.json()["id"]
    
    # Add SKU items
    for sku_data in sample_sku_data:
        sku_response = client.post(f"/api/orders/{order_id}/skus", json=sku_data, headers=auth_headers)
        assert sku_response.status_code == 200
        
        sku_item = sku_response.json()
        assert sku_item["sku_code"] == sku_data["sku_code"]
        assert sku_item["product_name"] == sku_data["product_name"]
        assert sku_item["quantity_ordered"] == sku_data["quantity_ordered"]

def test_get_order_details(auth_headers, sample_order_data, sample_sku_data):
    """Test getting detailed order information"""
    # Create order with SKU items
    order_response = client.post("/api/orders/", json=sample_order_data, headers=auth_headers)
    order_id = order_response.json()["id"]
    
    # Add SKU items
    for sku_data in sample_sku_data:
        client.post(f"/api/orders/{order_id}/skus", json=sku_data, headers=auth_headers)
    
    # Get detailed order info
    response = client.get(f"/api/orders/{order_id}/details", headers=auth_headers)
    assert response.status_code == 200
    
    order_details = response.json()
    assert "sku_items" in order_details
    assert len(order_details["sku_items"]) == len(sample_sku_data)
    assert "summary" in order_details
    assert order_details["summary"]["total_sku_count"] == len(sample_sku_data)

def test_status_transitions(auth_headers, sample_order_data):
    """Test order status transitions"""
    # Create order
    order_response = client.post("/api/orders/", json=sample_order_data, headers=auth_headers)
    order_id = order_response.json()["id"]
    
    # Test valid status transitions
    valid_transitions = [
        ("PENDING", "PROCESSING"),
        ("PROCESSING", "PICKED"),
        ("PICKED", "PACKED"),
        ("PACKED", "READY_FOR_DISPATCH"),
        ("READY_FOR_DISPATCH", "DISPATCHED"),
        ("DISPATCHED", "IN_TRANSIT"),
        ("IN_TRANSIT", "DELIVERED")
    ]
    
    for from_status, to_status in valid_transitions:
        response = client.put(
            f"/api/tracking/{order_id}/status",
            json={"status": to_status, "notes": f"Transition from {from_status} to {to_status}"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == to_status

def test_invalid_status_transition(auth_headers, sample_order_data):
    """Test invalid status transitions are rejected"""
    # Create order
    order_response = client.post("/api/orders/", json=sample_order_data, headers=auth_headers)
    order_id = order_response.json()["id"]
    
    # Try invalid transition (PENDING -> DELIVERED)
    response = client.put(
        f"/api/tracking/{order_id}/status",
        json={"status": "DELIVERED", "notes": "Invalid direct transition"},
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "Invalid status transition" in response.json()["detail"]

def test_trip_info_management(auth_headers, sample_order_data):
    """Test trip information management"""
    # Create order
    order_response = client.post("/api/orders/", json=sample_order_data, headers=auth_headers)
    order_id = order_response.json()["id"]
    
    # Add trip info
    trip_data = {
        "trip_id": "TRIP-001",
        "vehicle_number": "VH-123",
        "driver_name": "John Driver",
        "driver_phone": "555-0123",
        "estimated_delivery": "2024-01-20T14:00:00Z"
    }
    
    response = client.put(f"/api/orders/{order_id}/trip", json=trip_data, headers=auth_headers)
    assert response.status_code == 200
    
    trip_info = response.json()
    assert trip_info["trip_id"] == trip_data["trip_id"]
    assert trip_info["vehicle_number"] == trip_data["vehicle_number"]
    assert trip_info["driver_name"] == trip_data["driver_name"]

def test_order_rescheduling(auth_headers, sample_order_data):
    """Test order rescheduling functionality"""
    # Create order
    order_response = client.post("/api/orders/", json=sample_order_data, headers=auth_headers)
    order_id = order_response.json()["id"]
    
    # Reschedule order
    reschedule_data = {
        "new_delivery_date": "2024-01-25T10:00:00Z",
        "reason": "Customer requested change"
    }
    
    response = client.put(f"/api/orders/{order_id}/reschedule", json=reschedule_data, headers=auth_headers)
    assert response.status_code == 200
    
    updated_order = response.json()
    assert updated_order["requested_delivery_date"] == reschedule_data["new_delivery_date"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
