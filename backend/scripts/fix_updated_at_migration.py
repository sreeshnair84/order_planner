#!/usr/bin/env python3
"""
Database migration script to fix updated_at columns
"""

import asyncio
from sqlalchemy import text
from app.database.connection import engine
import logging

logger = logging.getLogger(__name__)

async def fix_updated_at_columns():
    """Fix updated_at columns to have default values"""
    
    migration_queries = [
        # Fix orders table
        """
        ALTER TABLE orders 
        ALTER COLUMN updated_at SET DEFAULT NOW();
        """,
        
        # Fix users table
        """
        ALTER TABLE users 
        ALTER COLUMN updated_at SET DEFAULT NOW();
        """,
        
        # Update existing NULL values
        """
        UPDATE orders 
        SET updated_at = created_at 
        WHERE updated_at IS NULL;
        """,
        
        """
        UPDATE users 
        SET updated_at = created_at 
        WHERE updated_at IS NULL;
        """
    ]
    
    try:
        async with engine.begin() as conn:
            for query in migration_queries:
                logger.info(f"Executing: {query.strip()}")
                await conn.execute(text(query))
        logger.info("Migration completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

async def main():
    await fix_updated_at_columns()

if __name__ == "__main__":
    asyncio.run(main())
