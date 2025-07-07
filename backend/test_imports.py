#!/usr/bin/env python3
"""Test to check if the FastAPI app can be imported and started"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    print("Testing imports...")
    
    # Test basic imports
    from fastapi import FastAPI
    print("✓ FastAPI imported")
    
    from app.utils.config import settings
    print("✓ Settings imported")
    
    from app.database.connection import Base, get_db
    print("✓ Database connection imported")
    
    # Test model imports
    from app.models.user import User
    print("✓ User model imported")
    
    from app.models.order import Order
    print("✓ Order model imported")
    
    from app.models.tracking import OrderTracking
    print("✓ OrderTracking model imported")
    
    from app.models.schemas import OrderDetailedResponse
    print("✓ Schemas imported")
    
    # Test API imports
    from app.api.auth import router as auth_router
    print("✓ Auth router imported")
    
    from app.api.orders import router as orders_router
    print("✓ Orders router imported")
    
    # Test main app creation
    from app.main import app
    print("✓ Main app imported")
    
    # Test OrderResponse creation
    from app.api.orders import OrderResponse
    print("✓ OrderResponse imported")
    
    print("✓ All imports successful")
    
except Exception as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("✓ App initialization test passed")
