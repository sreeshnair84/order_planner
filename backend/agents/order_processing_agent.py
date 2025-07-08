"""
Simplified Order Processing Agent using Azure AI Foundry
Uses the UnifiedOrderProcessor to eliminate code duplication.

This agent provides a streamlined interface for:
- Complete order processing workflow
- Individual step processing
- Error handling and retries
- Status monitoring
"""

import json
import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    Agent, AgentThread, ThreadMessage, ThreadRun,
    RunStatus, MessageRole, ToolSet, FunctionTool,
    SubmitToolOutputsAction, RequiredAction
)
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError, AzureError
from app.utils.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.unified_order_processor import UnifiedOrderProcessor

logger = logging.getLogger(__name__)

# Agent configuration constants
AGENT_NAME = "OrderProcessingAgent"
AGENT_DESCRIPTION = "Streamlined FMCG order processing agent with unified processing"
MAX_POLL_ITERATIONS = 60  # 2 minutes with 2-second intervals
POLL_INTERVAL = 2.0  # seconds

class OrderProcessingTools:
    """
    Simplified order processing tools using UnifiedOrderProcessor.
    Eliminates code duplication by delegating to the unified processor.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.processor = UnifiedOrderProcessor(db)
        self._tool_registry: Dict[str, Callable] = {
            "process_order_complete": self.process_order_complete,
            "parse_order_file": self.parse_order_file,
            "validate_order_data": self.validate_order_data,
            "process_email_workflow": self.process_email_workflow,
            "process_sku_items": self.process_sku_items,
            "calculate_logistics": self.calculate_logistics,
            "get_order_summary": self.get_order_summary,
            "retry_processing_step": self.retry_processing_step,
            "apply_corrections": self.apply_corrections
        }
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with error handling and logging"""
        start_time = time.time()
        
        try:
            if tool_name not in self._tool_registry:
                return self._create_error_result(f"Unknown tool: {tool_name}")
            
            logger.info(f"Executing tool '{tool_name}' with args: {arguments}")
            
            # Execute the tool
            result = await self._tool_registry[tool_name](**arguments)
            
            # Add execution metadata
            result["execution_time"] = round(time.time() - start_time, 2)
            result["tool_name"] = tool_name
            result["timestamp"] = datetime.utcnow().isoformat()
            
            logger.info(f"Tool '{tool_name}' completed in {result['execution_time']}s")
            return result
            
        except Exception as e:
            error_result = self._create_error_result(f"Tool execution failed: {str(e)}")
            error_result["tool_name"] = tool_name
            error_result["execution_time"] = round(time.time() - start_time, 2)
            logger.error(f"Tool '{tool_name}' failed: {str(e)}")
            return error_result
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error result"""
        return {
            "success": False,
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # ============== UNIFIED PROCESSOR DELEGATES ==============
    
    async def process_order_complete(self, order_id: str) -> Dict[str, Any]:
        """Complete order processing workflow"""
        try:
            return await self.processor.process_order_complete(order_id)
        except Exception as e:
            logger.error(f"Complete processing failed: {str(e)}")
            return self._create_error_result(str(e))
    
    async def parse_order_file(self, order_id: str) -> Dict[str, Any]:
        """Parse order file"""
        try:
            return await self.processor.process_file_parsing(order_id)
        except Exception as e:
            logger.error(f"File parsing failed: {str(e)}")
            return self._create_error_result(str(e))
    
    async def validate_order_data(self, order_id: str, validation_type: str = "completeness") -> Dict[str, Any]:
        """Validate order data"""
        try:
            return await self.processor.process_validation(order_id)
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            return self._create_error_result(str(e))
    
    async def process_email_workflow(self, order_id: str, missing_fields: List[str] = None) -> Dict[str, Any]:
        """Process unified email workflow (generate + send)"""
        try:
            # Get validation result first if missing_fields provided
            if missing_fields:
                validation_result = {"is_valid": False, "missing_fields": missing_fields}
            else:
                validation_result = await self.processor.process_validation(order_id)
            
            return await self.processor.process_email_workflow(order_id, validation_result)
        except Exception as e:
            logger.error(f"Email workflow failed: {str(e)}")
            return self._create_error_result(str(e))
    
    async def process_sku_items(self, order_id: str, auto_correct: bool = False) -> Dict[str, Any]:
        """Process SKU items"""
        try:
            return await self.processor.process_sku_items(order_id)
        except Exception as e:
            logger.error(f"SKU processing failed: {str(e)}")
            return self._create_error_result(str(e))
    
    async def calculate_logistics(self, order_id: str, shipping_method: str = "STANDARD") -> Dict[str, Any]:
        """Calculate logistics"""
        try:
            return await self.processor.process_logistics(order_id, shipping_method)
        except Exception as e:
            logger.error(f"Logistics calculation failed: {str(e)}")
            return self._create_error_result(str(e))
    
    async def get_order_summary(self, order_id: str) -> Dict[str, Any]:
        """Get order summary"""
        try:
            return await self.processor.get_order_summary(order_id)
        except Exception as e:
            logger.error(f"Get order summary failed: {str(e)}")
            return self._create_error_result(str(e))
    
    async def retry_processing_step(self, order_id: str, step_name: str, max_retries: int = 3) -> Dict[str, Any]:
        """Retry a processing step"""
        try:
            return await self.processor.retry_processing_step(order_id, step_name)
        except Exception as e:
            logger.error(f"Retry step failed: {str(e)}")
            return self._create_error_result(str(e))
    
    async def apply_corrections(self, order_id: str, corrections: Dict[str, Any], user_id: str = "ai_agent") -> Dict[str, Any]:
        """Apply corrections to order data"""
        try:
            return await self.processor.apply_corrections(order_id, corrections, user_id)
        except Exception as e:
            logger.error(f"Apply corrections failed: {str(e)}")
            return self._create_error_result(str(e))


class OrderProcessingAgent:
    """
    Azure AI Foundry Order Processing Agent
    
    This agent orchestrates the complete order processing workflow using Azure AI Foundry's
    function calling capabilities with comprehensive error handling and state management.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tools = OrderProcessingTools(db)
        self.client: Optional[AIProjectClient] = None
        self.agent: Optional[Agent] = None
        self.is_initialized = False
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Azure AI Project client and agent with error handling"""
        try:
            if not settings.AZURE_AI_PROJECT_CONNECTION_STRING:
                logger.warning("Azure AI Project connection string not configured")
                return
            
            # Initialize client with retry logic
            credential = DefaultAzureCredential()
            self.client = AIProjectClient.from_connection_string(
                conn_str=settings.AZURE_AI_PROJECT_CONNECTION_STRING,
                credential=credential
            )
            
            # Setup the agent with tools
            self._setup_agent()
            
            if self.agent:
                self.is_initialized = True
                logger.info(f"Order Processing Agent initialized successfully with ID: {self.agent.id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Order Processing Agent: {str(e)}")
            self.client = None
            self.agent = None
            self.is_initialized = False
    
    def _setup_agent(self):
        """Setup the order processing agent with comprehensive tool definitions"""
        if not self.client:
            logger.warning("Cannot setup agent: client not initialized")
            return
        
        try:
            # Define comprehensive function tools
            function_tools = [
                FunctionTool(
                    name="get_order_summary",
                    description="Get comprehensive order summary and current state",
                    parameters={
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "Order ID to get summary for"
                            }
                        },
                        "required": ["order_id"]
                    }
                ),
                FunctionTool(
                    name="parse_order_file",
                    description="Parse uploaded order file and extract structured data",
                    parameters={
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "Order ID to process"
                            },
                            "file_path": {
                                "type": "string",
                                "description": "Optional file path override"
                            }
                        },
                        "required": ["order_id"]
                    }
                ),
                FunctionTool(
                    name="validate_order_data",
                    description="Validate order data for completeness, accuracy, and compliance",
                    parameters={
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "Order ID to validate"
                            },
                            "validation_type": {
                                "type": "string",
                                "enum": ["completeness", "accuracy", "compliance"],
                                "description": "Type of validation to perform",
                                "default": "completeness"
                            }
                        },
                        "required": ["order_id"]
                    }
                ),
                FunctionTool(
                    name="generate_missing_info_email",
                    description="Generate email to request missing order information from retailer",
                    parameters={
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "Order ID"
                            },
                            "missing_fields": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of missing fields that need to be requested"
                            },
                            "recipient_email": {
                                "type": "string",
                                "description": "Email address to send request to (optional, will use retailer email from order)"
                            }
                        },
                        "required": ["order_id", "missing_fields"]
                    }
                ),
                FunctionTool(
                    name="process_sku_items",
                    description="Process and validate SKU items, calculate totals",
                    parameters={
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "Order ID to process"
                            },
                            "auto_correct": {
                                "type": "boolean",
                                "description": "Auto-correct minor SKU issues if possible",
                                "default": False
                            }
                        },
                        "required": ["order_id"]
                    }
                ),
                FunctionTool(
                    name="calculate_logistics",
                    description="Calculate shipping costs and logistics requirements",
                    parameters={
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "Order ID"
                            },
                            "shipping_method": {
                                "type": "string",
                                "enum": ["STANDARD", "EXPRESS", "ECONOMY"],
                                "description": "Shipping method to calculate costs for",
                                "default": "STANDARD"
                            }
                        },
                        "required": ["order_id"]
                    }
                ),
                FunctionTool(
                    name="update_order_status",
                    description="Update order processing status with notes",
                    parameters={
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "Order ID"
                            },
                            "status": {
                                "type": "string",
                                "description": "New order status (e.g., PROCESSING, COMPLETED, FAILED, PENDING_INFO)"
                            },
                            "notes": {
                                "type": "string",
                                "description": "Status update notes or reason for change"
                            }
                        },
                        "required": ["order_id", "status"]
                    }
                ),
                FunctionTool(
                    name="retry_failed_step",
                    description="Retry a failed processing step with improved error handling",
                    parameters={
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "Order ID"
                            },
                            "step_name": {
                                "type": "string",
                                "enum": ["parse", "validate", "sku_processing", "logistics"],
                                "description": "Name of the step to retry"
                            },
                            "max_retries": {
                                "type": "integer",
                                "description": "Maximum number of retry attempts",
                                "default": 3,
                                "minimum": 1,
                                "maximum": 5
                            }
                        },
                        "required": ["order_id", "step_name"]
                    }
                )
            ]
            
            # Create toolset
            toolset = ToolSet()
            for tool in function_tools:
                toolset.add(tool)
            
            # Enhanced agent instructions
            instructions = """
            You are an expert Order Processing Agent for FMCG/retail order management.
            
            Your primary workflow should follow these steps:
            
            1. **Order Assessment**: Always start by getting the order summary to understand current state
            2. **File Processing**: Parse uploaded order files (CSV, XML, Excel, etc.)
            3. **Data Validation**: Thoroughly validate order data for completeness and accuracy
            4. **Issue Resolution**: If missing information is found, generate appropriate emails to retailers
            5. **SKU Processing**: Process all SKU items, validate quantities, and calculate totals
            6. **Logistics Calculation**: Calculate shipping costs and delivery requirements
            7. **Status Management**: Keep order status updated throughout the process
            8. **Error Handling**: Use retry capabilities for failed steps
            
            **Important Guidelines:**
            - Always start with get_order_summary to understand the current state
            - Be thorough in validation - check for missing SKUs, quantities, contact info, addresses
            - For missing information, be specific about what fields are needed in emails
            - Use auto_correct sparingly for SKU processing - only for obvious typos
            - Update status at each major step to provide visibility
            - If a step fails, try to understand why and use retry_failed_step if appropriate
            - Provide detailed explanations of what you're doing and why
            - Always include order_number in your responses when available
            
            **Error Recovery:**
            - If any tool fails, analyze the error and try alternative approaches
            - Use retry_failed_step for transient failures
            - Update status to appropriate error states when needed
            - Provide clear explanations of what went wrong and suggested next steps
            
            Be professional, thorough, and always prioritize data accuracy and completeness.
            """
            
            # Try to get existing agent or create new one
            try:
                agents = self.client.agents.list_agents()
                existing_agent = None
                for agent in agents.data:
                    if agent.name == AGENT_NAME:
                        existing_agent = agent
                        break
                
                if existing_agent:
                    # Update existing agent with latest tools and instructions
                    self.agent = self.client.agents.update_agent(
                        assistant_id=existing_agent.id,
                        model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                        name=AGENT_NAME,
                        instructions=instructions,
                        toolset=toolset,
                        temperature=settings.AI_AGENT_TEMPERATURE,
                        description=AGENT_DESCRIPTION
                    )
                    logger.info(f"Updated existing agent: {self.agent.id}")
                else:
                    # Create new agent
                    self.agent = self.client.agents.create_agent(
                        model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                        name=AGENT_NAME,
                        instructions=instructions,
                        toolset=toolset,
                        temperature=settings.AI_AGENT_TEMPERATURE,
                        description=AGENT_DESCRIPTION
                    )
                    logger.info(f"Created new agent: {self.agent.id}")
                    
            except Exception as e:
                logger.error(f"Failed to setup agent: {str(e)}")
                self.agent = None
                
        except Exception as e:
            logger.error(f"Failed to setup agent tools: {str(e)}")
            self.agent = None
    
    async def create_thread(self, initial_message: str = None, metadata: Dict[str, Any] = None) -> Optional[AgentThread]:
        """Create a new agent thread with improved error handling"""
        if not self.is_initialized:
            logger.error("Agent not initialized - cannot create thread")
            return None
        
        try:
            # Create thread with optional metadata
            thread_options = {}
            if metadata:
                thread_options["metadata"] = metadata
            
            thread = self.client.agents.create_thread(**thread_options)
            
            # Add initial message if provided
            if initial_message:
                self.client.agents.create_message(
                    thread_id=thread.id,
                    role=MessageRole.USER,
                    content=initial_message
                )
                logger.info(f"Created thread {thread.id} with initial message")
            else:
                logger.info(f"Created empty thread {thread.id}")
            
            return thread
            
        except AzureError as e:
            logger.error(f"Azure error creating thread: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating thread: {str(e)}")
            return None
    
    async def add_message_to_thread(self, thread_id: str, message: str, role: MessageRole = MessageRole.USER) -> bool:
        """Add a message to an existing thread"""
        if not self.is_initialized:
            logger.error("Agent not initialized")
            return False
        
        try:
            self.client.agents.create_message(
                thread_id=thread_id,
                role=role,
                content=message
            )
            logger.info(f"Added message to thread {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add message to thread: {str(e)}")
            return False
    
    async def run_agent(self, thread_id: str, additional_instructions: str = None, timeout_seconds: int = 120) -> Dict[str, Any]:
        """
        Run the agent on a thread with comprehensive error handling and timeout management
        
        Args:
            thread_id: The thread ID to run the agent on
            additional_instructions: Optional additional instructions for this run
            timeout_seconds: Maximum time to wait for completion (default 2 minutes)
        
        Returns:
            Dict containing success status, results, and metadata
        """
        if not self.is_initialized:
            return self._create_run_error("Agent not initialized")
        
        start_time = time.time()
        
        try:
            # Create run with optional additional instructions
            run_params = {
                "thread_id": thread_id,
                "assistant_id": self.agent.id
            }
            
            if additional_instructions:
                run_params["additional_instructions"] = additional_instructions
            
            run = self.client.agents.create_run(**run_params)
            logger.info(f"Created run {run.id} for thread {thread_id}")
            
            # Poll for completion with timeout
            max_iterations = timeout_seconds // POLL_INTERVAL
            iteration = 0
            
            while iteration < max_iterations:
                elapsed_time = time.time() - start_time
                
                if elapsed_time > timeout_seconds:
                    logger.warning(f"Run {run.id} timed out after {elapsed_time:.1f}s")
                    return self._create_run_error("Agent execution timed out", {
                        "run_id": run.id,
                        "elapsed_time": elapsed_time
                    })
                
                try:
                    # Get current run status
                    run_status = self.client.agents.get_run(thread_id=thread_id, run_id=run.id)
                    
                    if run_status.status == RunStatus.COMPLETED:
                        # Get all messages from the thread
                        messages = self.client.agents.list_messages(thread_id=thread_id)
                        
                        # Process and format messages
                        formatted_messages = []
                        for msg in messages.data:
                            try:
                                content = ""
                                if msg.content and len(msg.content) > 0:
                                    # Handle different content types
                                    if hasattr(msg.content[0], 'text'):
                                        content = msg.content[0].text.value
                                    else:
                                        content = str(msg.content[0])
                                
                                formatted_messages.append({
                                    "id": msg.id,
                                    "role": msg.role,
                                    "content": content,
                                    "created_at": msg.created_at,
                                    "thread_id": msg.thread_id
                                })
                            except Exception as msg_error:
                                logger.warning(f"Error processing message {msg.id}: {str(msg_error)}")
                                continue
                        
                        execution_time = time.time() - start_time
                        logger.info(f"Run {run.id} completed successfully in {execution_time:.1f}s")
                        
                        return {
                            "success": True,
                            "status": "COMPLETED",
                            "run_id": run.id,
                            "thread_id": thread_id,
                            "messages": formatted_messages,
                            "execution_time": execution_time,
                            "iterations": iteration + 1
                        }
                    
                    elif run_status.status == RunStatus.REQUIRES_ACTION:
                        # Handle tool calls
                        logger.info(f"Run {run.id} requires action - processing tool calls")
                        
                        tool_outputs = []
                        tools_executed = []
                        
                        if (run_status.required_action and 
                            hasattr(run_status.required_action, 'submit_tool_outputs') and
                            run_status.required_action.submit_tool_outputs.tool_calls):
                            
                            for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
                                try:
                                    function_name = tool_call.function.name
                                    function_args = json.loads(tool_call.function.arguments)
                                    
                                    logger.info(f"Executing tool: {function_name} with args: {function_args}")
                                    
                                    # Execute the tool using our tools class
                                    tool_result = await self.tools.execute_tool(function_name, function_args)
                                    
                                    tool_outputs.append({
                                        "tool_call_id": tool_call.id,
                                        "output": json.dumps(tool_result, default=str)
                                    })
                                    
                                    tools_executed.append({
                                        "name": function_name,
                                        "args": function_args,
                                        "success": tool_result.get("success", False),
                                        "execution_time": tool_result.get("execution_time", 0)
                                    })
                                    
                                except Exception as tool_error:
                                    logger.error(f"Tool execution failed for {tool_call.function.name}: {str(tool_error)}")
                                    
                                    # Provide error output to the agent
                                    tool_outputs.append({
                                        "tool_call_id": tool_call.id,
                                        "output": json.dumps({
                                            "success": False,
                                            "error": str(tool_error),
                                            "tool_name": tool_call.function.name
                                        })
                                    })
                                    
                                    tools_executed.append({
                                        "name": tool_call.function.name,
                                        "args": {},
                                        "success": False,
                                        "error": str(tool_error)
                                    })
                            
                            # Submit all tool outputs
                            if tool_outputs:
                                self.client.agents.submit_tool_outputs_to_run(
                                    thread_id=thread_id,
                                    run_id=run.id,
                                    tool_outputs=tool_outputs
                                )
                                
                                logger.info(f"Submitted {len(tool_outputs)} tool outputs for run {run.id}")
                                
                                # Log tool execution summary
                                successful_tools = sum(1 for t in tools_executed if t.get("success", False))
                                logger.info(f"Tool execution summary: {successful_tools}/{len(tools_executed)} successful")
                    
                    elif run_status.status in [RunStatus.FAILED, RunStatus.CANCELLED, RunStatus.EXPIRED]:
                        error_msg = f"Run failed with status: {run_status.status}"
                        if hasattr(run_status, 'last_error') and run_status.last_error:
                            error_msg += f" - {run_status.last_error}"
                        
                        logger.error(f"Run {run.id} failed: {error_msg}")
                        return self._create_run_error(error_msg, {
                            "run_id": run.id,
                            "status": run_status.status,
                            "elapsed_time": time.time() - start_time
                        })
                    
                    elif run_status.status == RunStatus.IN_PROGRESS:
                        logger.debug(f"Run {run.id} still in progress (iteration {iteration + 1})")
                    
                except Exception as status_error:
                    logger.error(f"Error checking run status: {str(status_error)}")
                    # Continue polling unless it's a critical error
                    if iteration > 3:  # After a few tries, give up
                        return self._create_run_error(f"Repeated errors checking run status: {str(status_error)}")
                
                iteration += 1
                await asyncio.sleep(POLL_INTERVAL)
            
            # If we've reached here, we've timed out
            execution_time = time.time() - start_time
            logger.warning(f"Run {run.id} timed out after {execution_time:.1f}s ({iteration} iterations)")
            
            return self._create_run_error("Agent execution timed out", {
                "run_id": run.id,
                "elapsed_time": execution_time,
                "iterations": iteration
            })
            
        except AzureError as e:
            logger.error(f"Azure error during run: {str(e)}")
            return self._create_run_error(f"Azure service error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during run: {str(e)}")
            return self._create_run_error(f"Unexpected error: {str(e)}")
    
    def _create_run_error(self, error_message: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standardized run error response"""
        result = {
            "success": False,
            "status": "ERROR",
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if metadata:
            result.update(metadata)
        
        return result
    
    async def process_order_complete(self, order_id: str, order_number: str = None) -> Dict[str, Any]:
        """
        Complete order processing workflow using the agent with comprehensive error handling
        
        This is the main entry point for automated order processing that:
        1. Creates an agent thread
        2. Runs the complete processing workflow
        3. Handles errors and retries
        4. Provides detailed feedback
        """
        try:
            if not self.is_initialized:
                return {
                    "success": False,
                    "error": "Agent not initialized. Check Azure AI configuration.",
                    "order_id": order_id
                }
            
            # Create comprehensive initial message for the agent
            initial_message = f"""
            Please process order {order_number or order_id} (ID: {order_id}) using the complete order processing workflow.
            
            Follow these steps systematically:
            
            1. **Order Assessment**: Get the current order summary to understand the starting state
            2. **File Processing**: Parse the uploaded order file to extract structured data
            3. **Data Validation**: Validate the order data for completeness and accuracy
            4. **Missing Information Handling**: If missing information is found, generate appropriate emails to request it
            5. **SKU Processing**: Process all SKU items, validate data, and calculate totals
            6. **Logistics Calculation**: Calculate shipping costs and delivery requirements
            7. **Final Status Update**: Update the order status based on processing results
            
            Important guidelines:
            - Be thorough in your validation and provide specific details about any issues
            - For missing information, be clear about what exactly is needed
            - Update the order status at key milestones to provide visibility
            - If any step fails, try to understand why and use appropriate recovery methods
            - Provide a comprehensive summary at the end
            
            Please start by getting the order summary to understand the current state.
            """
            
            # Create thread with metadata
            thread_metadata = {
                "order_id": order_id,
                "order_number": order_number or "unknown",
                "workflow": "complete_processing",
                "started_at": datetime.utcnow().isoformat()
            }
            
            thread = await self.create_thread(initial_message, thread_metadata)
            if not thread:
                return {
                    "success": False,
                    "error": "Failed to create agent thread",
                    "order_id": order_id
                }
            
            logger.info(f"Created thread {thread.id} for complete processing of order {order_id}")
            
            # Run the agent with extended timeout for complete processing
            result = await self.run_agent(
                thread_id=thread.id,
                additional_instructions="Focus on thoroughness and accuracy. Provide detailed explanations of each step.",
                timeout_seconds=300  # 5 minutes for complete processing
            )
            
            # Enhance the result with additional context
            enhanced_result = {
                "success": result.get("success", False),
                "thread_id": thread.id,
                "order_id": order_id,
                "order_number": order_number,
                "workflow": "complete_processing",
                "agent_result": result
            }
            
            # Add summary information if successful
            if result.get("success"):
                enhanced_result["summary"] = {
                    "execution_time": result.get("execution_time", 0),
                    "iterations": result.get("iterations", 0),
                    "message_count": len(result.get("messages", [])),
                    "status": "Processing completed successfully"
                }
                logger.info(f"Complete processing succeeded for order {order_id} in {result.get('execution_time', 0):.1f}s")
            else:
                enhanced_result["summary"] = {
                    "status": "Processing failed",
                    "error": result.get("error", "Unknown error")
                }
                logger.error(f"Complete processing failed for order {order_id}: {result.get('error', 'Unknown error')}")
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Failed to process order with agent: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "order_id": order_id,
                "workflow": "complete_processing"
            }
    
    async def process_order_step(self, order_id: str, step_name: str, step_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a specific order step using the agent
        
        This allows for granular control and step-by-step processing with human oversight.
        """
        try:
            if not self.is_initialized:
                return {
                    "success": False,
                    "error": "Agent not initialized",
                    "order_id": order_id,
                    "step": step_name
                }
            
            # Map step names to specific instructions
            step_instructions = {
                "parse": "Parse the uploaded order file and extract all structured data. Be thorough and identify any potential issues.",
                "validate": "Validate the order data for completeness, accuracy, and compliance. Provide detailed feedback on any issues found.",
                "email": "Generate appropriate emails for any missing information. Be specific about what is needed.",
                "sku_processing": "Process all SKU items, validate quantities and details, calculate totals.",
                "logistics": "Calculate shipping costs and logistics requirements based on order details.",
                "status_update": "Update the order status based on current processing state."
            }
            
            if step_name not in step_instructions:
                return {
                    "success": False,
                    "error": f"Unknown step: {step_name}",
                    "order_id": order_id,
                    "available_steps": list(step_instructions.keys())
                }
            
            # Create step-specific message
            step_message = f"""
            Please perform the '{step_name}' step for order {order_id}.
            
            Specific instructions: {step_instructions[step_name]}
            
            First, get the current order summary to understand the state, then proceed with the step.
            """
            
            if step_params:
                step_message += f"\nAdditional parameters: {json.dumps(step_params, indent=2)}"
            
            # Create thread for this step
            thread_metadata = {
                "order_id": order_id,
                "step": step_name,
                "workflow": "step_processing",
                "started_at": datetime.utcnow().isoformat()
            }
            
            thread = await self.create_thread(step_message, thread_metadata)
            if not thread:
                return {
                    "success": False,
                    "error": "Failed to create agent thread",
                    "order_id": order_id,
                    "step": step_name
                }
            
            # Run the agent for this specific step
            result = await self.run_agent(
                thread_id=thread.id,
                timeout_seconds=120  # 2 minutes for individual steps
            )
            
            return {
                "success": result.get("success", False),
                "thread_id": thread.id,
                "order_id": order_id,
                "step": step_name,
                "step_result": result
            }
            
        except Exception as e:
            logger.error(f"Failed to process step {step_name} for order {order_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "order_id": order_id,
                "step": step_name
            }
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and health information"""
        status = {
            "initialized": self.is_initialized,
            "client_available": self.client is not None,
            "agent_available": self.agent is not None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if self.agent:
            status.update({
                "agent_id": self.agent.id,
                "agent_name": self.agent.name,
                "model": getattr(self.agent, 'model', 'unknown'),
                "temperature": getattr(self.agent, 'temperature', 'unknown')
            })
        
        if not self.is_initialized:
            status["error"] = "Agent not properly initialized"
        
        return status
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Close database session if needed
            if self.db:
                await self.db.close()
            
            # Note: Azure AI Project client doesn't require explicit cleanup
            logger.info("Order Processing Agent cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            # Only attempt cleanup if we have an event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.cleanup())
        except Exception:
            # If no event loop or other issues, just pass
            pass

# Utility functions for external use

async def create_order_processing_agent(db: AsyncSession) -> OrderProcessingAgent:
    """Factory function to create and initialize an order processing agent"""
    agent = OrderProcessingAgent(db)
    
    # Verify initialization
    if not agent.is_initialized:
        logger.warning("Order Processing Agent failed to initialize properly")
    
    return agent

async def process_order_with_agent(db: AsyncSession, order_id: str, order_number: str = None) -> Dict[str, Any]:
    """
    Convenience function to process an order with a new agent instance
    
    This is useful for one-off processing tasks.
    """
    agent = await create_order_processing_agent(db)
    
    try:
        result = await agent.process_order_complete(order_id, order_number)
        return result
    finally:
        await agent.cleanup()
