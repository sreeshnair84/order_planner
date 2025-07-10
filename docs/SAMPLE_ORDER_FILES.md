# Sample Order File for Testing Retailer Extraction

## CSV Format Example

```csv
Order Number,Date,Customer Name,Customer Email,Customer Phone,Delivery Address,Product Code,Product Name,Quantity,Unit Price,Total Price
PO-2024-001,2024-07-09,SuperMart Inc,orders@supermart.com,555-123-4567,"123 Main Street, New York, NY 10001",ABC123,Premium Coffee Beans,100,12.50,1250.00
PO-2024-001,2024-07-09,SuperMart Inc,orders@supermart.com,555-123-4567,"123 Main Street, New York, NY 10001",DEF456,Organic Tea Bags,50,8.99,449.50
PO-2024-001,2024-07-09,SuperMart Inc,orders@supermart.com,555-123-4567,"123 Main Street, New York, NY 10001",GHI789,Dark Chocolate Bars,75,3.25,243.75
```

## JSON Format Example

```json
{
  "order_info": {
    "order_number": "PO-2024-002",
    "order_date": "2024-07-09",
    "requested_delivery_date": "2024-07-15"
  },
  "customer": {
    "company_name": "Fresh Foods Market",
    "contact_person": "John Smith",
    "email": "procurement@freshfoods.com",
    "phone": "555-987-6543",
    "business_type": "Grocery Store"
  },
  "delivery_address": {
    "street": "456 Oak Avenue",
    "city": "Los Angeles",
    "state": "CA",
    "postal_code": "90210",
    "country": "USA"
  },
  "items": [
    {
      "sku": "MILK001",
      "product_name": "Whole Milk 1 Gallon",
      "category": "Dairy",
      "brand": "Farm Fresh",
      "quantity": 120,
      "unit": "gallons",
      "unit_price": 4.50,
      "total_price": 540.00,
      "weight_kg": 3.8,
      "temperature": "chilled"
    },
    {
      "sku": "BREAD002", 
      "product_name": "Artisan Bread Loaf",
      "category": "Bakery",
      "brand": "Golden Wheat",
      "quantity": 80,
      "unit": "loaves",
      "unit_price": 3.25,
      "total_price": 260.00,
      "weight_kg": 0.5,
      "temperature": "ambient"
    }
  ],
  "order_totals": {
    "subtotal": 800.00,
    "tax": 64.00,
    "total": 864.00,
    "currency": "USD"
  }
}
```

## Text Format Example

```
ORDER CONFIRMATION
==================

Order Number: PO-2024-003
Order Date: July 9, 2024
Delivery Date Requested: July 12, 2024

CUSTOMER INFORMATION:
Company: Quick Stop Convenience
Contact: Maria Rodriguez  
Email: orders@quickstop.com
Phone: 555-555-0123

DELIVERY ADDRESS:
789 Pine Street
Chicago, IL 60601
United States

ITEMS ORDERED:
==============

1. SKU: SNACK001
   Product: Mixed Nuts Variety Pack
   Quantity: 60 units
   Unit Price: $5.99
   Total: $359.40

2. SKU: DRINK002
   Product: Energy Drink 16oz
   Quantity: 144 cans
   Unit Price: $2.25
   Total: $324.00

3. SKU: CANDY003
   Product: Chocolate Candy Bars
   Quantity: 200 bars
   Unit Price: $1.50
   Total: $300.00

ORDER SUMMARY:
Subtotal: $983.40
Tax (8%): $78.67
Total: $1,062.07

Special Instructions: Deliver between 8 AM - 10 AM
```

## XML Format Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<purchase_order>
    <header>
        <order_number>PO-2024-004</order_number>
        <order_date>2024-07-09</order_date>
        <delivery_date>2024-07-14</delivery_date>
    </header>
    
    <vendor>
        <company_name>Metro Grocery Chain</company_name>
        <contact_person>David Wilson</contact_person>
        <email>purchasing@metrostore.com</email>
        <phone>555-111-2222</phone>
        <store_number>ST-0142</store_number>
    </vendor>
    
    <ship_to>
        <address_line_1>321 Broadway Street</address_line_1>
        <city>Seattle</city>
        <state>WA</state>
        <zip_code>98101</zip_code>
        <country>USA</country>
    </ship_to>
    
    <line_items>
        <item>
            <line_number>1</line_number>
            <sku>FRUIT001</sku>
            <description>Fresh Bananas</description>
            <category>Produce</category>
            <quantity>50</quantity>
            <unit_of_measure>pounds</unit_of_measure>
            <unit_price>1.89</unit_price>
            <extended_price>94.50</extended_price>
            <weight_kg>22.7</weight_kg>
            <perishable>true</perishable>
        </item>
        
        <item>
            <line_number>2</line_number>
            <sku>MEAT001</sku>
            <description>Ground Beef 80/20</description>
            <category>Meat</category>
            <quantity>25</quantity>
            <unit_of_measure>pounds</unit_of_measure>
            <unit_price>6.99</unit_price>
            <extended_price>174.75</extended_price>
            <weight_kg>11.3</weight_kg>
            <temperature_req>frozen</temperature_req>
        </item>
    </line_items>
    
    <totals>
        <subtotal>269.25</subtotal>
        <tax_rate>0.065</tax_rate>
        <tax_amount>17.50</tax_amount>
        <total_amount>286.75</total_amount>
    </totals>
</purchase_order>
```

## What the Retailer Extraction Should Find

For each of the above examples, the AI should extract:

### Retailer Information:
- **Company Name**: SuperMart Inc, Fresh Foods Market, Quick Stop Convenience, Metro Grocery Chain
- **Contact Email**: orders@supermart.com, procurement@freshfoods.com, etc.
- **Contact Phone**: 555-123-4567, 555-987-6543, etc.
- **Contact Person**: John Smith, Maria Rodriguez, David Wilson

### Delivery Address:
- **Street**: 123 Main Street, 456 Oak Avenue, 789 Pine Street, 321 Broadway Street
- **City**: New York, Los Angeles, Chicago, Seattle  
- **State**: NY, CA, IL, WA
- **Postal Code**: 10001, 90210, 60601, 98101
- **Country**: USA (or inferred)

### Additional Details:
- **Business Type**: Grocery Store, Convenience Store, etc.
- **Store Number**: ST-0142
- **Tax ID**: (if present in actual files)

## Testing Instructions

1. Save one of these examples as a file (e.g., `sample_order.csv`)
2. Upload to the system via the web interface
3. Note the order ID created
4. Test retailer extraction:
   ```bash
   python integration_test.py https://your-function-app.azurewebsites.net order-uuid-here
   ```

The system should:
- Extract the retailer information with high confidence (>0.8)
- Search for matching retailers in the database
- Update the order with retailer ID (if found) or extracted info
- Log all activities in order tracking
