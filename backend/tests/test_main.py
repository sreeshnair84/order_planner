import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Order Management System API", "version": "1.0.0"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"

def test_register_user():
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "company_name": "Test Company",
        "contact_person": "John Doe",
        "phone": "1234567890"
    }
    
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["email"] == user_data["email"]

def test_login():
    # First register a user
    user_data = {
        "email": "login@example.com",
        "password": "testpassword123",
        "company_name": "Test Company"
    }
    client.post("/api/auth/register", json=user_data)
    
    # Then try to login
    login_data = {
        "email": "login@example.com",
        "password": "testpassword123"
    }
    
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()
    assert response.json()["token_type"] == "bearer"
