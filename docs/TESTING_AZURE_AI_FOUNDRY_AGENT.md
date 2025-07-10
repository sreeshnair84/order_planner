# Testing Azure AI Foundry Order Processing Agent

This guide provides step-by-step instructions for testing the migrated `order_processing_assistant_v2.py` that now uses the Azure AI Foundry Agents API.

## Prerequisites

### 1. Install Required Packages

Ensure you have all the Azure AI Foundry packages installed:

```bash
pip install -r backend/requirements.txt
```

Key packages needed:
- `azure-ai-projects`
- `azure-ai-agents`
- `azure-identity`

### 2. Environment Variables

Set up the following environment variables in your `.env` file or environment:

```env
# Azure AI Project Configuration
PROJECT_ENDPOINT=https://your-ai-project.cognitiveservices.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/

# Azure Authentication (optional if using DefaultAzureCredential)
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id

# Database Configuration
DATABASE_URL=your-database-url
```

### 3. Azure Authentication

The agent uses `DefaultAzureCredential` which supports multiple authentication methods:

1. **Azure CLI**: Run `az login` if you have Azure CLI installed
2. **Environment Variables**: Set the client ID, secret, and tenant ID above
3. **Managed Identity**: If running on Azure resources
4. **Visual Studio/VS Code**: If signed into Azure

## Testing Methods

### Method 1: Direct Script Testing

Create a simple test script to verify the agent works:

```python
# test_azure_agent.py
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from agents.order_processing_assistant_v2 import OrderProcessingAgentV2, create_order_processing_assistant
from app.database.session import get_db

async def test_agent_initialization():
    """Test if the agent initializes correctly"""
    print("Testing Azure AI Foundry Agent Initialization...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create agent
        agent = OrderProcessingAgentV2(db)
        
        # Check status
        status = agent.get_status()
        print(f"Agent Status: {status}")
        
        if status['initialized']:
            print("✅ Agent initialized successfully!")
            print(f"Assistant ID: {status['assistant_id']}")
        else:
            print("❌ Agent initialization failed")
            if not status['azure_ai_available']:
                print("   - Azure AI packages not available")
            if not status['client_available']:
                print("   - Azure AI client not available")
            if not status['assistant_available']:
                print("   - Assistant not created")
        
        return agent, status['initialized']
        
    except Exception as e:
        print(f"❌ Error testing agent: {str(e)}")
        return None, False

async def test_agent_functions():
    """Test individual agent functions"""
    print("\nTesting individual agent functions...")
    
    db = next(get_db())
    agent = OrderProcessingAgentV2(db)
    
    if not agent.is_initialized:
        print("❌ Agent not initialized, skipping function tests")
        return
    
    # Test with a dummy order ID
    test_order_id = "test_order_123"
    
    try:
        # Test get order summary
        print("Testing _get_order_summary_sync...")
        result = agent._get_order_summary_sync(test_order_id)
        print(f"Result: {result[:100]}..." if len(result) > 100 else f"Result: {result}")
        
        # Test parse order file
        print("\nTesting _parse_order_file_sync...")
        result = agent._parse_order_file_sync(test_order_id)
        print(f"Result: {result[:100]}..." if len(result) > 100 else f"Result: {result}")
        
        # Test validation
        print("\nTesting _validate_order_data_sync...")
        result = agent._validate_order_data_sync(test_order_id)
        print(f"Result: {result[:100]}..." if len(result) > 100 else f"Result: {result}")
        
    except Exception as e:
        print(f"❌ Error testing functions: {str(e)}")

async def test_order_processing():
    """Test complete order processing workflow"""
    print("\nTesting complete order processing...")
    
    db = next(get_db())
    agent = OrderProcessingAgentV2(db)
    
    if not agent.is_initialized:
        print("❌ Agent not initialized, skipping order processing test")
        return
    
    # Test with a real order ID from your database
    test_order_id = input("Enter an order ID to test (or press Enter to skip): ").strip()
    
    if not test_order_id:
        print("Skipping order processing test")
        return
    
    try:
        result = await agent.process_order(
            order_id=test_order_id,
            user_message="Please get the order summary and validate the order data."
        )
        
        print(f"Processing Result: {result}")
        
        if result['success']:
            print("✅ Order processing completed successfully!")
            if 'response' in result:
                print(f"Assistant Response: {result['response']}")
        else:
            print(f"❌ Order processing failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error testing order processing: {str(e)}")

async def main():
    """Main test function"""
    print("Azure AI Foundry Order Processing Agent Test")
    print("=" * 50)
    
    # Test 1: Initialization
    agent, initialized = await test_agent_initialization()
    
    if not initialized:
        print("\n❌ Cannot proceed with further tests - agent not initialized")
        return
    
    # Test 2: Individual functions
    await test_agent_functions()
    
    # Test 3: Complete order processing
    await test_order_processing()
    
    print("\n" + "=" * 50)
    print("Testing completed!")

if __name__ == "__main__":
    asyncio.run(main())
```

