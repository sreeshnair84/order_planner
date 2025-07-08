"""
Order Processing Agent using Azure AI Foundry Agents API
Following Microsoft Azure AI Foundry documentation pattern.
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from azure.identity import DefaultAzureCredential
    from azure.ai.projects import AIProjectClient
    from azure.ai.agents.models import FunctionTool, RequiredFunctionToolCall, SubmitToolOutputsAction, ToolOutput
    AZURE_AI_AVAILABLE = True
except ImportError:
    # Fallback for development/testing when Azure AI packages aren't installed
    DefaultAzureCredential = None
    AIProjectClient = None
    FunctionTool = None
    RequiredFunctionToolCall = None
    SubmitToolOutputsAction = None
    ToolOutput = None
    AZURE_AI_AVAILABLE = False

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    AsyncSession = None
    SQLALCHEMY_AVAILABLE = False

from app.utils.config import settings
from app.services.unified_order_processor import UnifiedOrderProcessor

logger = logging.getLogger(__name__)


class OrderProcessingAgentV2:
    """
    Azure AI Foundry Agents-based Order Processing Agent
    
    Follows the official Microsoft Azure AI Foundry documentation pattern
    using the AIProjectClient with Azure endpoints.
    """
    
    def __init__(self, db):
        self.db = db
        self.processor = UnifiedOrderProcessor(db)
        self.client = None
        self.assistant = None
        self.is_initialized = False
        
        # Initialize the Azure AI Project client
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Azure AI Project client"""
        if not AZURE_AI_AVAILABLE:
            logger.warning("Azure AI Foundry packages not available - agent functionality disabled")
            return
            
        try:
            # Check for required environment variables
            endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING") or settings.AZURE_AI_PROJECT_CONNECTION_STRING
            deployment = settings.AZURE_OPENAI_DEPLOYMENT_NAME
            
            if not all([endpoint, deployment]):
                logger.warning("Azure AI Project configuration incomplete")
                return
            
            # Create the client
            self.client = AIProjectClient(
                endpoint=endpoint,
                credential=DefaultAzureCredential(),
            )
            
            # Create or get the assistant
            self._setup_assistant()
            
            if self.assistant:
                self.is_initialized = True
                logger.info(f"Order Processing Assistant initialized: {self.assistant.id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure AI Project client: {str(e)}")
            self.client = None
            self.assistant = None
    
    def _setup_assistant(self):
        """Create or retrieve the order processing assistant"""
        if not self.client or not AZURE_AI_AVAILABLE:
            return
        
        try:
            # Create the assistant using the new Azure AI Foundry pattern
            self.assistant = self.client.agents.create_agent(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                name="Order Processing Assistant",
                instructions="""
                You are an expert FMCG Order Processing Assistant. Your role is to help process retail orders efficiently and accurately.
                
                **Your Workflow:**
                1. Always start by getting the order summary to understand current status
                2. Parse order files when needed
                3. Validate order data thoroughly
                4. Generate emails for missing information
                5. Process SKU items and calculate totals
                6. Calculate logistics and shipping costs
                7. Apply any necessary corrections
                
                **Guidelines:**
                - Be thorough in validation - check for missing SKUs, quantities, contact info, delivery addresses
                - For missing information, be specific about what fields are needed
                - Always provide clear explanations of what you're doing and why
                - Update the user on progress at each major step
                - If any step fails, provide clear error messages and suggested next steps
                
                **Error Handling:**
                - If a function fails, explain what went wrong
                - Suggest alternative approaches when possible
                - Always prioritize data accuracy and completeness
                
                Be professional, thorough, and focus on helping users process orders successfully.
                """,
                tools=self._get_function_tools()
            )
            
            logger.info(f"Created assistant: {self.assistant.id}")
            
        except Exception as e:
            logger.error(f"Failed to create assistant: {str(e)}")
            self.assistant = None
    
    def _get_function_tools(self):
        """Get function tool definitions for the assistant"""
        if not AZURE_AI_AVAILABLE:
            return []
            
        # Define function tools according to Azure AI Foundry specification
        function_tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_order_summary",
                    "description": "Get comprehensive order summary and current status",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "The order ID to get summary for"
                            }
                        },
                        "required": ["order_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "parse_order_file",
                    "description": "Parse uploaded order file and extract structured data",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "The order ID to parse file for"
                            }
                        },
                        "required": ["order_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "validate_order_data",
                    "description": "Validate order data for completeness and accuracy",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "The order ID to validate"
                            }
                        },
                        "required": ["order_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "process_email_workflow",
                    "description": "Generate and send emails for missing information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "The order ID to process emails for"
                            },
                            "missing_fields": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of missing fields to request in email"
                            }
                        },
                        "required": ["order_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "process_sku_items",
                    "description": "Process and validate SKU items, calculate totals",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "The order ID to process SKU items for"
                            }
                        },
                        "required": ["order_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_logistics",
                    "description": "Calculate shipping costs and logistics requirements",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "The order ID to calculate logistics for"
                            },
                            "shipping_method": {
                                "type": "string",
                                "description": "Shipping method (STANDARD, EXPRESS, OVERNIGHT)",
                                "default": "STANDARD"
                            }
                        },
                        "required": ["order_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "apply_corrections",
                    "description": "Apply corrections to order data",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "The order ID to apply corrections to"
                            },
                            "corrections": {
                                "type": "object",
                                "description": "Dictionary of corrections to apply"
                            }
                        },
                        "required": ["order_id", "corrections"]
                    }
                }
            }
        ]
        
        return function_tools
    
    # Synchronous wrapper functions for the FunctionTool
    def _get_order_summary_sync(self, order_id: str) -> str:
        """Get comprehensive order summary and current status"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, we need to handle this differently
                result = asyncio.run_coroutine_threadsafe(
                    self.processor.get_order_summary(order_id), loop
                ).result()
            else:
                result = asyncio.run(self.processor.get_order_summary(order_id))
            return json.dumps(result, default=str)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    def _parse_order_file_sync(self, order_id: str) -> str:
        """Parse uploaded order file and extract structured data"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                result = asyncio.run_coroutine_threadsafe(
                    self.processor.process_file_parsing(order_id), loop
                ).result()
            else:
                result = asyncio.run(self.processor.process_file_parsing(order_id))
            return json.dumps(result, default=str)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    def _validate_order_data_sync(self, order_id: str) -> str:
        """Validate order data for completeness and accuracy"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                result = asyncio.run_coroutine_threadsafe(
                    self.processor.process_validation(order_id), loop
                ).result()
            else:
                result = asyncio.run(self.processor.process_validation(order_id))
            return json.dumps(result, default=str)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    def _process_email_workflow_sync(self, order_id: str, missing_fields: List[str] = None) -> str:
        """Generate and send emails for missing information"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            
            async def _execute():
                if missing_fields:
                    validation_result = {"is_valid": False, "missing_fields": missing_fields}
                else:
                    validation_result = await self.processor.process_validation(order_id)
                return await self.processor.process_email_workflow(order_id, validation_result)
            
            if loop.is_running():
                result = asyncio.run_coroutine_threadsafe(_execute(), loop).result()
            else:
                result = asyncio.run(_execute())
            return json.dumps(result, default=str)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    def _process_sku_items_sync(self, order_id: str) -> str:
        """Process and validate SKU items, calculate totals"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                result = asyncio.run_coroutine_threadsafe(
                    self.processor.process_sku_items(order_id), loop
                ).result()
            else:
                result = asyncio.run(self.processor.process_sku_items(order_id))
            return json.dumps(result, default=str)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    def _calculate_logistics_sync(self, order_id: str, shipping_method: str = "STANDARD") -> str:
        """Calculate shipping costs and logistics requirements"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                result = asyncio.run_coroutine_threadsafe(
                    self.processor.process_logistics(order_id, shipping_method), loop
                ).result()
            else:
                result = asyncio.run(self.processor.process_logistics(order_id, shipping_method))
            return json.dumps(result, default=str)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    def _apply_corrections_sync(self, order_id: str, corrections: Dict[str, Any]) -> str:
        """Apply corrections to order data"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                result = asyncio.run_coroutine_threadsafe(
                    self.processor.apply_corrections(order_id, corrections, "ai_assistant"), loop
                ).result()
            else:
                result = asyncio.run(self.processor.apply_corrections(order_id, corrections, "ai_assistant"))
            return json.dumps(result, default=str)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    async def process_order(self, order_id: str, user_message: str = None) -> Dict[str, Any]:
        """
        Process an order using the assistant
        
        Args:
            order_id: The order ID to process
            user_message: Optional user message, defaults to complete processing request
        """
        if not AZURE_AI_AVAILABLE:
            return {
                "success": False,
                "error": "Azure AI Foundry packages not available"
            }
            
        if not self.is_initialized:
            return {
                "success": False,
                "error": "Assistant not initialized"
            }
        
        try:
            # Default message for complete order processing
            if not user_message:
                user_message = f"""
                Please process order {order_id} completely. Follow your standard workflow:
                
                1. Get the order summary first
                2. Parse the order file if needed
                3. Validate the order data
                4. Generate emails for any missing information
                5. Process SKU items
                6. Calculate logistics
                7. Apply any necessary corrections
                
                Please be thorough and provide detailed feedback at each step.
                """
            
            # Create a thread using Azure AI Foundry pattern
            thread = self.client.agents.threads.create()
            
            # Add the user message
            self.client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_message
            )
            
            # Create the run
            run = self.client.agents.runs.create(
                thread_id=thread.id,
                agent_id=self.assistant.id
            )
            
            # Process the run with function call handling
            max_iterations = 10
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Wait for the run to complete or require action
                while run.status in ["queued", "in_progress"]:
                    time.sleep(1)
                    run = self.client.agents.runs.retrieve(thread_id=thread.id, run_id=run.id)
                
                # Check if run completed successfully
                if run.status == "completed":
                    break
                
                # Handle function calls
                elif run.status == "requires_action":
                    if hasattr(run, 'required_action') and run.required_action:
                        tool_calls = run.required_action.submit_tool_outputs.tool_calls
                        tool_outputs = []
                        
                        for tool_call in tool_calls:
                            function_name = tool_call.function.name
                            function_args = json.loads(tool_call.function.arguments)
                            
                            # Execute the function call
                            try:
                                result = await self._execute_function_call(function_name, function_args)
                                tool_outputs.append({
                                    "tool_call_id": tool_call.id,
                                    "output": json.dumps(result, default=str)
                                })
                            except Exception as e:
                                logger.error(f"Error executing function {function_name}: {str(e)}")
                                tool_outputs.append({
                                    "tool_call_id": tool_call.id,
                                    "output": json.dumps({"success": False, "error": str(e)})
                                })
                        
                        # Submit the tool outputs
                        run = self.client.agents.runs.submit_tool_outputs(
                            thread_id=thread.id,
                            run_id=run.id,
                            tool_outputs=tool_outputs
                        )
                
                elif run.status == "failed":
                    error_msg = f"Run failed with status: {run.status}"
                    if hasattr(run, 'last_error') and run.last_error:
                        error_msg += f" - {run.last_error}"
                    
                    return {
                        "success": False,
                        "error": error_msg,
                        "thread_id": thread.id,
                        "run_id": run.id
                    }
                
                else:
                    break
            
            # Get the final messages
            messages = self.client.agents.messages.list(thread_id=thread.id)
            
            # Format the response
            assistant_messages = []
            for message in messages.data:
                if message.role == "assistant":
                    for content_part in message.content:
                        if content_part.type == "text":
                            assistant_messages.append(content_part.text.value)
            
            return {
                "success": True,
                "thread_id": thread.id,
                "run_id": run.id,
                "response": assistant_messages,
                "status": run.status
            }
        
        except Exception as e:
            logger.error(f"Error processing order: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_function_call(self, function_name: str, function_args: dict) -> dict:
        """Execute a function call from the assistant"""
        try:
            if function_name == "get_order_summary":
                return await self.processor.get_order_summary(function_args["order_id"])
            
            elif function_name == "parse_order_file":
                return await self.processor.process_file_parsing(function_args["order_id"])
            
            elif function_name == "validate_order_data":
                return await self.processor.process_validation(function_args["order_id"])
            
            elif function_name == "process_email_workflow":
                missing_fields = function_args.get("missing_fields")
                if missing_fields:
                    validation_result = {"is_valid": False, "missing_fields": missing_fields}
                else:
                    validation_result = await self.processor.process_validation(function_args["order_id"])
                return await self.processor.process_email_workflow(function_args["order_id"], validation_result)
            
            elif function_name == "process_sku_items":
                return await self.processor.process_sku_items(function_args["order_id"])
            
            elif function_name == "calculate_logistics":
                shipping_method = function_args.get("shipping_method", "STANDARD")
                return await self.processor.process_logistics(function_args["order_id"], shipping_method)
            
            elif function_name == "apply_corrections":
                return await self.processor.apply_corrections(
                    function_args["order_id"], 
                    function_args["corrections"], 
                    "ai_assistant"
                )
            
            else:
                return {"success": False, "error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get assistant status"""
        return {
            "azure_ai_available": AZURE_AI_AVAILABLE,
            "sqlalchemy_available": SQLALCHEMY_AVAILABLE,
            "initialized": self.is_initialized,
            "client_available": self.client is not None,
            "assistant_available": self.assistant is not None,
            "assistant_id": self.assistant.id if self.assistant else None,
            "model": settings.AZURE_OPENAI_DEPLOYMENT_NAME if self.assistant else None
        }


async def create_order_processing_assistant(db) -> OrderProcessingAgentV2:
    """Factory function to create the assistant"""
    return OrderProcessingAgentV2(db)


async def process_order_with_assistant(db, order_id: str, user_message: str = None) -> Dict[str, Any]:
    """Convenience function to process an order with the assistant"""
    assistant = await create_order_processing_assistant(db)
    return await assistant.process_order(order_id, user_message)
