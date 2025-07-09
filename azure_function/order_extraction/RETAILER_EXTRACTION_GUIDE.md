# Retailer Information Extraction and Order Update Feature

## Overview
This feature enhances the Azure Function to extract retailer information from uploaded order files, search for matching retailers in the database, and automatically update orders with the best retailer matches.

## Features Implemented

### 1. Retailer Information Extraction
- **AI-powered extraction** of retailer details from order documents
- Supports multiple file formats (CSV, Excel, PDF, Word, etc.)
- Extracts:
  - Company/retailer name
  - Contact person
  - Email address
  - Phone number
  - Business address
  - Business type

### 2. Delivery Address Extraction
- **AI-powered extraction** of delivery address information
- Extracts:
  - Street address
  - City, state, postal code
  - Country
  - Delivery instructions
  - Contact information

### 3. Retailer Search and Matching
- **Intelligent retailer search** with confidence scoring
- Search criteria:
  - Exact email match (highest priority)
  - Exact phone number match
  - Company name similarity matching
  - Partial name matching
- **Confidence scoring** (0.0 to 1.0):
  - 0.7+ = High confidence (auto-assign)
  - 0.5-0.7 = Medium confidence (review recommended)
  - <0.5 = Low confidence (manual verification required)

### 4. Automatic Order Updates
- Updates orders with extracted retailer information
- Assigns retailer_id for high-confidence matches
- Updates delivery_address field
- Adds processing notes with match details
- Maintains audit trail of retailer assignments

## Azure Function Endpoints

### 1. Extract Retailer Info (`/api/extract_retailer_info`)
**Method:** POST  
**Purpose:** Extract retailer info from order and search for matches

**Request:**
```json
{
  "order_id": "uuid-of-order"
}
```

**Response:**
```json
{
  "success": true,
  "order_id": "12345678-1234-1234-1234-123456789012",
  "order_number": "ORD-2025-001",
  "extraction_results": {
    "retailer_info": {
      "name": "ABC Retail Store",
      "contact_person": "John Smith",
      "email": "john@abcretail.com",
      "phone": "+1-555-123-4567",
      "address": {
        "street": "123 Main Street",
        "city": "Springfield",
        "state": "IL",
        "postal_code": "62701",
        "country": "USA"
      },
      "business_type": "RETAIL"
    },
    "delivery_address": {
      "street": "456 Oak Avenue",
      "city": "Springfield",
      "state": "IL",
      "postal_code": "62702",
      "delivery_instructions": "Loading dock on north side"
    }
  },
  "retailer_search": {
    "total_matches": 2,
    "matches": [
      {
        "retailer_id": 1,
        "name": "ABC Retail Store",
        "confidence_score": 0.95,
        "match_criteria": ["email_exact", "name_exact"]
      }
    ],
    "best_match": {
      "retailer_id": 1,
      "confidence_score": 0.95
    }
  },
  "update_result": {
    "success": true,
    "match_status": "matched_high_confidence",
    "retailer_id": 1
  },
  "recommendations": [
    "High confidence retailer match found and assigned automatically"
  ]
}
```

### 2. Search Retailers (`/api/search_retailers`)
**Method:** POST  
**Purpose:** Search for retailers based on criteria

**Request:**
```json
{
  "name": "ABC Retail",
  "email": "john@abcretail.com",
  "phone": "+1-555-123-4567"
}
```

**Response:**
```json
{
  "success": true,
  "search_criteria": {
    "name": "ABC Retail",
    "email": "john@abcretail.com"
  },
  "total_matches": 2,
  "matches": [
    {
      "retailer_id": 1,
      "name": "ABC Retail Store",
      "code": "ABC001",
      "contact_email": "john@abcretail.com",
      "confidence_score": 0.95,
      "match_criteria": ["email_exact", "name_partial"]
    }
  ]
}
```

### 3. Assign Retailer (`/api/assign_retailer`)
**Method:** POST  
**Purpose:** Manually assign a retailer to an order

