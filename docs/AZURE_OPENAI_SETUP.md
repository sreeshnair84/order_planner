# Azure OpenAI Integration Setup

## Overview
This Azure Function integrates with Azure OpenAI to provide AI-powered order parsing and completeness checking for FMCG supply chain operations.

## Implementation Details

### Authentication Pattern
The implementation follows Microsoft's recommended authentication pattern using:
- **Managed Identity**: For production environments
- **DefaultAzureCredential**: Handles multiple credential types
- **Token Provider**: Uses `get_bearer_token_provider` for secure token management

### Azure OpenAI Configuration

#### Required Environment Variables
```json
{
  "AZURE_OPENAI_ENDPOINT": "https://your-openai-resource.openai.azure.com/",
  "AZURE_OPENAI_DEPLOYMENT": "gpt-4o"
}
```

#### API Version
- Uses latest stable API version: **2024-10-21**
- Supports structured JSON responses
- Includes automatic retry logic

### Features

#### 1. Order Completeness Analysis
- Analyzes parsed order data for completeness
- Returns completeness score (0.0 - 1.0)
- Identifies missing fields and validation errors
- Provides recommendations for improvement

#### 2. SKU Item Extraction
- Extracts individual product items from order data
- Standardizes product information format
- Handles various file types (CSV, Excel, JSON, Word, Text)

#### 3. Error Handling
- Comprehensive error handling for all OpenAI API errors
- Automatic retry with exponential backoff
- Fallback responses when AI is unavailable
- Detailed logging for troubleshooting

### Error Types Handled
- `APIConnectionError`: Network connectivity issues
- `RateLimitError`: API rate limit exceeded
- `APIStatusError`: HTTP status errors (4xx, 5xx)
- `AuthenticationError`: Authentication failures
- `JSONDecodeError`: Response parsing errors

### Database Schema Compatibility

#### Order Table Fields Used
- `id`: Order UUID
- `order_number`: Unique order identifier
- `parsed_data`: JSON field for AI analysis results
- `missing_fields`: JSON array of missing required fields
- `validation_errors`: JSON array of validation issues
- `total_sku_count`: Number of SKU items
- `total_quantity`: Sum of all quantities
- `total_weight_kg`: Total weight
- `total_volume_m3`: Total volume
- `subtotal`: Total price before tax

#### OrderSKUItem Table Fields
- `sku_code`: Product SKU identifier
- `product_name`: Product description
- `category`: Product category
- `brand`: Brand name
- `quantity_ordered`: Ordered quantity
- `unit_of_measure`: Unit type
- `unit_price`: Price per unit
- `total_price`: Total price for quantity
- `weight_kg`: Item weight
- `volume_m3`: Item volume
- `temperature_requirement`: Storage temperature
- `fragile`: Fragility indicator
- `product_attributes`: Additional attributes (JSON)

## API Endpoints

### 1. `/api/order_file_reader`
**Purpose**: Parse order files and analyze completeness

**Parameters**:
- `order_id` (required): UUID of the order to process

**Response**:
```json
{
  "order_id": "uuid",
  "order_number": "string",
  "parse_status": "PARSING_COMPLETE|PARSING_PARTIAL|PARSING_INCOMPLETE|PARSING_FAILED",
  "parse_message": "string",
  "parsed_data": {},
  "ai_analysis": {
    "completeness_score": 0.85,
    "missing_fields": [],
    "validation_errors": [],
    "recommendations": []
  },
  "sku_items": [],
  "summary": {
    "total_sku_count": 10,
    "completeness_score": 0.85,
    "missing_fields_count": 2,
    "validation_errors_count": 0
  }
}
```

### 2. `/api/validate_order_completeness`
**Purpose**: Validate existing order completeness

**Parameters**:
- `order_id` (required): UUID of the order to validate

**Response**:
```json
{
  "order_id": "uuid",
  "validation_timestamp": "ISO datetime",
  "completeness_metrics": {
    "has_order_number": true,
    "has_sku_items": true,
    "sku_count_match": true,
    "has_pricing": true,
    "completeness_score": 0.9
  },
  "ai_analysis": {},
  "recommendations": [],
  "next_steps": []
}
```

### 3. `/api/health`
**Purpose**: Health check and configuration status

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "ISO datetime",
  "azure_openai_configured": true
}
```

## Deployment Requirements

### Azure Resources Needed
1. **Azure Function App** (Python 3.9+)
2. **Azure OpenAI Service** with GPT-4o deployment
3. **Azure Storage Account** for file storage
4. **PostgreSQL Database** (Azure Database for PostgreSQL)

### Managed Identity Setup
1. Enable System-assigned or User-assigned Managed Identity on Function App
2. Grant **Cognitive Services OpenAI User** role to the identity
3. Scope the role assignment to the Azure OpenAI resource

### Local Development
1. Install Azure CLI: `az login`
2. Set environment variables in `local.settings.json`
3. Run: `func start` from the `/az` directory

## Performance Considerations

### Token Limits
- Analysis prompts: ~1500 max tokens
- SKU extraction: ~2000 max tokens
- Automatic truncation for large datasets

### Retry Logic
- 3 automatic retries with exponential backoff
- 2-second delay for rate limit errors
- Circuit breaker pattern for persistent failures

### Caching
- Connection pooling for database
- Token caching via DefaultAzureCredential
- Response caching recommended for production

## Security Best Practices

### Authentication
- ✅ Uses Managed Identity (no keys in code)
- ✅ Secure token provider pattern
- ✅ Automatic token refresh

### Data Protection
- ✅ No sensitive data in logs
- ✅ Encrypted database connections (SSL)
- ✅ Secure blob storage access

### Access Control
- ✅ Function-level authentication
- ✅ RBAC for Azure OpenAI access
- ✅ Database user permissions

## Monitoring & Logging

### Application Insights
- Track AI request success/failure rates
- Monitor token usage and costs
- Alert on high error rates

### Custom Metrics
- Order processing completeness scores
- SKU extraction accuracy
- AI service availability

### Log Categories
- `INFO`: Successful operations
- `WARNING`: Fallback scenarios
- `ERROR`: AI service failures
- `DEBUG`: Detailed request/response data

## Troubleshooting

### Common Issues

1. **"Azure OpenAI endpoint not configured"**
   - Check `AZURE_OPENAI_ENDPOINT` environment variable
   - Verify endpoint URL format

2. **Authentication failures**
   - Verify Managed Identity is enabled
   - Check RBAC role assignments
   - Ensure correct token scope

3. **Rate limit errors**
   - Monitor token usage in Azure Portal
   - Consider upgrading to higher tier
   - Implement request queuing

4. **JSON parsing errors**
   - Check AI model response format
   - Verify `response_format` parameter
   - Review prompt engineering

### Debug Commands
```bash
# Test connectivity
func start --debug

# Check environment
echo $AZURE_OPENAI_ENDPOINT

# Verify authentication
az account show
```

## Cost Optimization

### Token Usage
- Optimize prompts for clarity and brevity
- Use structured JSON responses
- Implement result caching where appropriate

### Model Selection
- `gpt-4o`: Best accuracy, higher cost
- `gpt-4o-mini`: Good accuracy, lower cost
- Monitor cost vs. accuracy trade-offs

### Usage Patterns
- Batch processing for multiple orders
- Asynchronous processing for large files
- Rate limiting to control costs
