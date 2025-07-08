# Azure AI Foundry Migration Guide

## Overview

The `order_processing_assistant_v2.py` has been updated to follow the official Microsoft Azure AI Foundry documentation pattern, transitioning from the direct OpenAI SDK to the Azure AI Foundry Agents API.

## Key Changes Made

### 1. Import Updates
- **From**: `from openai import AzureOpenAI`
- **To**: `from azure.ai.projects import AIProjectClient`
- **Added**: `from azure.ai.agents.models import FunctionTool, RequiredFunctionToolCall, SubmitToolOutputsAction, ToolOutput`

### 2. Client Initialization
- **From**: `AzureOpenAI(api_key=..., api_version=..., azure_endpoint=...)`
- **To**: `AIProjectClient(endpoint=..., credential=DefaultAzureCredential(), api_version="latest")`

### 3. Authentication Method
- **From**: API key-based authentication
- **To**: Azure DefaultAzureCredential (more secure, supports managed identity)

### 4. Assistant Creation
- **From**: `client.beta.assistants.create(...)`
- **To**: `client.agents.create_agent(...)`

### 5. Function Tool Definition
- **From**: Manual JSON schema definition for function tools
- **To**: `FunctionTool(functions=user_functions)` with automatic schema generation

### 6. Thread and Message Management
- **From**: `client.beta.threads.create()` and `client.beta.threads.messages.create()`
- **To**: `client.agents.threads.create()` and `client.agents.messages.create()`

### 7. Run Processing
- **From**: Manual polling with `client.beta.threads.runs.create()` and status checking
- **To**: `client.agents.runs.create_and_process()` for automatic function call handling

### 8. Function Execution
- **From**: Manual function routing based on function name
- **To**: `FunctionTool.execute(tool_call)` for automatic function execution

## Environment Variables Required

The updated implementation requires:

1. `PROJECT_ENDPOINT` - Azure AI Foundry project endpoint (or falls back to `AZURE_OPENAI_ENDPOINT`)
2. `AZURE_OPENAI_DEPLOYMENT_NAME` - Model deployment name

Note: API keys are no longer required as authentication is handled via Azure DefaultAzureCredential.

## Function Changes

### User Functions
All user functions have been converted to synchronous wrapper functions to work with the `FunctionTool` pattern:
- `_get_order_summary_sync()`
- `_parse_order_file_sync()`
- `_validate_order_data_sync()`
- `_process_email_workflow_sync()`
- `_process_sku_items_sync()`
- `_calculate_logistics_sync()`
- `_apply_corrections_sync()`

These wrappers handle the async-to-sync conversion required by the Azure AI Foundry pattern.

## Error Handling

The implementation includes robust error handling:
- Graceful fallback when Azure AI packages aren't installed
- Package availability detection with `AZURE_AI_AVAILABLE` flag
- Detailed error reporting in the `get_status()` method

## Benefits of Azure AI Foundry Pattern

1. **Better Integration**: Native Azure integration with better security
2. **Simplified Function Calling**: Automatic schema generation and execution
3. **Enhanced Reliability**: Built-in retry and error handling
4. **Future-Proof**: Follows Microsoft's recommended patterns for Azure AI
5. **Better Monitoring**: Integration with Azure monitoring and logging
6. **Security**: Uses Azure managed identity instead of API keys

## Installation

The required packages are already in `requirements.txt`:
```
azure-ai-projects>=1.0.0b4
azure-identity>=1.15.0
azure-core>=1.29.0
azure-ai-inference>=1.0.0b1
```

To install:
```bash
pip install -r requirements.txt
```

## Testing

The updated assistant maintains the same interface:
```python
assistant = OrderProcessingAgentV2(db)
result = await assistant.process_order(order_id, user_message)
status = assistant.get_status()
```

## Migration Notes

- The old OpenAI SDK-based code is completely replaced
- All function signatures remain the same for backward compatibility
- Enhanced error reporting provides better debugging information
- The assistant supports both manual and automatic function execution modes

## References

- [Azure AI Foundry Functions Calling Sample](https://github.com/azure-ai-foundry/foundry-samples/blob/main/samples/microsoft/python/getting-started-agents/functions_calling.py)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-services/)
- [Azure AI Agents Python SDK](https://pypi.org/project/azure-ai-projects/)
