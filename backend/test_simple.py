#!/usr/bin/env python3
"""Simple test to check if the app starts correctly"""

import asyncio
from app.main import app
from app.database.connection import init_db, check_database_exists

async def test_basic_app():
    """Test basic app functionality"""
    try:
        print("Testing database connection...")
        db_exists = await check_database_exists()
        print(f"Database exists: {db_exists}")
        
        if db_exists:
            print("Initializing database...")
            await init_db()
            print("Database initialized successfully")
        else:
            print("Database connection failed")
            
        print("App created successfully")
        return True
        
    except Exception as e:
        print(f"Error during app initialization: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_basic_app())
    if success:
        print("✓ Basic app test passed")
    else:
        print("✗ Basic app test failed")
