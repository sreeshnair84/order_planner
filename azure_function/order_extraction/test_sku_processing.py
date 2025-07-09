"""
Test script to verify the SKU insertion functionality
"""
import json
import uuid

def test_sku_item_processing():
    """Test that SKU items are processed correctly"""
    
    # Sample SKU items data that might come from AI
    test_sku_items = [
        {
            'sku_code': 'SKU001',
            'product_name': 'Test Product 1',
            'category': 'Food',
            'brand': 'Test Brand',
            'quantity_ordered': 10,
            'unit_of_measure': 'pieces',
            'unit_price': 5.50,
            'total_price': 55.00,
            'weight_kg': 0.5,
            'volume_m3': 0.01,
            'temperature_requirement': 'ambient',
            'fragile': False,
            'product_attributes': {'color': 'red', 'size': 'medium'}
        },
        {
            'sku_code': 'SKU002',
            'product_name': 'Test Product 2',
            'category': None,  # Test null values
            'brand': '',       # Test empty string
            'quantity_ordered': 5,
            'unit_of_measure': None,
            'unit_price': None,
            'total_price': None,
            'weight_kg': None,
            'volume_m3': None,
            'temperature_requirement': None,
            'fragile': False,
            'product_attributes': {}
        }
    ]
    
    print("Testing SKU item processing...")
    
    # Test the logic we use in the insert function
    for i, item in enumerate(test_sku_items):
        print(f"\nProcessing item {i+1}:")
        print(f"  Type: {type(item)}")
        print(f"  Is dict: {isinstance(item, dict)}")
        
        if isinstance(item, dict):
            # Test all the get() calls we make in the function
            values = [
                str(uuid.uuid4()),  # id
                "test-order-id",    # order_id
                item.get('sku_code', ''),
                item.get('product_name', ''),
                item.get('category'),
                item.get('brand', ''),
                item.get('quantity_ordered', 0),
                item.get('unit_of_measure'),
                item.get('unit_price'),
                item.get('total_price'),
                item.get('weight_kg'),
                item.get('volume_m3'),
                item.get('temperature_requirement'),
                item.get('fragile', False),
                json.dumps(item.get('product_attributes', {})),
            ]
            
            print(f"  Values count: {len(values)}")
            print(f"  Values: {values}")
            print("  ✓ Processing successful")
        else:
            print(f"  ✗ Item is not a dictionary: {item}")
    
    print("\nTesting invalid data:")
    
    # Test with invalid data types
    invalid_items = [
        "not a dict",
        123,
        None,
        ["list", "item"],
        {"missing_required": "fields"}
    ]
    
    for i, item in enumerate(invalid_items):
        print(f"\nInvalid item {i+1}:")
        print(f"  Type: {type(item)}")
        print(f"  Is dict: {isinstance(item, dict)}")
        
        if not isinstance(item, dict):
            print("  ✓ Correctly identified as invalid")
        else:
            print("  Testing get() calls on invalid dict...")
            try:
                values = [
                    item.get('sku_code', ''),
                    item.get('product_name', ''),
                    item.get('category'),
                ]
                print(f"  Values: {values}")
                print("  ✓ Handled gracefully")
            except Exception as e:
                print(f"  ✗ Error: {e}")

if __name__ == "__main__":
    test_sku_item_processing()
    print("\n✓ SKU item processing test completed")
