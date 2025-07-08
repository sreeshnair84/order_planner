from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import json
import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import uuid

# Try to import Azure packages, fall back to mock if not available
try:
    from azure.ai.projects import AIProjectClient
    from azure.ai.projects.models import RunStatus, ThreadMessage, MessageRole
    from azure.identity import DefaultAzureCredential
    from azure.core.exceptions import AzureError
    AZURE_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Azure AI packages not available: {e}. Using mock implementation.")
    AZURE_AVAILABLE = False
    
    # Mock classes for development
    class AIProjectClient:
        pass
    class RunStatus:
        COMPLETED = "completed"
        FAILED = "failed"
        REQUIRES_ACTION = "requires_action"
    class MessageRole:
        USER = "user"
        ASSISTANT = "assistant"
    class AzureError(Exception):
        pass

from app.utils.config import settings
from app.models.order import Order
from app.models.tracking import OrderTracking, AIAgentThread

# Try to import the comprehensive agent, fall back to mock
try:
    from agents.order_processing_agent import OrderProcessingAgent, create_order_processing_agent
    AGENT_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Order processing agent not available: {e}. Using mock implementation.")
    AGENT_AVAILABLE = False
    
    # Mock agent for development
    class OrderProcessingAgent:
        def __init__(self, db):
            self.db = db
            self.is_initialized = False
        
        async def get_agent_status(self):
            return {"initialized": False, "error": "Azure packages not installed"}
        
        async def create_thread(self, message=None, metadata=None):
            return None
        
        async def run_agent(self, thread_id, **kwargs):
            return {"success": False, "error": "Azure packages not installed"}
        
        async def process_order_complete(self, order_id, order_number=None):
            return {"success": False, "error": "Azure packages not installed"}
        
        async def process_order_step(self, order_id, step_name, step_params=None):
            return {"success": False, "error": "Azure packages not installed"}
        
        async def cleanup(self):
            pass

logger = logging.getLogger(__name__)

@dataclass
class AgentToolResult:
    """Result from an agent tool execution"""
    success: bool
    data: Any
    message: str
    metadata: Optional[Dict] = None

@dataclass
class AgentThreadState:
    """State management for AI agent threads"""
    thread_id: str
    order_id: str
    status: str
    messages: List[Dict]
    tools_used: List[str]
    created_at: datetime
    updated_at: datetime

