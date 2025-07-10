"""
Unified Order Processing API Endpoints
Consolidates order processing functionality using the UnifiedOrderProcessor.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.config import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.services.unified_order_processor import UnifiedOrderProcessor
from agents.order_processing_agent import create_order_processing_agent
import uuid

router = APIRouter(prefix="/api/requestedorders", tags=["unified-order-processing"])
logger = logging.getLogger(__name__)


# ============== UNIFIED PROCESSING ENDPOINTS ==============

@router.post("/{order_id}/process-unified")
async def process_order_unified(
    order_id: str,
    use_agent: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unified order processing endpoint - single API call for complete workflow
    
    - If use_agent=True: Uses the AI agent for processing
    - If use_agent=False: Uses the UnifiedOrderProcessor directly
    """
    try:
        logger.info(f"Starting unified processing for order {order_id} (agent={use_agent})")
        
        if use_agent:
            # Use AI agent for processing
            agent = await create_order_processing_agent(db)
            try:
                result = await agent.process_order_complete(order_id)
                return {
                    "success": result.get("success", False),
                    "message": "Order processed using AI agent",
                    "processing_method": "ai_agent",
                    "data": result
                }
            finally:
                await agent.cleanup()
        else:
            # Use UnifiedOrderProcessor directly
            processor = UnifiedOrderProcessor(db)
            result = await processor.process_order_complete(order_id)
            
            return {
                "success": result.get("success", False),
                "message": "Order processed using unified processor",
                "processing_method": "unified_processor",
                "data": result
            }
    
    except Exception as e:
        logger.error(f"Unified processing failed for order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


@router.post("/{order_id}/process-step")
async def process_order_step(
    order_id: str,
    step_name: str,
    use_agent: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process individual order processing step
    
    Available steps: parse, validate, email, sku_processing, logistics
    """
    try:
        valid_steps = ["parse", "validate", "email", "sku_processing", "logistics"]
        if step_name not in valid_steps:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid step. Available steps: {valid_steps}"
            )
        
        logger.info(f"Processing step '{step_name}' for order {order_id} (agent={use_agent})")
        
        if use_agent:
            # Use AI agent for step processing
            agent = await create_order_processing_agent(db)
            try:
                result = await agent.process_order_step(order_id, step_name)
                return {
                    "success": result.get("success", False),
                    "message": f"Step '{step_name}' processed using AI agent",
                    "processing_method": "ai_agent",
                    "step": step_name,
                    "data": result
                }
            finally:
                await agent.cleanup()
        else:
            # Use UnifiedOrderProcessor directly
            processor = UnifiedOrderProcessor(db)
            
            # Map step names to processor methods
            step_mapping = {
                "parse": processor.process_file_parsing,
                "validate": processor.process_validation,
                "email": lambda oid: processor.process_email_workflow(oid, {"is_valid": False}),
                "sku_processing": processor.process_sku_items,
                "logistics": processor.process_logistics
            }
            
            step_func = step_mapping[step_name]
            result = await step_func(order_id)
            
            return {
                "success": result.get("success", False),
                "message": f"Step '{step_name}' processed using unified processor",
                "processing_method": "unified_processor",
                "step": step_name,
                "data": result
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Step processing failed for order {order_id}, step {step_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Step processing failed: {str(e)}"
        )


@router.post("/{order_id}/apply-corrections")
async def apply_order_corrections(
    order_id: str,
    corrections: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Apply user corrections to order data"""
    try:
        logger.info(f"Applying corrections to order {order_id}")
        
        processor = UnifiedOrderProcessor(db)
        result = await processor.apply_corrections(order_id, corrections, str(current_user.id))
        
        return {
            "success": result.get("success", False),
            "message": "Corrections applied successfully",
            "data": result
        }
    
    except Exception as e:
        logger.error(f"Apply corrections failed for order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Apply corrections failed: {str(e)}"
        )


@router.post("/{order_id}/retry-step")
async def retry_processing_step(
    order_id: str,
    step_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retry a failed processing step"""
    try:
        logger.info(f"Retrying step '{step_name}' for order {order_id}")
        
        processor = UnifiedOrderProcessor(db)
        result = await processor.retry_processing_step(order_id, step_name)
        
        return {
            "success": result.get("success", False),
            "message": f"Step '{step_name}' retry completed",
            "step": step_name,
            "data": result
        }
    
    except Exception as e:
        logger.error(f"Retry step failed for order {order_id}, step {step_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retry step failed: {str(e)}"
        )


@router.get("/{order_id}/summary-unified")
async def get_order_summary_unified(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive order summary using unified processor"""
    try:
        processor = UnifiedOrderProcessor(db)
        result = await processor.get_order_summary(order_id)
        
        return {
            "success": result.get("success", False),
            "message": "Order summary retrieved",
            "data": result
        }
    
    except Exception as e:
        logger.error(f"Get order summary failed for order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get order summary failed: {str(e)}"
        )


# ============== AGENT MANAGEMENT ENDPOINTS ==============

@router.post("/agent/create")
async def create_agent(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create and initialize a new Order Processing Agent"""
    try:
        agent = await create_order_processing_agent(db)
        status = await agent.get_agent_status()
        await agent.cleanup()
        
        return {
            "success": status.get("initialized", False),
            "message": "Agent created successfully" if status.get("initialized") else "Agent creation failed",
            "agent_status": status
        }
    
    except Exception as e:
        logger.error(f"Agent creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent creation failed: {str(e)}"
        )


@router.get("/agent/status")
async def get_agent_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current agent status"""
    try:
        agent = await create_order_processing_agent(db)
        status = await agent.get_agent_status()
        await agent.cleanup()
        
        return {
            "success": True,
            "message": "Agent status retrieved",
            "agent_status": status
        }
    
    except Exception as e:
        logger.error(f"Get agent status failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get agent status failed: {str(e)}"
        )


# ============== BATCH PROCESSING ENDPOINTS ==============

@router.post("/batch/process-unified")
async def batch_process_orders(
    order_ids: list[str],
    use_agent: bool = False,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process multiple orders in batch"""
    try:
        logger.info(f"Starting batch processing for {len(order_ids)} orders")
        
        # Validate order IDs
        valid_order_ids = []
        for order_id in order_ids:
            try:
                uuid.UUID(order_id)
                valid_order_ids.append(order_id)
            except ValueError:
                logger.warning(f"Invalid order ID: {order_id}")
        
        if not valid_order_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid order IDs provided"
            )
        
        # Process orders
        results = []
        processor = UnifiedOrderProcessor(db)
        
        for order_id in valid_order_ids:
            try:
                if use_agent:
                    agent = await create_order_processing_agent(db)
                    try:
                        result = await agent.process_order_complete(order_id)
                    finally:
                        await agent.cleanup()
                else:
                    result = await processor.process_order_complete(order_id)
                
                results.append({
                    "order_id": order_id,
                    "success": result.get("success", False),
                    "result": result
                })
            
            except Exception as e:
                logger.error(f"Batch processing failed for order {order_id}: {str(e)}")
                results.append({
                    "order_id": order_id,
                    "success": False,
                    "error": str(e)
                })
        
        successful_count = sum(1 for r in results if r["success"])
        
        return {
            "success": True,
            "message": f"Batch processing completed: {successful_count}/{len(results)} successful",
            "processing_method": "ai_agent" if use_agent else "unified_processor",
            "total_orders": len(results),
            "successful_orders": successful_count,
            "failed_orders": len(results) - successful_count,
            "results": results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch processing failed: {str(e)}"
        )


# ============== UTILITY ENDPOINTS ==============

@router.get("/processing/methods")
async def get_processing_methods():
    """Get available processing methods and their descriptions"""
    return {
        "success": True,
        "methods": {
            "unified_processor": {
                "name": "Unified Order Processor",
                "description": "Direct processing using the consolidated order processor",
                "advantages": ["Fast", "Reliable", "Predictable"],
                "use_cases": ["High volume processing", "Production workloads"]
            },
            "ai_agent": {
                "name": "AI Agent Processing",
                "description": "Processing using Azure AI Foundry agent with natural language capabilities",
                "advantages": ["Intelligent decision making", "Error recovery", "Detailed explanations"],
                "use_cases": ["Complex orders", "Exception handling", "Interactive processing"]
            }
        },
        "available_steps": [
            "parse", "validate", "email", "sku_processing", "logistics"
        ]
    }


@router.get("/processing/health")
async def get_processing_health(
    db: AsyncSession = Depends(get_db)
):
    """Get health status of processing components"""
    try:
        # Test unified processor
        processor = UnifiedOrderProcessor(db)
        processor_health = {"available": True, "type": "unified_processor"}
        
        # Test agent
        agent_health = {"available": False, "type": "ai_agent"}
        try:
            agent = await create_order_processing_agent(db)
            status = await agent.get_agent_status()
            agent_health["available"] = status.get("initialized", False)
            agent_health["details"] = status
            await agent.cleanup()
        except Exception as e:
            agent_health["error"] = str(e)
        
        return {
            "success": True,
            "message": "Processing health check completed",
            "components": {
                "unified_processor": processor_health,
                "ai_agent": agent_health
            },
            "overall_health": "healthy" if processor_health["available"] else "degraded"
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "success": False,
            "message": "Health check failed",
            "error": str(e),
            "overall_health": "unhealthy"
        }
