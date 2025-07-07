#!/usr/bin/env python3
"""
Script to check and fix database schema issues
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database.connection import engine
from app.utils.config import settings
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_and_fix_schema():
    """Check and fix database schema issues"""
    try:
        # Get database connection
        async with engine.begin() as conn:
            # Check if order_tracking table exists
            table_exists = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'order_tracking'
                )
            """))
            table_exists = table_exists.scalar()
            
            if not table_exists:
                logger.info("order_tracking table doesn't exist, creating it...")
                await conn.execute(text("""
                    CREATE TABLE order_tracking (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        order_id UUID NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        message TEXT,
                        details TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        FOREIGN KEY (order_id) REFERENCES orders(id)
                    )
                """))
                logger.info("order_tracking table created")
            else:
                logger.info("order_tracking table exists")
                
                # Check if timestamp column exists (it shouldn't)
                timestamp_exists = await conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'order_tracking' 
                        AND column_name = 'timestamp'
                    )
                """))
                timestamp_exists = timestamp_exists.scalar()
                
                if timestamp_exists:
                    logger.info("Removing timestamp column from order_tracking table...")
                    await conn.execute(text("ALTER TABLE order_tracking DROP COLUMN IF EXISTS timestamp"))
                    logger.info("timestamp column removed")
                
                # Check if created_at column exists
                created_at_exists = await conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'order_tracking' 
                        AND column_name = 'created_at'
                    )
                """))
                created_at_exists = created_at_exists.scalar()
                
                if not created_at_exists:
                    logger.info("Adding created_at column to order_tracking table...")
                    await conn.execute(text("""
                        ALTER TABLE order_tracking 
                        ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    """))
                    logger.info("created_at column added")
            
            # Check if email_communications table exists  
            table_exists = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'email_communications'
                )
            """))
            table_exists = table_exists.scalar()
            
            if not table_exists:
                logger.info("email_communications table doesn't exist, creating it...")
                await conn.execute(text("""
                    CREATE TABLE email_communications (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        order_id UUID NOT NULL,
                        email_type VARCHAR(50) NOT NULL,
                        recipient VARCHAR(255) NOT NULL,
                        sender VARCHAR(255),
                        subject VARCHAR(255),
                        body TEXT,
                        sent_at TIMESTAMP WITH TIME ZONE,
                        response_received_at TIMESTAMP WITH TIME ZONE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        status VARCHAR(50) NOT NULL DEFAULT 'pending',
                        FOREIGN KEY (order_id) REFERENCES orders(id)
                    )
                """))
                logger.info("email_communications table created")
            else:
                logger.info("email_communications table exists")
                
                # Check for old column names and rename them
                old_columns = ['to_email', 'from_email', 'content']
                new_columns = ['recipient', 'sender', 'body']
                
                for old_col, new_col in zip(old_columns, new_columns):
                    old_exists = await conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'email_communications' 
                            AND column_name = :col_name
                        )
                    """), {"col_name": old_col})
                    old_exists = old_exists.scalar()
                    
                    new_exists = await conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'email_communications' 
                            AND column_name = :col_name
                        )
                    """), {"col_name": new_col})
                    new_exists = new_exists.scalar()
                    
                    if old_exists and not new_exists:
                        logger.info(f"Renaming column {old_col} to {new_col}...")
                        await conn.execute(text(f"""
                            ALTER TABLE email_communications 
                            RENAME COLUMN {old_col} TO {new_col}
                        """))
                        logger.info(f"Column {old_col} renamed to {new_col}")
                    elif not old_exists and not new_exists:
                        # Add the new column if neither exists
                        logger.info(f"Adding column {new_col}...")
                        col_type = "VARCHAR(255)" if new_col != "body" else "TEXT"
                        await conn.execute(text(f"""
                            ALTER TABLE email_communications 
                            ADD COLUMN {new_col} {col_type}
                        """))
                        logger.info(f"Column {new_col} added")
            
            logger.info("Schema check and fix completed successfully")
            
    except Exception as e:
        logger.error(f"Error checking/fixing schema: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(check_and_fix_schema())