class OrderProcessingAgentService:
    """
    Azure AI Foundry Agent service for order processing with comprehensive tooling.
    
    This service acts as a bridge between the FastAPI application and the Azure AI Foundry
    agent, providing database integration and state management.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent: Optional[OrderProcessingAgent] = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the order processing agent"""
        try:
            if not AZURE_AVAILABLE or not AGENT_AVAILABLE:
                logger.warning("Azure AI packages or agent not available - using mock implementation")
                self.agent = OrderProcessingAgent(self.db)
                return
            
            self.agent = OrderProcessingAgent(self.db)
            if self.agent.is_initialized:
                logger.info("OrderProcessingAgentService initialized successfully with Azure AI")
            else:
                logger.warning("OrderProcessingAgent failed to initialize - check Azure AI configuration")
        except Exception as e:
            logger.error(f"Failed to initialize OrderProcessingAgentService: {str(e)}")
            self.agent = OrderProcessingAgent(self.db)  # Fall back to mock
    async def create_agent_thread(self, order_id: str, user_message: str) -> Dict[str, Any]:
        """Create a new AI agent thread for order processing"""
        try:
            if not self.agent or not self.agent.is_initialized:
                raise ValueError("Agent not initialized")
            
            # Create thread using our agent
            thread = await self.agent.create_thread(
                initial_message=user_message,
                metadata={
                    "order_id": order_id,
                    "created_by": "api_service",
                    "purpose": "order_processing"
                }
            )
            
            if not thread:
                raise ValueError("Failed to create agent thread")
            
            # Save thread state to database
            thread_state = AIAgentThread(
                id=uuid.uuid4(),
                order_id=uuid.UUID(order_id),
                thread_id=thread.id,
                status="CREATED",
                messages=[{
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "user"
                }],
                tools_used=[],
                metadata={
                    "agent_id": self.agent.agent.id if self.agent.agent else None,
                    "created_via": "api_service"
                }
            )
            
            self.db.add(thread_state)
            await self.db.commit()
            
            await self._log_tracking(order_id, "AI_THREAD_CREATED", 
                                   f"AI agent thread created: {thread.id}")
            
            return {
                "thread_id": thread.id,
                "status": "CREATED",
                "order_id": order_id,
                "agent_initialized": True
            }
            
        except Exception as e:
            logger.error(f"Failed to create agent thread: {str(e)}")
            raise
    
    async def run_agent_with_tools(self, thread_id: str, order_id: str, additional_instructions: str = None) -> Dict[str, Any]:
        """Run the AI agent with order processing tools"""
        try:
            if not self.agent or not self.agent.is_initialized:
                raise ValueError("Agent not initialized")
            
            # Update thread status in database
            await self._update_thread_status(thread_id, "RUNNING")
            
            # Add additional message if provided
            if additional_instructions:
                await self.agent.add_message_to_thread(thread_id, additional_instructions)
            
            # Run the agent
            result = await self.agent.run_agent(
                thread_id=thread_id,
                additional_instructions=additional_instructions,
                timeout_seconds=180  # 3 minutes
            )
            
            # Update thread status based on result
            final_status = "COMPLETED" if result.get("success") else "FAILED"
            await self._update_thread_status(thread_id, final_status)
            
            # Extract tools used from the result
            tools_used = []
            if result.get("success") and "messages" in result:
                # Try to extract tool usage from messages or metadata
                # This is a simplified extraction - you might want to enhance this
                for message in result["messages"]:
                    content = message.get("content", "")
                    if "tool:" in content.lower() or "function:" in content.lower():
                        # Extract tool names from content
                        pass  # Implement tool extraction logic if needed
            
            # Update database with final state
            await self._update_thread_with_result(thread_id, result, tools_used)
            
            # Log completion
            await self._log_tracking(
                order_id, 
                "AI_AGENT_COMPLETED" if result.get("success") else "AI_AGENT_FAILED",
                f"Agent execution completed with status: {final_status}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to run agent: {str(e)}")
            await self._update_thread_status(thread_id, "ERROR")
            await self._log_tracking(order_id, "AI_AGENT_ERROR", f"Agent execution failed: {str(e)}")
            raise
    
    async def process_order_completely(self, order_id: str, order_number: str = None) -> Dict[str, Any]:
        """Process an order completely using the agent"""
        try:
            if not self.agent or not self.agent.is_initialized:
                raise ValueError("Agent not initialized")
            
            # Use the agent's complete processing method
            result = await self.agent.process_order_complete(order_id, order_number)
            
            # If successful, save the thread state to database
            if result.get("success") and result.get("thread_id"):
                thread_id = result["thread_id"]
                
                # Save thread state
                thread_state = AIAgentThread(
                    id=uuid.uuid4(),
                    order_id=uuid.UUID(order_id),
                    thread_id=thread_id,
                    status="COMPLETED",
                    messages=result.get("agent_result", {}).get("messages", []),
                    tools_used=["complete_processing_workflow"],
                    metadata={
                        "processing_type": "complete",
                        "execution_time": result.get("summary", {}).get("execution_time", 0),
                        "agent_id": self.agent.agent.id if self.agent.agent else None
                    }
                )
                
                self.db.add(thread_state)
                await self.db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process order completely: {str(e)}")
            raise
    
    async def process_order_step(self, order_id: str, step_name: str, step_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a specific order step using the agent"""
        try:
            if not self.agent or not self.agent.is_initialized:
                raise ValueError("Agent not initialized")
            
            result = await self.agent.process_order_step(order_id, step_name, step_params)
            
            # Save step result to database if successful
            if result.get("success") and result.get("thread_id"):
                thread_id = result["thread_id"]
                
                thread_state = AIAgentThread(
                    id=uuid.uuid4(),
                    order_id=uuid.UUID(order_id),
                    thread_id=thread_id,
                    status="COMPLETED",
                    messages=result.get("step_result", {}).get("messages", []),
                    tools_used=[step_name],
                    metadata={
                        "processing_type": "step",
                        "step_name": step_name,
                        "step_params": step_params or {},
                        "agent_id": self.agent.agent.id if self.agent.agent else None
                    }
                )
                
                self.db.add(thread_state)
                await self.db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process order step: {str(e)}")
            raise
    
    async def get_thread_state(self, thread_id: str) -> Optional[AgentThreadState]:
        """Get thread state from database"""
        try:
            result = await self.db.execute(
                select(AIAgentThread).where(AIAgentThread.thread_id == thread_id)
            )
            thread_record = result.scalar_one_or_none()
            
            if not thread_record:
                return None
            
            return AgentThreadState(
                thread_id=thread_record.thread_id,
                order_id=str(thread_record.order_id),
                status=thread_record.status,
                messages=thread_record.messages or [],
                tools_used=thread_record.tools_used or [],
                created_at=thread_record.created_at,
                updated_at=thread_record.updated_at
            )
            
        except Exception as e:
            logger.error(f"Failed to get thread state: {str(e)}")
            return None
    
    async def list_order_threads(self, order_id: str) -> List[AgentThreadState]:
        """List all threads for an order (alias for compatibility)"""
        return await self.list_threads_for_order(order_id)
    
    async def list_threads_for_order(self, order_id: str) -> List[AgentThreadState]:
        """List all threads for an order"""
        try:
            result = await self.db.execute(
                select(AIAgentThread)
                .where(AIAgentThread.order_id == uuid.UUID(order_id))
                .order_by(AIAgentThread.created_at.desc())
            )
            threads = result.scalars().all()
            
            return [
                AgentThreadState(
                    thread_id=thread.thread_id,
                    order_id=str(thread.order_id),
                    status=thread.status,
                    messages=thread.messages or [],
                    tools_used=thread.tools_used or [],
                    created_at=thread.created_at,
                    updated_at=thread.updated_at
                )
                for thread in threads
            ]
            
        except Exception as e:
            logger.error(f"Failed to list threads for order: {str(e)}")
            return []
    
    # Helper methods
    
    async def _update_thread_status(self, thread_id: str, status: str):
        """Update thread status in database"""
        try:
            await self.db.execute(
                update(AIAgentThread)
                .where(AIAgentThread.thread_id == thread_id)
                .values(
                    status=status,
                    updated_at=datetime.utcnow()
                )
            )
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update thread status: {str(e)}")
    
    async def _update_thread_with_result(self, thread_id: str, result: Dict[str, Any], tools_used: List[str]):
        """Update thread with execution result"""
        try:
            messages = result.get("messages", [])
            metadata = {
                "execution_time": result.get("execution_time", 0),
                "iterations": result.get("iterations", 0),
                "success": result.get("success", False)
            }
            
            await self.db.execute(
                update(AIAgentThread)
                .where(AIAgentThread.thread_id == thread_id)
                .values(
                    messages=messages,
                    tools_used=tools_used,
                    metadata=metadata,
                    updated_at=datetime.utcnow()
                )
            )
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update thread with result: {str(e)}")
    
    async def _log_tracking(self, order_id: str, event_type: str, message: str):
        """Log tracking event"""
        try:
            tracking_entry = OrderTracking(
                id=uuid.uuid4(),
                order_id=uuid.UUID(order_id),
                event_type=event_type,
                message=message,
                details={"source": "ai_agent_service"}
            )
            
            self.db.add(tracking_entry)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log tracking: {str(e)}")
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.agent:
                await self.agent.cleanup()
            logger.info("OrderProcessingAgentService cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        if not self.agent:
            return {
                "initialized": False,
                "error": "Agent not created"
            }
        
        return await self.agent.get_agent_status()
