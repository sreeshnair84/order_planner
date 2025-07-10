# SKU Items Processing Remarks Feature

## Overview
This feature adds detailed processing remarks to SKU items to track missing information and validation issues at the item level. This helps identify which specific SKU items need attention and what information is missing.

## Changes Made

### 1. Database Schema Update
- Added `processing_remarks` column to `order_sku_items` table
- Column type: `TEXT` (nullable)
- Stores comma-separated remarks about missing or invalid data

### 2. Backend Updates

#### Model Changes (`backend/app/models/sku_item.py`)
- Added `processing_remarks` field to `OrderSKUItem` model

#### Schema Updates (`backend/app/models/schemas.py`)
- Added `processing_remarks` to both `SKUItemCreate` and `SKUItemResponse` schemas

#### Service Updates (`backend/app/services/sku_service.py`)
- Updated `create_sku_items` method to handle processing remarks
- Updated `convert_to_response` method to include processing remarks

#### Order Processing (`backend/app/services/unified_order_processor.py`)
- Enhanced `process_sku_items` method to generate processing remarks for:
  - Missing SKU codes
  - Missing product names
  - Invalid quantities
  - Missing pricing
  - Missing categories/brands
  - Default values used for weight/volume

### 3. Azure Function Updates (`azure_function/order_extraction/function_app.py`)
- Updated database insert to include processing_remarks field
- Enhanced AI prompts to generate processing remarks
- Updated SKU extraction to identify missing fields

### 4. Frontend Updates

#### New SKU Items Tab
- Added "SKU Items" tab to Order Processing Screen
- Displays detailed table with all SKU item information
- Shows processing remarks in highlighted format
- Includes summary statistics

#### Service Integration (`frontend/src/services/orderService.js`)
- Added `getOrderSKUItems()` method to fetch SKU details

## Usage

### For Users
1. **View SKU Items**: Navigate to Order Processing → Select Order → SKU Items tab
2. **Review Remarks**: Check the "Processing Remarks" column for any issues
3. **Take Action**: Address missing information based on remarks

### Processing Remarks Examples
- "Missing SKU code"
- "Missing or invalid pricing information"
- "Missing product category"
- "Using default weight (1kg) - actual weight not provided"
- "Processing error: Invalid data format"

### Summary Statistics
The SKU Items tab shows:
- Total number of SKU items
- Total quantity across all items
- Total order value
- Number of items with processing remarks

## Database Migration

To add the new column to existing installations:

### Windows
```batch
cd backend\scripts
migrate_add_processing_remarks.bat
```

### Manual SQL
```sql
ALTER TABLE order_sku_items 
ADD COLUMN processing_remarks TEXT;
```

### Python Script
```bash
cd backend/scripts
python add_processing_remarks_column.py
```

## API Endpoints

### Get SKU Items for Order
```
GET /api/requestedorders/{order_id}/sku-details
```

Returns array of SKU items with processing remarks:
```json
[
  {
    "id": "uuid",
    "sku_code": "ABC123",
    "product_name": "Product Name",
    "quantity_ordered": 10,
    "unit_price": 15.99,
    "processing_remarks": "Missing product category",
    ...
  }
]
```

## Benefits

1. **Granular Tracking**: Know exactly which SKU items have issues
2. **Automated Detection**: AI and validation logic automatically identify problems
3. **Better Visibility**: Frontend clearly shows items needing attention
4. **Improved Processing**: Focus effort on specific problematic items
5. **Audit Trail**: Track what issues were found and when

## Next Steps

1. Run database migration to add the new column
2. Test the new SKU Items tab in the frontend
3. Review processing remarks for existing orders
4. Update order processing workflows to address remarked items

## Troubleshooting

### Common Issues
1. **Column doesn't exist**: Run the database migration script
2. **No remarks showing**: Check if AI analysis is working properly
3. **Tab not appearing**: Ensure frontend code is updated and built

### Validation
To verify the feature is working:
1. Process a new order with incomplete data
2. Check SKU Items tab for processing remarks
3. Verify remarks are stored in database
4. Confirm AI is generating appropriate remarks

## Technical Notes

- Processing remarks are generated during order parsing and SKU processing
- AI prompts specifically look for missing required fields
- Remarks are stored as text and can contain multiple issues separated by semicolons
- Frontend displays remarks in highlighted boxes for visibility
- The feature is backward compatible with existing orders (they will have null remarks)
