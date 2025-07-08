# Order Processing System with AI Foundry Integration

## Overview

This implementation provides a comprehensive order processing system with Azure AI Foundry integration, featuring:

- **Enhanced Order Processing Screen** - React frontend for viewing, processing, and reprocessing orders
- **AI Foundry Agent Integration** - Azure AI-powered order processing with agent tools
- **Human-in-the-Loop Email Workflow** - Email-based corrections and confirmations
- **Real-time Processing Traces** - Complete visibility of all processing steps
- **Consolidated Backend Architecture** - Optimized and deduplicated backend services

## Key Features

### 1. Order Processing Screen (Frontend)

**Location**: `frontend/src/components/OrderProcessingScreen.js`

**Features**:
- **Multi-tab Interface**: Overview, Processing, AI Agent, Tracking, Communications
- **Real-time Updates**: Auto-refresh every 3-10 seconds
- **Order Actions**: View, Process, Reprocess, Correct, AI Process
- **Status Tracking**: Visual status indicators and progress tracking
- **AI Thread Management**: Create and monitor AI agent threads

**Usage**:
```javascript
import OrderProcessingScreen from '../components/OrderProcessingScreen';

<OrderProcessingScreen 
  orderId={orderId}
  onClose={handleClose}
/>
```

### 2. AI Foundry Agent Service

**Location**: `backend/app/services/ai_foundry_agent_service.py`

**Features**:
- **Thread Management**: Create and manage AI agent threads
- **Agent Tools**: 6 specialized tools for order processing
- **Tool Execution**: Parse files, validate data, generate emails, etc.
- **State Tracking**: Complete thread state management
- **Error Handling**: Robust error handling and retries

**Available Tools**:
1. `parse_order_file` - Parse uploaded order files
2. `validate_order_data` - Validate order completeness
3. `generate_missing_info_email` - Generate emails for missing info
4. `process_sku_items` - Process and validate SKU items
5. `calculate_logistics` - Calculate shipping and logistics
6. `update_order_status` - Update order status

### 3. Enhanced API Endpoints

**AI Agent API** (`backend/app/api/ai_agent.py`):
- `POST /api/ai-agent/threads` - Create AI thread
- `GET /api/ai-agent/threads/{thread_id}` - Get thread state
- `POST /api/ai-agent/threads/{thread_id}/run` - Run agent
- `GET /api/ai-agent/orders/{order_id}/threads` - List order threads
- `POST /api/ai-agent/orders/{order_id}/process-with-ai` - AI process order

**Enhanced Processing API** (`backend/app/api/enhanced_order_processing.py`):
- `POST /api/orders/{order_id}/reprocess` - Reprocess with new ID
- `POST /api/orders/{order_id}/correct` - Apply corrections
- `GET /api/orders/{order_id}/steps` - Get processing steps
- `GET /api/orders/{order_id}/summary` - Get order summary

**Human-in-Loop Email API** (`backend/app/api/human_in_loop_email.py`):
- `GET /api/orders/{order_id}/emails/pending` - Get pending emails
- `POST /api/orders/{order_id}/emails/{email_id}/approve` - Approve email
- `POST /api/orders/{order_id}/emails/retailer-response` - Handle retailer response
- `POST /api/orders/{order_id}/structured-order/confirm` - Confirm order

### 4. Database Models

**AI Agent Thread** (`backend/app/models/ai_agent_thread.py`):
```python
class AIAgentThread(Base):
    __tablename__ = "ai_agent_threads"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    thread_id = Column(String(255), unique=True)
    status = Column(String(50))
    messages = Column(JSONB)
    tools_used = Column(JSONB)
    metadata = Column(JSONB)
```

## Configuration

### Environment Variables (.env)

