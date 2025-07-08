# Order Processing Agent Testing Guide

## 🎯 Quick Start Testing

### 1. Environment Check
```bash
cd backend
python test_agent_simple.py
```

### 2. Current Status ✅
Based on the test results:
- ✅ Database models working
- ✅ Configuration working  
- ✅ API components working
- ✅ Agent service (mock mode) working
- ❌ Azure AI packages need update

## 🔧 Fix Azure AI Package Issues

### Update Azure AI Packages
```bash
pip install --upgrade azure-ai-projects
pip install azure-ai-agents
```

Or install from requirements:
```bash
pip install -r requirements.txt --upgrade
```

### Alternative: Use Mock Mode (Recommended for Testing)
The agent already has full mock support built-in. This works perfectly for testing without Azure AI.

## 🧪 Testing Methods

### Method 1: Mock Testing (No Azure Required)
```bash
# Run basic tests
python test_agent_simple.py

# Test the AI service in mock mode
python -c "
import asyncio
from app.services.ai_foundry_agent_service import OrderProcessingAgentService

async def test():
    service = OrderProcessingAgentService(None)
    status = await service.get_agent_status()
    print('Agent Status:', status)
    
asyncio.run(test())
"
```

### Method 2: Database Testing (With Real Database)
```bash
# First setup database
python scripts/setup_database.py

# Then run full tests
python test_agent.py
```

### Method 3: API Testing (With Server Running)
```bash
# Start the server
python -m uvicorn app.main:app --reload

# In another terminal, test the API
curl -X GET http://localhost:8000/api/ai-agent/status
```

## 📊 Test Results Explanation

### ✅ Working Components
1. **AI Service** - Works in mock mode, will auto-detect Azure AI when available
2. **Database Models** - All order, tracking, and SKU models working
3. **Configuration** - Environment variables and settings working
4. **API Components** - FastAPI routes and middleware working

### ⚠️ Azure AI Dependencies
The agent uses fallback patterns:
- **Without Azure AI**: Works in mock mode for development/testing
- **With Azure AI**: Full agent functionality with real AI processing

## 🚀 Production Usage

### For Development/Testing:
```python
from app.services.ai_foundry_agent_service import OrderProcessingAgentService

# Create service (will use mock if Azure not available)
service = OrderProcessingAgentService(db_session)

# Test order processing
result = await service.process_order_completely(order_id, order_number)
```

### For Production with Azure AI:
1. Set up Azure AI Project
2. Add `AZURE_AI_PROJECT_CONNECTION_STRING` to environment
3. Install latest Azure AI packages
4. Agent will automatically use real Azure AI

## 📋 API Endpoints Available

### Agent Status
```bash
GET /api/ai-agent/status
```

### Process Order
```bash
POST /api/ai-agent/orders/{order_id}/process
```

### Process Order Step
```bash
POST /api/ai-agent/orders/{order_id}/steps/{step_name}
```

### Get Thread State
```bash
GET /api/ai-agent/orders/{order_id}/threads
```

## 🔍 Troubleshooting

### Issue: Azure AI Import Errors
**Solution**: Use mock mode or update packages
```bash
pip install --upgrade azure-ai-projects azure-ai-agents
```

### Issue: Database Connection Errors
**Solution**: Setup database first
```bash
python scripts/setup_database.py
```

### Issue: Agent Not Initialized
**Solution**: Check environment variables or use mock mode
```bash
# Check config
python -c "from app.utils.config import settings; print(settings.AZURE_AI_PROJECT_CONNECTION_STRING)"
```

## 🎉 Next Steps

1. **For Development**: Use mock mode, it works perfectly
2. **For Testing**: Run `python test_agent_simple.py`
3. **For Production**: Set up Azure AI and update packages
4. **For Integration**: Use the API endpoints shown above

The agent is fully functional in mock mode and ready for development and testing!
