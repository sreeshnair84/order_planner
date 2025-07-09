# Enhanced Order File Reader Azure Function

This Azure Function provides AI-powered order file parsing and completeness validation for FMCG supply chain operations.

## Features

### 🔍 Enhanced File Parsing
- **Multi-format Support**: CSV, Excel, JSON, Text, Word documents
- **Intelligent Data Extraction**: Uses Azure OpenAI to extract structured data from various file formats
- **Comprehensive Analysis**: Detailed parsing with metadata and statistics

### 🤖 AI-Powered Order Analysis
- **Completeness Scoring**: Automated assessment of order completeness (0.0 to 1.0 scale)
- **Missing Field Detection**: Identifies required fields that are missing
- **Validation Error Detection**: Finds data quality issues and inconsistencies
- **Smart Recommendations**: Provides actionable suggestions for order improvement

### 📊 SKU Item Extraction
- **Automated SKU Parsing**: Extracts individual product items using AI
- **Rich Product Data**: Captures SKU codes, names, quantities, pricing, and attributes
- **Database Integration**: Automatically stores extracted SKU items in the database

### 📈 Order Summary Calculation
- **Automatic Metrics**: Calculates total SKU count, quantities, weights, volumes
- **Pricing Analysis**: Computes subtotals and identifies pricing gaps
- **Status Management**: Updates order status based on completeness analysis

## API Endpoints

### 1. Order File Reader
**Endpoint**: `POST /api/order_file_reader`

Parses order files and performs comprehensive analysis.

**Parameters**:
- `order_id` (string): UUID of the order to process

**Response**:
```json
{
  "order_id": "uuid",
  "order_number": "string",
  "priority": "string",
  "requested_delivery_date": "date",
  "file_info": {
    "original_filename": "string",
    "file_path": "string",
    "file_type": "string",
    "file_size": "number"
  },
  "parse_status": "PARSING_COMPLETE|PARSING_PARTIAL|PARSING_INCOMPLETE|PARSING_FAILED",
  "parse_message": "string",
  "parsed_data": {},
  "ai_analysis": {
    "completeness_score": "float",
    "missing_fields": ["array"],
    "validation_errors": ["array"],
    "recommendations": ["array"],
    "order_summary": {}
  },
  "sku_items": [],
  "summary": {
    "total_sku_count": "number",
    "completeness_score": "float",
    "missing_fields_count": "number",
    "validation_errors_count": "number"
  }
}
```

### 2. Order Completeness Validation
**Endpoint**: `POST /api/validate_order_completeness`

Validates existing order data for completeness and provides recommendations.

**Parameters**:
- `order_id` (string): UUID of the order to validate

**Response**:
```json
{
  "order_id": "uuid",
  "order_number": "string",
  "validation_timestamp": "datetime",
  "completeness_metrics": {
    "has_order_number": "boolean",
    "has_sku_items": "boolean",
    "sku_count_match": "boolean",
    "has_pricing": "boolean",
    "has_categories": "boolean",
    "completeness_score": "float"
  },
  "ai_analysis": {},
  "recommendations": ["array"],
  "sku_summary": {},
  "next_steps": ["array"]
}
```

### 3. Health Check
**Endpoint**: `GET /api/health`

Returns function health status and configuration.

## Configuration

### Required Environment Variables

1. **Database Configuration**:
   - `DB_HOST`: PostgreSQL server hostname
   - `DB_NAME`: Database name
   - `DB_USER`: Database username
   - `DB_PASSWORD`: Database password
   - `DB_PORT`: Database port (default: 5432)

2. **Azure Storage**:
   - `AzureWebJobsStorage`: Azure Storage connection string

3. **Azure OpenAI** (for AI features):
   - `AZURE_OPENAI_ENDPOINT`: Azure OpenAI service endpoint
   - `AZURE_OPENAI_DEPLOYMENT`: Deployment name (default: "gpt-4")

### Database Schema

The function works with the following tables:

1. **orders**: Main order table with enhanced fields
2. **order_sku_items**: Individual SKU items for each order
3. **order_tracking**: Tracking history for order processing

## Deployment

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Settings**:
   - Update `local.settings.json` with your configuration
   - Ensure Azure OpenAI resource is created and accessible

3. **Deploy to Azure**:
   ```bash
   func azure functionapp publish <your-function-app-name>
   ```

## Authentication & Security

- Uses **Azure Managed Identity** for Azure OpenAI authentication (recommended)
- Supports **DefaultAzureCredential** for local development
- Database connections use SSL/TLS encryption
- No hardcoded credentials - all secrets in environment variables

## AI Analysis Details

### Completeness Scoring
- **0.9-1.0**: Order is complete and ready for processing
- **0.7-0.9**: Order is mostly complete with minor issues
- **0.5-0.7**: Order has significant gaps requiring attention
- **0.0-0.5**: Order is incomplete and needs major revision

### SKU Extraction Intelligence
- Automatically identifies product information from various formats
- Handles missing data gracefully with null values
- Validates quantity fields and data types
- Extracts product attributes and classifications

### Validation Categories
- **Required Fields**: Order number, customer info, delivery details
- **Product Data**: SKU codes, quantities, descriptions
- **Pricing Information**: Unit prices, totals, taxes
- **Logistics Data**: Weights, volumes, special requirements

## Error Handling

- Comprehensive error logging with Azure Application Insights
- Graceful degradation when AI services are unavailable
- Retry logic for transient database connection issues
- Detailed error messages for debugging

## Performance Considerations

- Connection pooling for database operations
- Efficient file parsing with streaming for large files
- Batch operations for SKU item insertions
- Optimized AI prompts to minimize token usage

## Monitoring

Monitor the following metrics:
- Function execution duration
- Parse success/failure rates
- AI analysis accuracy
- Database connection health
- File processing throughput

## Support

For issues or questions:
1. Check function logs in Azure Portal
2. Verify environment variable configuration
3. Ensure Azure OpenAI service is accessible
4. Validate database connectivity and schema
