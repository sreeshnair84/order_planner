"""
Simple test script to validate the PostgreSQL database schema for order_sku_items table
"""
import psycopg2
from psycopg2 import sql
import os
import sys
import logging

# Add the azure_function/order_extraction directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from db_config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT
except ImportError:
    print("Error: Cannot import database configuration. Make sure db_config.py exists.")
    sys.exit(1)

def test_database_connection():
    """Test database connection and validate order_sku_items table schema"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            sslmode='require'
        )
        
        cur = conn.cursor()
        
        # Check if order_sku_items table exists and get its schema
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'order_sku_items'
            ORDER BY ordinal_position;
        """)
        
        columns = cur.fetchall()
        
        if not columns:
            print("ERROR: order_sku_items table does not exist!")
            return False
        
        print("order_sku_items table schema:")
        print("Column Name | Data Type | Nullable | Default")
        print("-" * 50)
        
        expected_columns = [
            'id', 'order_id', 'sku_code', 'product_name', 'category', 'brand',
            'quantity_ordered', 'unit_of_measure', 'unit_price', 'total_price',
            'weight_kg', 'volume_m3', 'temperature_requirement', 'fragile',
            'product_attributes', 'created_at', 'updated_at'
        ]
        
        actual_columns = []
        for col in columns:
            column_name, data_type, is_nullable, column_default = col
            actual_columns.append(column_name)
            print(f"{column_name} | {data_type} | {is_nullable} | {column_default}")
        
        print("\nExpected columns:", expected_columns)
        print("Actual columns:  ", actual_columns)
        
        missing_columns = set(expected_columns) - set(actual_columns)
        extra_columns = set(actual_columns) - set(expected_columns)
        
        if missing_columns:
            print(f"\nMISSING COLUMNS: {missing_columns}")
        
        if extra_columns:
            print(f"\nEXTRA COLUMNS: {extra_columns}")
        
        if not missing_columns and not extra_columns:
            print("\n✓ Table schema matches expected structure")
        
        # Test a simple insert with dummy data
        print("\nTesting insert operation...")
        
        test_data = {
            'sku_code': 'TEST001',
            'product_name': 'Test Product',
            'category': 'Test Category',
            'brand': 'Test Brand',
            'quantity_ordered': 1,
            'unit_of_measure': 'pieces',
            'unit_price': 10.50,
            'total_price': 10.50,
            'weight_kg': 0.5,
            'volume_m3': 0.01,
            'temperature_requirement': 'ambient',
            'fragile': False,
            'product_attributes': {}
        }
        
        # Generate test IDs
        import uuid
        import json
        test_order_id = str(uuid.uuid4())
        test_item_id = str(uuid.uuid4())
        
        insert_query = sql.SQL("""
            INSERT INTO order_sku_items (
                id, order_id, sku_code, product_name, category, brand,
                quantity_ordered, unit_of_measure, unit_price, total_price,
                weight_kg, volume_m3, temperature_requirement, fragile,
                product_attributes, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
            )
        """)
        
        cur.execute(insert_query, (
            test_item_id,
            test_order_id,
            test_data.get('sku_code', ''),
            test_data.get('product_name', ''),
            test_data.get('category'),
            test_data.get('brand', ''),
            test_data.get('quantity_ordered', 0),
            test_data.get('unit_of_measure'),
            test_data.get('unit_price'),
            test_data.get('total_price'),
            test_data.get('weight_kg'),
            test_data.get('volume_m3'),
            test_data.get('temperature_requirement'),
            test_data.get('fragile', False),
            json.dumps(test_data.get('product_attributes', {})),
        ))
        
        print("✓ Insert test successful")
        
        # Clean up test data
        cur.execute("DELETE FROM order_sku_items WHERE id = %s", (test_item_id,))
        conn.commit()
        print("✓ Test data cleaned up")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Database test failed: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = test_database_connection()
    if success:
        print("\n✓ Database validation completed successfully")
    else:
        print("\n✗ Database validation failed")
        sys.exit(1)
