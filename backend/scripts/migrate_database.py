#!/usr/bin/env python3
"""
Database migration script to update existing order_management database
with new schema changes for enhanced order management system.
"""
import asyncio
import asyncpg
import sys
import os
from app.utils.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Migration SQL statements
MIGRATION_SCRIPTS = [
    # Add new columns to orders table
    """
    ALTER TABLE orders ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'NORMAL';
    ALTER TABLE orders ADD COLUMN IF NOT EXISTS special_instructions TEXT;
    ALTER TABLE orders ADD COLUMN IF NOT EXISTS requested_delivery_date TIMESTAMP WITH TIME ZONE;
    ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_address JSONB;
    ALTER TABLE orders ADD COLUMN IF NOT EXISTS retailer_info JSONB;
    ALTER TABLE orders ADD COLUMN IF NOT EXISTS total_sku_count INTEGER DEFAULT 0;
    ALTER TABLE orders ADD COLUMN IF NOT EXISTS total_quantity INTEGER DEFAULT 0;
    ALTER TABLE orders ADD COLUMN IF NOT EXISTS total_weight_kg DECIMAL(10,2) DEFAULT 0;
    ALTER TABLE orders ADD COLUMN IF NOT EXISTS total_volume_m3 DECIMAL(10,2) DEFAULT 0;
    ALTER TABLE orders ADD COLUMN IF NOT EXISTS subtotal DECIMAL(10,2) DEFAULT 0;
    ALTER TABLE orders ADD COLUMN IF NOT EXISTS tax DECIMAL(10,2) DEFAULT 0;
    ALTER TABLE orders ADD COLUMN IF NOT EXISTS total DECIMAL(10,2) DEFAULT 0;
    ALTER TABLE orders ADD COLUMN IF NOT EXISTS trip_id VARCHAR(100);
    ALTER TABLE orders ADD COLUMN IF NOT EXISTS trip_status VARCHAR(50);
    ALTER TABLE orders ADD COLUMN IF NOT EXISTS estimated_delivery_date TIMESTAMP WITH TIME ZONE;
    """,
    
    # Create order_sku_items table
    """
    CREATE TABLE IF NOT EXISTS order_sku_items (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
        sku_code VARCHAR(100) NOT NULL,
        product_name VARCHAR(255) NOT NULL,
        category VARCHAR(100),
        brand VARCHAR(100),
        quantity_ordered INTEGER NOT NULL,
        unit_of_measure VARCHAR(50),
        unit_price DECIMAL(10,2),
        total_price DECIMAL(10,2),
        weight_kg DECIMAL(10,2),
        volume_m3 DECIMAL(10,2),
        temperature_requirement VARCHAR(50),
        fragile BOOLEAN DEFAULT FALSE,
        product_attributes JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """,
    
    # Create indexes for order_sku_items
    """
    CREATE INDEX IF NOT EXISTS idx_order_sku_items_order_id ON order_sku_items(order_id);
    CREATE INDEX IF NOT EXISTS idx_order_sku_items_sku_code ON order_sku_items(sku_code);
    """,
    
    # Add sender column to email_communications if it doesn't exist
    """
    ALTER TABLE email_communications ADD COLUMN IF NOT EXISTS sender VARCHAR(255);
    """,
    
    # Create function to update updated_at timestamp
    """
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """,
    
    # Create triggers for updated_at columns
    """
    DROP TRIGGER IF EXISTS update_orders_updated_at ON orders;
    CREATE TRIGGER update_orders_updated_at
        BEFORE UPDATE ON orders
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_order_sku_items_updated_at ON order_sku_items;
    CREATE TRIGGER update_order_sku_items_updated_at
        BEFORE UPDATE ON order_sku_items
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """
]

async def run_migration():
    """Run database migration"""
    try:
        # Parse the database URL
        db_url = settings.DATABASE_URL
        
        # Extract connection parameters
        parts = db_url.replace('postgresql://', '').split('/')
        connection_part = parts[0]
        database = parts[1] if len(parts) > 1 else 'order_management'
        
        # Split connection part
        auth_host = connection_part.split('@')
        auth_part = auth_host[0]
        host_port = auth_host[1]
        
        # Extract credentials
        username, password = auth_part.split(':')
        host, port = host_port.split(':')
        
        logger.info(f"Connecting to database {database} at {host}:{port}")
        
        # Connect to the database
        conn = await asyncpg.connect(
            host=host,
            port=int(port),
            user=username,
            password=password,
            database=database
        )
        
        logger.info("Connected to database successfully")
        
        # Run migration scripts
        for i, script in enumerate(MIGRATION_SCRIPTS, 1):
            try:
                logger.info(f"Running migration script {i}/{len(MIGRATION_SCRIPTS)}")
                await conn.execute(script)
                logger.info(f"Migration script {i} completed successfully")
            except Exception as e:
                logger.error(f"Error in migration script {i}: {e}")
                # Continue with other scripts
        
        await conn.close()
        logger.info("Database migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

async def verify_migration():
    """Verify that migration was successful"""
    try:
        # Parse the database URL
        db_url = settings.DATABASE_URL
        
        # Extract connection parameters
        parts = db_url.replace('postgresql://', '').split('/')
        connection_part = parts[0]
        database = parts[1] if len(parts) > 1 else 'order_management'
        
        # Split connection part
        auth_host = connection_part.split('@')
        auth_part = auth_host[0]
        host_port = auth_host[1]
        
        # Extract credentials
        username, password = auth_part.split(':')
        host, port = host_port.split(':')
        
        # Connect to the database
        conn = await asyncpg.connect(
            host=host,
            port=int(port),
            user=username,
            password=password,
            database=database
        )
        
        # Check if new table exists
        table_exists = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'order_sku_items')"
        )
        
        if table_exists:
            logger.info("✓ order_sku_items table created successfully")
        else:
            logger.error("✗ order_sku_items table not found")
        
        # Check if new columns exist in orders table
        columns_to_check = [
            'priority', 'special_instructions', 'total_sku_count', 
            'total_quantity', 'trip_id', 'trip_status'
        ]
        
        for column in columns_to_check:
            column_exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'orders' AND column_name = $1
                )
                """, column
            )
            
            if column_exists:
                logger.info(f"✓ Column '{column}' added to orders table")
            else:
                logger.error(f"✗ Column '{column}' not found in orders table")
        
        await conn.close()
        logger.info("Migration verification completed")
        
    except Exception as e:
        logger.error(f"Migration verification failed: {e}")
        raise

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    
    try:
        asyncio.run(run_migration())
        asyncio.run(verify_migration())
        logger.info("Database migration and verification completed successfully!")
    except Exception as e:
        logger.error(f"Migration process failed: {e}")
        sys.exit(1)