```bash
# Azure AI Foundry Configuration
AZURE_AI_PROJECT_CONNECTION_STRING=your-azure-ai-project-connection-string
AZURE_AI_PROJECT_ID=your-project-id
AZURE_AI_RESOURCE_GROUP=your-resource-group
AZURE_AI_SUBSCRIPTION_ID=your-subscription-id
AZURE_AI_REGION=eastus

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-openai-api-key
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_MODEL_NAME=gpt-4

# Azure AI Assistant Configuration
AZURE_AI_ASSISTANT_ID=your-assistant-id
AZURE_AI_THREAD_TIMEOUT=300

# Azure Authentication
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id

# AI Agent Configuration
AI_AGENT_ENABLED=true
AI_AGENT_MAX_ITERATIONS=10
AI_AGENT_TEMPERATURE=0.1
AI_AGENT_MAX_TOKENS=4000
```

## Installation and Setup

### Prerequisites

1. **Python 3.9+** with pip
2. **Node.js 16+** with npm
3. **PostgreSQL 12+** 
4. **Redis 6+**
5. **Azure Account** with AI services access

### 1. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# If you encounter Azure package issues, install them separately:
pip install azure-ai-projects --pre
pip install azure-identity azure-core
pip install openai>=1.13.0

# Set up environment variables
cp ../.env.example .env
# Edit .env with your Azure credentials (see configuration section below)

# Run database migrations
alembic upgrade head

# Start the backend server
python -m uvicorn app.main:app --reload --port 8000
```

#### Troubleshooting Azure Package Installation

If you encounter issues installing Azure AI packages:

```bash
# Option 1: Install from pre-release versions
pip install azure-ai-projects --pre --upgrade
pip install azure-identity --upgrade
pip install azure-core --upgrade

# Option 2: Use specific versions
pip install azure-ai-projects==1.0.0b4
pip install azure-identity==1.15.0
pip install azure-core==1.29.0

# Option 3: If packages are not available, the system will fall back to mock implementation
# Check the logs for "Agent not initialized" warnings
```

### 2. Azure AI Foundry Setup (Required for AI Features)

#### Step 1: Create Azure Resources

```bash
# Install Azure CLI if not already installed
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Create resource group
az group create --name order-processing-rg --location eastus

# Create Azure OpenAI resource
az cognitiveservices account create \
  --name order-processing-openai \
  --resource-group order-processing-rg \
  --kind OpenAI \
  --sku S0 \
  --location eastus

# Create Azure AI Project (using Azure AI Studio)
# This requires using the Azure AI Studio portal
```

#### Step 2: Configure Azure AI Studio

1. **Go to [Azure AI Studio](https://ml.azure.com/)**
2. **Create new AI Project**:
   - Name: `order-processing-ai`
   - Resource Group: `order-processing-rg`
   - Region: `East US`
3. **Create AI Hub** (if needed)
4. **Deploy OpenAI Model**:
   - Model: `gpt-4` or `gpt-4-turbo`
   - Deployment name: `gpt-4-deployment`
5. **Get Connection String**:
   - Go to Project Settings
   - Copy the connection string

#### Step 3: Configure Environment Variables

Update your `.env` file with the Azure credentials:

## Usage Workflow

### 1. Upload Order
1. Navigate to Order Creation page
2. Upload CSV/XML file with order data
3. Set priority and special instructions
4. Click "Upload Order"

### 2. Process Order
1. Click "View" on uploaded order
2. Order Processing Screen opens
3. Choose processing method:
   - **Process**: Standard processing
   - **Process with AI**: AI-powered processing
   - **Reprocess**: Reprocess with new ID

### 3. AI Agent Processing
1. Click "Process with AI" or go to AI Agent tab
2. Create new AI thread with instructions
3. Monitor real-time processing steps
4. View tool execution results
5. Handle any human-in-loop requirements

### 4. Human-in-Loop Email Workflow
1. System generates emails for missing information
2. Emails require human approval before sending
3. Retailer responds with corrections
4. System processes responses and updates order
5. Final structured order requires confirmation

### 5. Tracking and Monitoring
1. View real-time processing traces
2. Monitor AI agent thread status
3. Track email communications
4. Review processing steps and duration

## Architecture Benefits

### 1. Consolidated Backend
- **Eliminated Duplication**: Consolidated duplicate processing logic
- **Service Layer**: Clean separation of concerns
- **Unified API**: Consistent API patterns across all endpoints

### 2. Agent-Based Processing
- **Tool-Based Architecture**: Modular, reusable processing tools
- **State Management**: Complete thread state tracking
- **Error Recovery**: Automatic retry and error handling

### 3. Real-Time Visibility
- **Live Updates**: Real-time status updates in frontend
- **Complete Traces**: Full processing history and traces
- **Interactive Monitoring**: Click-through to detailed information

### 4. Human-in-Loop Integration
- **Email Workflow**: Structured email-based corrections
- **Approval Process**: Human approval for critical communications
- **Confirmation Flow**: Multi-step order confirmation process

## API Integration Examples

### Create AI Thread and Process Order

```javascript
import { aiAgentService } from '../services/aiAgentService';

