"""
South India FMCG Data Viewer
============================

This script displays all retailers and manufacturers created in the database in a readable format.
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

async def view_all_data():
    """Display all retailers, manufacturers, and routes in a readable format"""
    try:
        async with AsyncSessionLocal() as session:
            print("🔍 SOUTH INDIA FMCG DATABASE CONTENTS")
            print("=" * 60)
            
            # Display all retailers grouped by state
            print("\n🏪 ALL RETAILERS (19 Total)")
            print("-" * 40)
            
            result = await session.execute(text("""
                SELECT code, name, city, state, notes
                FROM retailers 
                ORDER BY state, city, code
            """))
            
            current_state = ""
            for row in result:
                if row.state != current_state:
                    current_state = row.state
                    print(f"\n📍 {current_state}:")
                
                business_type = row.notes.split(", ")[0].replace("Business Type: ", "") if row.notes else "Unknown"
                category = row.notes.split(", ")[1].replace("Category: ", "") if row.notes and ", " in row.notes else "Unknown"
                print(f"   • {row.code}: {row.name}")
                print(f"     📍 {row.city}, {row.state}")
                print(f"     🏷️  {business_type} | {category}")
            
            # Display all manufacturers  
            print("\n\n🏭 ALL MANUFACTURERS (8 Total)")
            print("-" * 40)
            
            result = await session.execute(text("""
                SELECT code, name, city, state, notes
                FROM manufacturers 
                ORDER BY state, city, code
            """))
            
            current_state = ""
            for row in result:
                if row.state != current_state:
                    current_state = row.state
                    print(f"\n📍 {current_state}:")
                
                specialization = row.notes.replace("Specializes in: ", "") if row.notes else "Unknown"
                print(f"   • {row.code}: {row.name}")
                print(f"     📍 {row.city}, {row.state}")
                print(f"     🏷️  {specialization}")
            
            # Display route summary
            print("\n\n🚛 ROUTE SUMMARY (15 Total)")
            print("-" * 40)
            
            result = await session.execute(text("""
                SELECT r.name, r.origin_city, r.destination_city, r.distance_km, 
                       m.name as manufacturer_name, r.notes
                FROM routes r
                JOIN manufacturers m ON r.manufacturer_id = m.id
                ORDER BY r.distance_km
            """))
            
            for row in result:
                vehicle_type = ""
                frequency = ""
                retailers = ""
                
                if row.notes:
                    parts = row.notes.split(", ")
                    for part in parts:
                        if part.startswith("Vehicle: "):
                            vehicle_type = part.replace("Vehicle: ", "")
                        elif part.startswith("Frequency: "):
                            frequency = part.replace("Frequency: ", "")
                        elif part.startswith("Retailers: "):
                            retailers = part.replace("Retailers: ", "")
                
                print(f"   • {row.name} ({row.distance_km}km)")
                print(f"     🚛 {vehicle_type} | 📅 {frequency}")
                print(f"     🏭 From: {row.manufacturer_name} ({row.origin_city})")
                print(f"     🏪 Retailers: {retailers}")
                print()
            
            # Display associations summary
            print("\n🔗 RETAILER-MANUFACTURER ASSOCIATIONS")
            print("-" * 40)
            
            result = await session.execute(text("""
                SELECT m.code as mfg_code, m.name as mfg_name, 
                       COUNT(rma.retailer_id) as retailer_count
                FROM manufacturers m
                LEFT JOIN retailer_manufacturer_association rma ON m.id = rma.manufacturer_id
                GROUP BY m.id, m.code, m.name
                ORDER BY m.code
            """))
            
            for row in result:
                print(f"   • {row.mfg_code}: {row.mfg_name} → {row.retailer_count} retailers")
            
            # Show detailed associations for each manufacturer
            print("\n📊 DETAILED ASSOCIATIONS")
            print("-" * 40)
            
            result = await session.execute(text("""
                SELECT m.code as mfg_code, m.name as mfg_name,
                       r.code as retailer_code, r.name as retailer_name, r.city, r.state
                FROM manufacturers m
                JOIN retailer_manufacturer_association rma ON m.id = rma.manufacturer_id
                JOIN retailers r ON rma.retailer_id = r.id
                ORDER BY m.code, r.state, r.city
            """))
            
            current_mfg = ""
            for row in result:
                if row.mfg_code != current_mfg:
                    current_mfg = row.mfg_code
                    print(f"\n🏭 {row.mfg_code} - {row.mfg_name}:")
                
                print(f"   └─ {row.retailer_code}: {row.retailer_name} ({row.city}, {row.state})")
            
            print("\n" + "=" * 60)
            print("✨ DATA VIEW COMPLETE!")
            print("✨ All South India FMCG retailers and manufacturers are successfully stored.")
            
    except Exception as e:
        print(f"❌ Error viewing data: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🌟 South India FMCG Data Viewer")
    print("🌟 Displaying all retailers, manufacturers, and routes")
    print("-" * 60)
    asyncio.run(view_all_data())
