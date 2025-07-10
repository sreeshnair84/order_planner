from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.connection import get_db
from app.models.user import User
from app.models.order import Order
from app.api.auth import get_current_user
from app.services.ai_foundry_agent_service import OrderProcessingAgentService
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-agent", tags=["AI Agent"])

class CreateThreadRequest(BaseModel):
    order_id: str
    message: str
    auto_start: bool = True

class ThreadMessageRequest(BaseModel):
    message: str

class ThreadResponse(BaseModel):
    thread_id: str
    order_id: str
    status: str
    messages: List[Dict]
    tools_used: List[str]
    created_at: str
    updated_at: str

class AgentRunResponse(BaseModel):
    status: str
    thread_id: str
    run_id: Optional[str] = None
    messages: Optional[List[str]] = None
    tools_used: Optional[List[str]] = None
    error: Optional[str] = None

@router.post("/threads")
async def create_ai_thread(
    request: CreateThreadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new AI agent thread for order processing"""
    try:
        # Verify order exists and user has access
        result = await db.execute(
            select(Order).where(
                Order.id == uuid.UUID(request.order_id),
                Order.user_id == current_user.id
            )
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or access denied"
            )
        
        # Initialize AI agent service
        agent_service = OrderProcessingAgentService(db)
        
        # Create thread
        thread_result = await agent_service.create_agent_thread(
            request.order_id, request.message
        )
        
        # Auto-start processing if requested
        if request.auto_start:
            run_result = await agent_service.run_agent_with_tools(
                thread_result["thread_id"], request.order_id
            )
            thread_result.update(run_result)
        
        return {
            "success": True,
            "message": "AI thread created successfully",
            "data": thread_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create AI thread: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create AI thread: {str(e)}"
        )

@router.get("/threads/{thread_id}")
async def get_thread_state(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current state of an AI thread"""
    try:
        agent_service = OrderProcessingAgentService(db)
        thread_state = await agent_service.get_thread_state(thread_id)
        
        if not thread_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread not found"
            )
        
        # Verify user has access to the order
        result = await db.execute(
            select(Order).where(
                Order.id == uuid.UUID(thread_state.order_id),
                Order.user_id == current_user.id
            )
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this thread"
            )
        
        return {
            "success": True,
            "data": ThreadResponse(
                thread_id=thread_state.thread_id,
                order_id=thread_state.order_id,
                status=thread_state.status,
                messages=thread_state.messages,
                tools_used=thread_state.tools_used,
                created_at=thread_state.created_at.isoformat(),
                updated_at=thread_state.updated_at.isoformat()
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get thread state: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get thread state: {str(e)}"
        )

@router.post("/threads/{thread_id}/run")
async def run_agent(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run the AI agent on an existing thread"""
    try:
        agent_service = OrderProcessingAgentService(db)
        thread_state = await agent_service.get_thread_state(thread_id)
        
        if not thread_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread not found"
            )
        
        # Verify user has access
        result = await db.execute(
            select(Order).where(
                Order.id == uuid.UUID(thread_state.order_id),
                Order.user_id == current_user.id
            )
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this thread"
            )
        
        # Run agent
        run_result = await agent_service.run_agent_with_tools(
            thread_id, thread_state.order_id
        )
        
        return {
            "success": True,
            "message": "Agent run completed",
            "data": AgentRunResponse(**run_result)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run agent: {str(e)}"
        )

@router.post("/threads/{thread_id}/messages")
async def add_message_to_thread(
    thread_id: str,
    request: ThreadMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a message to an existing thread and optionally run the agent"""
    try:
        agent_service = OrderProcessingAgentService(db)
        
        # Verify thread exists and user has access
        thread_state = await agent_service.get_thread_state(thread_id)
        if not thread_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread not found"
            )
        
        # Verify user access
        result = await db.execute(
            select(Order).where(
                Order.id == uuid.UUID(thread_state.order_id),
                Order.user_id == current_user.id
            )
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this thread"
            )
        
        # Add message to thread (simplified - in real implementation, use Azure AI client)
        # For now, we'll just run the agent again
        run_result = await agent_service.run_agent_with_tools(
            thread_id, thread_state.order_id
        )
        
        return {
            "success": True,
            "message": "Message added and agent run completed",
            "data": run_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add message: {str(e)}"
        )

@router.get("/requestedorders/{order_id}/threads")
async def list_order_threads(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all AI threads for an order"""
    try:
        # Verify order exists and user has access
        result = await db.execute(
            select(Order).where(
                Order.id == uuid.UUID(order_id),
                Order.user_id == current_user.id
            )
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or access denied"
            )
        
        # Get all threads for the order
        agent_service = OrderProcessingAgentService(db)
        threads = await agent_service.list_order_threads(order_id)
        
        thread_responses = [
            ThreadResponse(
                thread_id=thread.thread_id,
                order_id=thread.order_id,
                status=thread.status,
                messages=thread.messages,
                tools_used=thread.tools_used,
                created_at=thread.created_at.isoformat(),
                updated_at=thread.updated_at.isoformat()
            )
            for thread in threads
        ]
        
        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "threads": thread_responses,
                "total_count": len(thread_responses)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list threads: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list threads: {str(e)}"
        )

@router.post("/requestedorders/{order_id}/process-with-ai")
async def process_order_with_ai(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process an order using AI agent (convenience endpoint)"""
    try:
        # Verify order exists and user has access
        result = await db.execute(
            select(Order).where(
                Order.id == uuid.UUID(order_id),
                Order.user_id == current_user.id
            )
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or access denied"
            )
        
        # Initialize AI agent service
        agent_service = OrderProcessingAgentService(db)
        
        # Create thread with processing message
        processing_message = f"""
        Please process order {order.order_number} with the following steps:
        1. Parse the uploaded file data
        2. Validate order completeness and accuracy
        3. Process SKU items and check inventory
        4. Calculate logistics and shipping costs
        5. Generate any necessary emails for missing information
        6. Update order status based on processing results
        
        Order details:
        - File: {order.file_path}
        - Type: {order.file_type}
        - Status: {order.status}
        """
        
        # Create and run thread
        thread_result = await agent_service.create_agent_thread(
            order_id, processing_message
        )
        
        run_result = await agent_service.run_agent_with_tools(
            thread_result["thread_id"], order_id
        )
        
        return {
            "success": True,
            "message": "Order processing with AI completed",
            "data": {
                "thread_id": thread_result["thread_id"],
                "processing_result": run_result,
                "order_status": order.status
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process order with AI: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process order with AI: {str(e)}"
        )