// Create AI thread for order processing
const response = await aiAgentService.createThread(
  orderId,
  "Please process this order with full validation and generate any necessary emails",
  true // auto-start
);

// Monitor thread progress
const threadState = await aiAgentService.getThreadState(response.data.thread_id);
```

### Handle Human-in-Loop Email

```javascript
// Get pending emails
const pendingEmails = await orderService.getPendingEmails(orderId);

// Approve email with modifications
await orderService.approveEmail(orderId, emailId, {
  approved: true,
  modifications: {
    subject: "Updated subject line",
    content: "Modified email content"
  },
  send_immediately: true
});
```

### Reprocess Order with New ID

```javascript
// Reprocess with new order ID
const reprocessResult = await orderService.reprocessOrder(orderId, {
  new_order_id: "ORD-2025-NEW-001",
  processing_options: {
    skip_validation: false,
    force_ai_processing: true
  }
});
```

## Monitoring and Debugging

### 1. Processing Traces
- View complete processing history in Tracking tab
- Each step shows start/end times and duration
- Error messages and retry attempts logged

### 2. AI Agent Monitoring
- Real-time thread status updates
- Tool execution results and metadata
- Message history and conversation flow

### 3. Email Communication Tracking
- Complete email thread for each order
- Approval status and modification history
- Retailer response tracking and processing

## Security Considerations

1. **Authentication**: All API endpoints require valid JWT tokens
2. **Authorization**: Users can only access their own orders
3. **Azure Integration**: Uses Azure service principal authentication
4. **Data Encryption**: All sensitive data encrypted in transit and at rest
5. **Audit Trail**: Complete audit trail of all processing steps

## Performance Optimizations

1. **Real-time Updates**: Efficient polling with configurable intervals
2. **Async Processing**: All heavy processing done asynchronously
3. **Caching**: Redis caching for frequently accessed data
4. **Database Optimization**: Proper indexing and query optimization
5. **Frontend Optimization**: React Query for efficient data fetching

## Troubleshooting

### Common Issues

1. **AI Agent Not Working**:
   - Check Azure AI Foundry credentials
   - Verify assistant ID configuration
   - Check network connectivity to Azure

2. **Email Workflow Issues**:
   - Verify SMTP configuration
   - Check email template formatting
   - Review approval workflow settings

3. **Processing Errors**:
   - Check file format and structure
   - Review validation error messages
   - Verify all required fields present

### Logs and Debugging

- Backend logs: Check FastAPI application logs
- Frontend logs: Check browser console
- Azure logs: Monitor Azure AI Foundry logs
- Database logs: Check PostgreSQL logs for query issues

## Future Enhancements

1. **Advanced AI Models**: Integration with newer AI models and capabilities
2. **Workflow Automation**: More sophisticated automation rules
3. **Analytics Dashboard**: Advanced analytics and reporting
4. **Multi-tenant Support**: Support for multiple organizations
5. **Mobile Interface**: Mobile-responsive design improvements
