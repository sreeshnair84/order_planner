"""
Add status column to email_communications table

This migration adds the missing status column to the email_communications table
to track email sending status (pending, sent, failed, etc.)
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.connection import engine

async def add_status_column():
    """Add status column to email_communications table"""
    
    try:
        async with engine.begin() as conn:
            # Check if column already exists
            check_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'email_communications' 
            AND column_name = 'status'
            """
            
            result = await conn.execute(text(check_sql))
            exists = result.fetchone()
            
            if not exists:
                print("Adding status column to email_communications table...")
                
                # Add the status column
                alter_sql = """
                ALTER TABLE email_communications 
                ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'pending'
                """
                
                await conn.execute(text(alter_sql))
                print("✅ Status column added successfully")
                
                # Update existing records to have pending status
                update_sql = """
                UPDATE email_communications 
                SET status = 'pending' 
                WHERE status IS NULL
                """
                
                await conn.execute(text(update_sql))
                print("✅ Existing records updated")
            else:
                print("✅ Status column already exists")
                
    except Exception as e:
        print(f"❌ Error adding status column: {str(e)}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("Running email_communications status column migration...")
    asyncio.run(add_status_column())
    print("Migration completed!")
