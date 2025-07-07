"""
Migration script to add manufacturer assignment fields to orders table
and create manufacturer-retailer relationships
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.connection import get_engine
import logging

logger = logging.getLogger(__name__)

async def migrate_database():
    """Run database migrations for manufacturer assignment"""
    engine = get_engine()
    
    try:
        async with engine.begin() as conn:
            logger.info("Starting database migration for manufacturer assignment...")
            
            # Add manufacturer assignment fields to orders table
            await conn.execute(text("""
                ALTER TABLE orders 
                ADD COLUMN IF NOT EXISTS retailer_id INTEGER REFERENCES retailers(id),
                ADD COLUMN IF NOT EXISTS manufacturer_id INTEGER REFERENCES manufacturers(id),
                ADD COLUMN IF NOT EXISTS assigned_by UUID REFERENCES users(id),
                ADD COLUMN IF NOT EXISTS assigned_at TIMESTAMP WITH TIME ZONE,
                ADD COLUMN IF NOT EXISTS assignment_notes TEXT
            """))
            
            logger.info("Added manufacturer assignment fields to orders table")
            
            # Create retailer_manufacturer_association table if it doesn't exist
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS retailer_manufacturer_association (
                    retailer_id INTEGER REFERENCES retailers(id) ON DELETE CASCADE,
                    manufacturer_id INTEGER REFERENCES manufacturers(id) ON DELETE CASCADE,
                    PRIMARY KEY (retailer_id, manufacturer_id)
                )
            """))
            
            logger.info("Created retailer_manufacturer_association table")
            
            # Create manufacturers table if it doesn't exist
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS manufacturers (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    contact_email VARCHAR(255) NOT NULL,
                    contact_phone VARCHAR(50),
                    address TEXT,
                    city VARCHAR(100),
                    state VARCHAR(50),
                    zip_code VARCHAR(20),
                    country VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    notes TEXT,
                    lead_time_days INTEGER DEFAULT 7,
                    min_order_value INTEGER DEFAULT 0,
                    preferred_payment_terms VARCHAR(100),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            logger.info("Created manufacturers table")
            
            # Create retailers table if it doesn't exist
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS retailers (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    contact_email VARCHAR(255) NOT NULL,
                    contact_phone VARCHAR(50),
                    address TEXT,
                    city VARCHAR(100),
                    state VARCHAR(50),
                    zip_code VARCHAR(20),
                    country VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    notes TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            logger.info("Created retailers table")
            
            # Create routes table if it doesn't exist
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS routes (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    manufacturer_id INTEGER REFERENCES manufacturers(id) NOT NULL,
                    origin_city VARCHAR(100) NOT NULL,
                    origin_state VARCHAR(50),
                    origin_country VARCHAR(100),
                    destination_city VARCHAR(100) NOT NULL,
                    destination_state VARCHAR(50),
                    destination_country VARCHAR(100),
                    distance_km INTEGER,
                    estimated_transit_days INTEGER DEFAULT 3,
                    transport_mode VARCHAR(50) DEFAULT 'truck',
                    cost_per_km INTEGER DEFAULT 0,
                    max_weight_kg INTEGER,
                    max_volume_m3 INTEGER,
                    is_active BOOLEAN DEFAULT TRUE,
                    notes TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            logger.info("Created routes table")
            
            # Create indexes for performance (separate commands)
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_orders_retailer_id ON orders(retailer_id)",
                "CREATE INDEX IF NOT EXISTS idx_orders_manufacturer_id ON orders(manufacturer_id)",
                "CREATE INDEX IF NOT EXISTS idx_orders_assigned_by ON orders(assigned_by)",
                "CREATE INDEX IF NOT EXISTS idx_manufacturers_code ON manufacturers(code)",
                "CREATE INDEX IF NOT EXISTS idx_retailers_code ON retailers(code)",
                "CREATE INDEX IF NOT EXISTS idx_routes_manufacturer_id ON routes(manufacturer_id)"
            ]
            
            for index_sql in indexes:
                await conn.execute(text(index_sql))
            
            logger.info("Created indexes for performance")
            
            # Insert sample data
            await conn.execute(text("""
                INSERT INTO manufacturers (name, code, contact_email, contact_phone, city, state, country)
                VALUES 
                    ('ABC Manufacturing', 'ABC001', 'contact@abcmfg.com', '+1-555-0101', 'Chicago', 'IL', 'USA'),
                    ('XYZ Production', 'XYZ002', 'info@xyzprod.com', '+1-555-0102', 'Detroit', 'MI', 'USA'),
                    ('Global Suppliers Inc', 'GSI003', 'support@globalsuppliers.com', '+1-555-0103', 'Houston', 'TX', 'USA')
                ON CONFLICT (code) DO NOTHING
            """))
            
            await conn.execute(text("""
                INSERT INTO retailers (name, code, contact_email, contact_phone, city, state, country)
                VALUES 
                    ('Mega Retail Corp', 'MRC001', 'orders@megaretail.com', '+1-555-0201', 'New York', 'NY', 'USA'),
                    ('Quick Mart Chain', 'QMC002', 'purchasing@quickmart.com', '+1-555-0202', 'Los Angeles', 'CA', 'USA'),
                    ('Super Store Network', 'SSN003', 'suppliers@superstore.com', '+1-555-0203', 'Miami', 'FL', 'USA')
                ON CONFLICT (code) DO NOTHING
            """))
            
            logger.info("Inserted sample manufacturer and retailer data")
            
            await conn.commit()
            logger.info("Migration completed successfully!")
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(migrate_database())