### Method 2: Integration Testing

Test the agent within your existing application:

```python
# Add to your existing test files or create test_agent_integration.py

async def test_agent_in_api_context():
    """Test the agent within the API context"""
    from app.main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Test the endpoint that uses the agent
    response = client.post(
        "/api/requestedorders/process-with-agent",
        json={
            "order_id": "test_order_123",
            "message": "Please process this order completely"
        }
    )
    
    print(f"API Response: {response.status_code}")
    print(f"Response Data: {response.json()}")
```

### Method 3: Unit Testing

Create proper unit tests:

```python
# tests/test_azure_agent.py
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from agents.order_processing_assistant_v2 import OrderProcessingAgentV2

class TestOrderProcessingAgentV2:
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def agent(self, mock_db):
        return OrderProcessingAgentV2(mock_db)
    
    def test_initialization_without_azure_packages(self, mock_db):
        """Test graceful handling when Azure packages aren't available"""
        with patch('agents.order_processing_assistant_v2.AZURE_AI_AVAILABLE', False):
            agent = OrderProcessingAgentV2(mock_db)
            assert not agent.is_initialized
            
            status = agent.get_status()
            assert not status['azure_ai_available']
    
    @patch('agents.order_processing_assistant_v2.AZURE_AI_AVAILABLE', True)
    @patch('agents.order_processing_assistant_v2.AIProjectClient')
    def test_successful_initialization(self, mock_client_class, mock_db):
        """Test successful initialization with Azure packages"""
        mock_client = Mock()
        mock_assistant = Mock()
        mock_assistant.id = "test_assistant_id"
        
        mock_client.agents.create_agent.return_value = mock_assistant
        mock_client_class.return_value = mock_client
        
        agent = OrderProcessingAgentV2(mock_db)
        
        assert agent.client is not None
        assert agent.assistant is not None
        assert agent.is_initialized
    
    @pytest.mark.asyncio
    async def test_process_order_without_initialization(self, agent):
        """Test order processing when agent is not initialized"""
        agent.is_initialized = False
        
        result = await agent.process_order("test_order")
        
        assert not result['success']
        assert "not initialized" in result['error']
    
    def test_sync_function_wrappers(self, agent):
        """Test that sync wrapper functions work correctly"""
        # Mock the processor
        agent.processor = Mock()
        agent.processor.get_order_summary = AsyncMock(return_value={"test": "data"})
        
        result = agent._get_order_summary_sync("test_order")
        
        # Should return JSON string
        assert isinstance(result, str)
        assert "test" in result
```

## Troubleshooting Common Issues

### 1. Azure AI Packages Not Found

```bash
# Install specific versions if needed
pip install azure-ai-projects==1.0.0b1
pip install azure-identity==1.16.0
```

### 2. Authentication Issues

```bash
# Check Azure CLI login
az account show

# Test authentication
az cognitiveservices account show --name your-resource-name --resource-group your-rg
```

### 3. Environment Variables

Create a test script to verify environment variables:

```python
import os

required_vars = [
    'PROJECT_ENDPOINT',
    'AZURE_OPENAI_DEPLOYMENT_NAME',
    'AZURE_OPENAI_ENDPOINT'
]

print("Environment Variables Check:")
for var in required_vars:
    value = os.getenv(var)
    print(f"{var}: {'✅ Set' if value else '❌ Missing'}")
    if value:
        print(f"  Value: {value[:50]}{'...' if len(value) > 50 else ''}")
```

### 4. Function Tool Issues

If function tools aren't working:

1. Check that all wrapper functions are synchronous
2. Verify the function definitions are properly formatted
3. Ensure the processor methods exist and are accessible

### 5. Database Connection Issues

```python
# Test database connection separately
from app.database.session import get_db

try:
    db = next(get_db())
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
```

## Testing Checklist

- [ ] Azure AI packages installed
- [ ] Environment variables configured
- [ ] Azure authentication working
- [ ] Database connection available
- [ ] Agent initializes successfully
- [ ] Function tools are defined correctly
- [ ] Individual functions work
- [ ] Complete order processing works
- [ ] Error handling works correctly
- [ ] Status reporting is accurate

## Expected Outputs

### Successful Initialization
```
✅ Agent initialized successfully!
Assistant ID: asst_xxx...
```

### Function Test Results
```
Testing _get_order_summary_sync...
Result: {"success": true, "order": {...}}
```

### Order Processing
```
✅ Order processing completed successfully!
Assistant Response: ['I'll help you process this order...', '...']
```

## Next Steps

After successful testing:

1. **Integration**: Integrate the agent into your API endpoints
2. **Monitoring**: Add logging and monitoring for production use
3. **Performance**: Test with real order data and measure performance
4. **Error Handling**: Test edge cases and error scenarios
5. **Documentation**: Update API documentation with new capabilities
