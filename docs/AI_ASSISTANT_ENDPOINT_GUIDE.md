# AI Assistant Order Processing Endpoint

This document explains how to use the new AI Assistant endpoint for processing orders.

## Endpoint Details

**URL:** `POST /api/orders/{order_id}/process-with-assistant`

**Authentication:** Bearer Token (JWT) required

**Description:** Process an order using the Azure AI Foundry Assistant that will automatically handle the complete order processing workflow.

## Request Parameters

### Path Parameters
- `order_id` (string, required): The UUID of the order to process

### Request Body (JSON, optional)
```json
{
  "user_message": "string (optional)",
  "custom_instructions": "string (optional)"
}
```

#### Fields:
- **`user_message`**: Custom message to send to the AI assistant
- **`custom_instructions`**: Specific instructions for processing (alternative to user_message)

## Response Format

### Success Response (200 OK)
```json
{
  "success": true,
  "thread_id": "thread_abc123",
  "run_id": "run_xyz789",
  "response": [
    "Order processing started...",
    "Order summary retrieved successfully...",
    "Validation completed..."
  ],
  "status": "completed",
  "error": null,
  "message": null
}
```

### Error Response (4xx/5xx)
```json
{
  "success": false,
  "thread_id": null,
  "run_id": null,
  "response": null,
  "status": null,
  "error": "Error description",
  "message": "Additional error context"
}
```

## Processing Workflow

The AI assistant automatically performs the following steps:

1. **Get Order Summary** - Retrieves current order status and details
2. **Parse Order File** - Extracts structured data from uploaded files
3. **Validate Order Data** - Checks for completeness and accuracy
4. **Generate Emails** - Creates emails for missing information
5. **Process SKU Items** - Validates and calculates SKU totals
6. **Calculate Logistics** - Determines shipping costs and logistics
7. **Apply Corrections** - Makes necessary data corrections

## Usage Examples

### 1. Basic Processing (Default Workflow)

```bash
curl -X POST "http://localhost:8000/api/orders/123e4567-e89b-12d3-a456-426614174000/process-with-assistant" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 2. With Custom Message

```bash
curl -X POST "http://localhost:8000/api/orders/123e4567-e89b-12d3-a456-426614174000/process-with-assistant" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "Please focus on validating SKU items and calculating shipping costs. Also check if customer contact information is complete."
  }'
```

### 3. With Custom Instructions

```bash
curl -X POST "http://localhost:8000/api/orders/123e4567-e89b-12d3-a456-426614174000/process-with-assistant" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "custom_instructions": "Only perform order validation and email generation. Skip logistics calculations for now."
  }'
```

## Python Client Example

```python
import httpx
import asyncio

async def process_order_with_assistant(order_id: str, auth_token: str, custom_message: str = None):
    """Process an order using the AI assistant"""
    
    url = f"http://localhost:8000/api/orders/{order_id}/process-with-assistant"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    payload = {}
    if custom_message:
        payload["user_message"] = custom_message
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Request failed: {response.status_code} - {response.text}")

# Usage
async def main():
    order_id = "123e4567-e89b-12d3-a456-426614174000"
    token = "your-jwt-token-here"
    
    # Basic processing
    result = await process_order_with_assistant(order_id, token)
    print("Processing result:", result)
    
    # Custom processing
    custom_result = await process_order_with_assistant(
        order_id, 
        token, 
        "Please focus on SKU validation and cost calculations"
    )
    print("Custom processing result:", custom_result)

# Run the example
# asyncio.run(main())
```

## JavaScript/Frontend Example

```javascript
async function processOrderWithAssistant(orderId, authToken, customMessage = null) {
    const url = `/api/orders/${orderId}/process-with-assistant`;
    
    const payload = {};
    if (customMessage) {
        payload.user_message = customMessage;
    }
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            return await response.json();
        } else {
            throw new Error(`Request failed: ${response.status}`);
        }
    } catch (error) {
        console.error('Error processing order:', error);
        throw error;
    }
}

// Usage example
async function handleOrderProcessing() {
    const orderId = "123e4567-e89b-12d3-a456-426614174000";
    const token = localStorage.getItem('authToken');
    
    try {
        // Show loading state
        showLoadingSpinner();
        
        // Process with assistant
        const result = await processOrderWithAssistant(orderId, token);
        
        if (result.success) {
            console.log('Processing successful:', result);
            showSuccessMessage(result.response);
        } else {
            console.error('Processing failed:', result.error);
            showErrorMessage(result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        showErrorMessage('Failed to process order');
    } finally {
        hideLoadingSpinner();
    }
}
```

## Error Handling

### Common Error Scenarios

1. **Order Not Found (404)**
   ```json
   {
     "detail": "Order not found"
   }
   ```

2. **Order Cannot Be Processed (400)**
   ```json
   {
     "detail": "Order cannot be processed in CANCELLED status"
   }
   ```

3. **Assistant Not Available (500)**
   ```json
   {
     "success": false,
     "error": "Azure AI Foundry packages not available"
   }
   ```

4. **Processing Failed (500)**
   ```json
   {
     "success": false,
     "error": "Assistant processing failed: Connection timeout"
   }
   ```

## Order Status Updates

The endpoint automatically updates the order status and creates tracking entries:

- **During Processing**: Status = `AI_PROCESSING`
- **On Success**: Status = `AI_PROCESSED`
- **On Error**: Status = `AI_PROCESSING_ERROR`

## Prerequisites

1. **Authentication**: Valid JWT token required
2. **Order Ownership**: Order must belong to the authenticated user
3. **Order Status**: Order must not be in `CANCELLED` or `DELIVERED` status
4. **Azure AI Setup**: Azure AI Foundry configuration must be complete

## Rate Limiting

Consider implementing rate limiting for this endpoint as AI processing can be resource-intensive.

## Monitoring

The endpoint creates tracking entries for all processing attempts, making it easy to monitor:
- Processing success/failure rates
- Performance metrics
- Error patterns

## Best Practices

1. **Handle Async Nature**: Processing may take time, consider implementing polling or webhooks
2. **Error Recovery**: Implement retry logic for transient failures
3. **User Feedback**: Provide clear status updates to users during processing
4. **Logging**: Monitor thread_id and run_id for debugging
5. **Validation**: Always validate order_id format before making requests