**Request:**
```json
{
  "order_id": "12345678-1234-1234-1234-123456789012",
  "retailer_id": 1,
  "notes": "Manual assignment after verification"
}
```

**Response:**
```json
{
  "success": true,
  "order_id": "12345678-1234-1234-1234-123456789012",
  "retailer_id": 1,
  "retailer_name": "ABC Retail Store",
  "retailer_code": "ABC001",
  "processing_note": "Retailer manually assigned: ABC Retail Store (ID: 1, Code: ABC001). Manual assignment after verification"
}
```

## Database Updates

### Orders Table Updates
The following fields are updated when retailer information is processed:

- **`retailer_info`** (JSONB): Stores extracted retailer information and search results
- **`retailer_id`** (Integer): Foreign key to retailers table (for high-confidence matches)
- **`delivery_address`** (JSONB): Stores extracted delivery address information
- **`processing_notes`** (Text): Appended with match/assignment details

### Sample retailer_info JSON Structure
```json
{
  "extracted_info": {
    "name": "ABC Retail Store",
    "email": "john@abcretail.com",
    "phone": "+1-555-123-4567"
  },
  "search_results": [
    {
      "retailer_id": 1,
      "confidence_score": 0.95,
      "match_criteria": ["email_exact"]
    }
  ],
  "best_match": {
    "retailer_id": 1,
    "confidence_score": 0.95
  },
  "match_status": "matched_high_confidence",
  "last_updated": "2025-01-09T10:30:00"
}
```

## Error Handling

### When No Retailer Matches Found
```json
{
  "success": true,
  "retailer_search": {
    "total_matches": 0,
    "matches": []
  },
  "update_result": {
    "match_status": "no_match"
  },
  "recommendations": [
    "No retailer matches found - may need to create new retailer"
  ]
}
```

### When Order Already Has Retailer Assigned
```json
{
  "success": true,
  "message": "Order already has retailer assigned",
  "retailer_id": 1,
  "current_retailer_info": {...},
  "current_delivery_address": {...}
}
```

### Error Response Format
```json
{
  "success": false,
  "error": "Error description",
  "order_id": "12345678-1234-1234-1234-123456789012"
}
```

## Match Confidence Levels

### High Confidence (0.7+)
- **Action:** Automatic assignment
- **Criteria:** Exact email match OR exact phone + partial name match
- **Status:** `matched_high_confidence`

### Medium Confidence (0.5-0.7)
- **Action:** Manual review recommended
- **Criteria:** Strong name similarity OR partial contact info match
- **Status:** `matched_medium_confidence`

### Low Confidence (<0.5)
- **Action:** Manual verification required
- **Criteria:** Weak name similarity only
- **Status:** `matched_low_confidence`

### No Match
- **Action:** Create new retailer or manual search
- **Criteria:** No matches found
- **Status:** `no_match`

## Usage Workflow

1. **Order Upload**: Customer uploads order file
2. **Initial Processing**: Azure Function processes file and extracts SKU items
3. **Retailer Extraction**: Call `/api/extract_retailer_info` with order_id
4. **Automatic Matching**: System searches for retailer matches and assigns if high confidence
5. **Manual Review**: For medium/low confidence matches, review and use `/api/assign_retailer`
6. **Order Processing**: Continue with order processing using assigned retailer_id

## Configuration

### Environment Variables Required
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI service endpoint
- `AZURE_OPENAI_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_DEPLOYMENT`: Model deployment name (default: gpt-4o)
- `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`: Database connection

### Confidence Threshold Settings
- High confidence threshold: 0.7 (configurable in code)
- Medium confidence threshold: 0.5 (configurable in code)

## Testing

Use the provided test script `test_retailer_extraction.py` to validate the functionality with sample data.

## Security Considerations

- All database queries use parameterized statements to prevent SQL injection
- Retailer search is limited to active retailers only
- Processing notes include timestamps for audit trails
- Sensitive information is not logged in plain text

## Performance Considerations

- Retailer search is limited to top 10 matches for performance
- Database connections are properly closed after use
- AI extraction includes retry logic with exponential backoff
- Search results are cached in the retailer_info JSON field
