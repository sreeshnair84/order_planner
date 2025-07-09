#!/usr/bin/env python3
"""
Migration script to add processing_remarks column to order_sku_items table
"""

import psycopg2
import os
import sys
from datetime import datetime

def get_db_config():
    """Get database configuration from environment variables"""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'order_planner'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }

def add_processing_remarks_column():
    """Add processing_remarks column to order_sku_items table"""
    db_config = get_db_config()
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        print(f"[{datetime.now()}] Connected to database")
        
        # Check if column already exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'order_sku_items' 
            AND column_name = 'processing_remarks'
        """)
        
        if cur.fetchone():
            print(f"[{datetime.now()}] Column 'processing_remarks' already exists in order_sku_items table")
            return True
        
        # Add the column
        print(f"[{datetime.now()}] Adding processing_remarks column to order_sku_items table...")
        
        cur.execute("""
            ALTER TABLE order_sku_items 
            ADD COLUMN processing_remarks TEXT
        """)
        
        # Commit the changes
        conn.commit()
        
        print(f"[{datetime.now()}] Successfully added processing_remarks column")
        
        # Verify the column was added
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'order_sku_items' 
            AND column_name = 'processing_remarks'
        """)
        
        result = cur.fetchone()
        if result:
            print(f"[{datetime.now()}] Verification: Column added - {result[0]} ({result[1]}, nullable: {result[2]})")
        else:
            print(f"[{datetime.now()}] ERROR: Column was not found after adding")
            return False
        
        cur.close()
        conn.close()
        
        print(f"[{datetime.now()}] Migration completed successfully")
        return True
        
    except Exception as e:
        print(f"[{datetime.now()}] ERROR: Migration failed - {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """Main migration function"""
    print(f"[{datetime.now()}] Starting migration: Add processing_remarks column to order_sku_items")
    
    # Check if all required environment variables are set
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"[{datetime.now()}] WARNING: Missing environment variables: {', '.join(missing_vars)}")
        print(f"[{datetime.now()}] Using default values where possible")
    
    success = add_processing_remarks_column()
    
    if success:
        print(f"[{datetime.now()}] Migration completed successfully!")
        sys.exit(0)
    else:
        print(f"[{datetime.now()}] Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
