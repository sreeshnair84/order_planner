"""
Database Check Script
=====================

This script checks the database to see if the retailers, manufacturers, and routes were created successfully.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from app.models.retailer import Retailer, Manufacturer, Route
    from app.database.connection import AsyncSessionLocal
    from sqlalchemy import text, select
    print("✅ Successfully imported models and database session")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

async def check_database():
    """Check what's in the database"""
    try:
        async with AsyncSessionLocal() as session:
            print("🔍 Checking database contents...")
            
            # Check retailers
            result = await session.execute(text('SELECT COUNT(*) FROM retailers'))
            retailer_count = result.scalar()
            print(f"🏪 Retailers in database: {retailer_count}")
            
            # Check manufacturers  
            result = await session.execute(text('SELECT COUNT(*) FROM manufacturers'))
            manufacturer_count = result.scalar()
            print(f"🏭 Manufacturers in database: {manufacturer_count}")
            
            # Check routes
            result = await session.execute(text('SELECT COUNT(*) FROM routes'))
            route_count = result.scalar()
            print(f"🚛 Routes in database: {route_count}")
            
            # Check associations
            result = await session.execute(text('SELECT COUNT(*) FROM retailer_manufacturer_association'))
            association_count = result.scalar()
            print(f"🔗 Retailer-Manufacturer associations: {association_count}")
            
            print("\n" + "="*50)
            
            # Show some sample retailers
            if retailer_count > 0:
                print("📋 Sample Retailers:")
                result = await session.execute(text("""
                    SELECT code, name, city, state 
                    FROM retailers 
                    ORDER BY code 
                    LIMIT 5
                """))
                for row in result:
                    print(f"   • {row.code}: {row.name} ({row.city}, {row.state})")
            
            # Show some sample manufacturers
            if manufacturer_count > 0:
                print("\n📋 Sample Manufacturers:")
                result = await session.execute(text("""
                    SELECT code, name, city, state 
                    FROM manufacturers 
                    ORDER BY code 
                    LIMIT 5
                """))
                for row in result:
                    print(f"   • {row.code}: {row.name} ({row.city}, {row.state})")
            
            # Show some sample routes
            if route_count > 0:
                print("\n📋 Sample Routes:")
                result = await session.execute(text("""
                    SELECT r.name, r.origin_city, r.destination_city, r.distance_km, m.name as manufacturer_name
                    FROM routes r
                    JOIN manufacturers m ON r.manufacturer_id = m.id
                    ORDER BY r.name 
                    LIMIT 5
                """))
                for row in result:
                    print(f"   • {row.name}: {row.origin_city} → {row.destination_city} ({row.distance_km}km) via {row.manufacturer_name}")
            
            print("\n" + "="*50)
            
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 Database Check Script")
    print("-" * 30)
    asyncio.run(check_database())
