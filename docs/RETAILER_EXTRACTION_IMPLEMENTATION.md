# Retailer Information Extraction Implementation

## Overview

This implementation adds automatic retailer information extraction from order files uploaded to the system. When files are processed from the Azure Blob storage bucket, the system now:

1. **Extracts retailer information** from the file content using Azure OpenAI
2. **Searches for matching retailers** in the database
3. **Updates order records** with retailer ID, retailer info, and delivery address

## Key Features

### 1. AI-Powered Retailer Extraction
- Uses Azure OpenAI to analyze order files and extract retailer information
- Extracts company names, contact information, delivery addresses, and business details
- Returns confidence scores and extraction notes

### 2. Intelligent Database Matching
The system searches for retailers using multiple strategies in order of preference:
1. **Exact code match** - Highest priority if retailer code is found
2. **Exact name match** - Direct company name matching
3. **Email match** - Contact email matching
4. **Fuzzy name match** - Partial name matching using PostgreSQL similarity

### 3. Automatic Order Updates
When a retailer is found, the system automatically updates:
- `retailer_id` - Links to the retailers table
- `retailer_info` - JSON containing extracted and matched information
- `delivery_address` - JSON containing delivery address from the file

## New Azure Function Endpoints

### 1. Enhanced File Processing
The existing `order_file_reader` endpoint now includes retailer extraction as part of the standard file processing workflow.

### 2. Dedicated Retailer Extraction
**Endpoint**: `/api/extract_retailer_info`
**Method**: POST/GET
**Parameters**: `order_id`

Extracts retailer information from an already uploaded order file.

**Example Request**:
```json
{
  "order_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Example Response**:
```json
{
  "order_id": "123e4567-e89b-12d3-a456-426614174000",
  "order_number": "ORD-2024-001",
  "retailer_extraction": {
    "retailer_extracted": true,
    "confidence_score": 0.85,
    "extracted_info": {
      "retailer_name": "SuperMart Inc",
      "contact_email": "orders@supermart.com",
      "delivery_address": {
        "street": "123 Main St",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "USA"
      }
    }
  },
  "database_search": {
    "found": true,
    "search_method": "exact_name_match",
    "retailer": {
      "id": 42,
      "name": "SuperMart Inc",
      "code": "SM001"
    }
  },
  "updated": true,
  "message": "Retailer extraction completed - Retailer identified: SuperMart Inc"
}
```

### 3. Manual Retailer Mapping
**Endpoint**: `/api/update_retailer_mapping`
**Method**: POST
**Use Case**: When extracted retailer info doesn't match database or manual override is needed

**Example Request**:
```json
{
  "order_id": "123e4567-e89b-12d3-a456-426614174000",
  "retailer_id": 42,
  "delivery_address": {
    "street": "123 Main St",
    "city": "New York", 
    "state": "NY",
    "postal_code": "10001",
    "country": "USA"
  }
}
```

## Database Changes

### Orders Table Updates
The system updates these fields in the `orders` table:
- `retailer_id` - Foreign key reference to retailers table
- `retailer_info` - JSONB field containing extraction and matching details
- `delivery_address` - JSONB field containing delivery address information

### Example `retailer_info` JSON structure:
```json
{
  "extracted_from_file": true,
  "extraction_confidence": 0.85,
  "extraction_notes": "Clear retailer name and contact info found",
  "extracted_details": {
    "retailer_name": "SuperMart Inc",
    "contact_email": "orders@supermart.com",
    "contact_phone": "+1-555-123-4567",
    "delivery_address": {
      "street": "123 Main St",
      "city": "New York",
      "state": "NY", 
      "postal_code": "10001",
      "country": "USA"
    }
  },
  "database_match": {
    "found": true,
    "search_method": "exact_name_match",
    "matched_retailer": {
      "id": 42,
      "name": "SuperMart Inc",
      "code": "SM001"
    }
  }
}
```

### Order Tracking
All retailer extraction activities are logged in the `order_tracking` table with detailed information about:
- Extraction results and confidence scores
- Database search methods and results
- Manual updates and changes

## Requirements

### PostgreSQL Extensions
The system uses the `pg_trgm` extension for fuzzy text matching:
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### Azure OpenAI Configuration
Requires these environment variables:
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_KEY` 
- `AZURE_OPENAI_DEPLOYMENT` (default: gpt-4o)
- `AZURE_OPENAI_VERSION` (default: 2024-11-20)

### Azure Blob Storage
- `REQUESTED_ORDERS_BLOB_CONNECTION_STRING`

## Usage Workflow

### Automatic Processing
1. User uploads order file via the web interface
2. File is stored in Azure Blob storage
3. `order_file_reader` function processes the file:
   - Parses file content
   - Extracts SKU items
   - **NEW**: Extracts retailer information
   - **NEW**: Searches for retailer in database
   - **NEW**: Updates order with retailer details
4. Order tracking records all activities

### Manual Processing
1. For orders where automatic extraction didn't find a match:
   - Call `/api/extract_retailer_info` to retry extraction
   - Use `/api/update_retailer_mapping` to manually assign retailer
2. View extraction results in order tracking history

## Error Handling

The system handles various scenarios gracefully:
- **No retailer info found**: Order processed normally, retailer fields remain null
- **Fuzzy matches**: Uses similarity scoring to find close matches
- **Multiple potential matches**: Returns best match based on similarity score
- **Azure OpenAI unavailable**: Falls back to basic processing without AI analysis
- **Database errors**: Proper error logging and user feedback

## Monitoring and Logging

All retailer extraction activities are logged with:
- Extraction confidence scores
- Database search methods used
- Success/failure reasons
- Performance metrics
- Error details for troubleshooting

## Security Considerations

- Uses Azure managed identity for secure Azure OpenAI access
- Parameterized SQL queries prevent injection attacks
- Sensitive retailer information is properly encrypted in database
- Access logs track all retailer information access
