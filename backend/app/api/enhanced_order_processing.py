from app.services.azure_functions_client import AzureFunctionsClient
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database.connection import get_db
from app.models.user import User
from app.models.order import Order
from app.api.auth import get_current_user
from app.services.order_processing_service import OrderProcessingService
from app.services.ai_foundry_agent_service import OrderProcessingAgentService
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/requestedorders", tags=["Enhanced Order Processing"])

class ReprocessOrderRequest(BaseModel):
    new_order_id: Optional[str] = None
    processing_options: Optional[Dict] = None

class CorrectOrderRequest(BaseModel):
    corrections: Dict[str, Any]
    apply_immediately: bool = True

class OrderStepResponse(BaseModel):
    step_id: str
    step_name: str
    status: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    details: Optional[Dict] = None
    error_message: Optional[str] = None

@router.post("/{order_id}/reprocess")
async def reprocess_order(
    order_id: str,
    request: ReprocessOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reprocess an order with a new order ID (if provided)"""
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
        
        # Create new order if new_order_id is provided
        if request.new_order_id:
            # Clone the order with new ID
            new_id = uuid.uuid4()
            new_order = Order(
                id=new_id,
                user_id=current_user.id,
                order_number=request.new_order_id,
                original_filename=order.original_filename,
                file_path=order.file_path,
                file_type=order.file_type,
                file_size=order.file_size,
                file_metadata=order.file_metadata,
                priority=order.priority,
                special_instructions=order.special_instructions,
                requested_delivery_date=order.requested_delivery_date,
                delivery_address=order.delivery_address,
                retailer_info=order.retailer_info,
                status="UPLOADED"
            )
            
            db.add(new_order)
            await db.commit()
            
            # Process the new order
            return await AzureFunctionsClient().process_order_file(new_id)
        else:
            # Reprocess existing order
            # Reset order status
            order.status = "UPLOADED"
            order.parsed_data = None
            order.missing_fields = None
            order.validation_errors = None
            order.processing_notes = None
            
            await db.commit()
            
            # Process the order
            return await AzureFunctionsClient().process_order_file(order_id)
            
            r
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reprocess order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reprocess order: {str(e)}"
        )

@router.post("/{order_id}/correct")
async def correct_order(
    order_id: str,
    request: CorrectOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Apply corrections to an order"""
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
        
        # Apply corrections to parsed data
        if order.parsed_data:
            # Deep merge corrections into parsed data
            def apply_corrections(data, corrections, path=""):
                for key, value in corrections.items():
                    if isinstance(value, dict) and key in data and isinstance(data[key], dict):
                        apply_corrections(data[key], value, f"{path}.{key}" if path else key)
                    else:
                        data[key] = value
                        logger.info(f"Applied correction at {path}.{key if path else key}: {value}")
            
            apply_corrections(order.parsed_data, request.corrections)
            
            # Update order fields if they are in corrections
            if 'priority' in request.corrections:
                order.priority = request.corrections['priority']
            if 'special_instructions' in request.corrections:
                order.special_instructions = request.corrections['special_instructions']
            if 'delivery_address' in request.corrections:
                order.delivery_address = request.corrections['delivery_address']
            if 'retailer_info' in request.corrections:
                order.retailer_info = request.corrections['retailer_info']
        
        # Clear validation errors since corrections have been applied
        order.validation_errors = None
        order.missing_fields = None
        
        # Add correction notes
        correction_notes = f"Manual corrections applied by {current_user.email}"
        if order.processing_notes:
            order.processing_notes += f"\n{correction_notes}"
        else:
            order.processing_notes = correction_notes
        
        await db.commit()
        
        # Reprocess if requested
        if request.apply_immediately:
            service = OrderProcessingService(db)
            processing_result = await service.process_uploaded_order(order_id)
            
            return {
                "success": True,
                "message": "Corrections applied and order reprocessed",
                "data": {
                    "order_id": order_id,
                    "corrections_applied": request.corrections,
                    "processing_result": processing_result
                }
            }
        else:
            return {
                "success": True,
                "message": "Corrections applied successfully",
                "data": {
                    "order_id": order_id,
                    "corrections_applied": request.corrections
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to correct order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to correct order: {str(e)}"
        )

@router.get("/{order_id}/steps")
async def get_order_steps(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed processing steps for an order"""
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
        
        # Get tracking entries for detailed steps
        from app.models.tracking import OrderTracking
        tracking_result = await db.execute(
            select(OrderTracking)
            .where(OrderTracking.order_id == uuid.UUID(order_id))
            .order_by(OrderTracking.created_at.asc())
        )
        tracking_entries = tracking_result.scalars().all()
        
        # Convert tracking entries to step responses
        steps = []
        current_step = None
        
        for entry in tracking_entries:
            if entry.event_type.endswith('_STARTED'):
                step_name = entry.event_type.replace('_STARTED', '')
                current_step = {
                    "step_id": f"{step_name}_{entry.id}",
                    "step_name": step_name,
                    "status": "RUNNING",
                    "start_time": entry.created_at.isoformat(),
                    "details": entry.details
                }
            elif entry.event_type.endswith('_COMPLETED') and current_step:
                current_step["status"] = "COMPLETED"
                current_step["end_time"] = entry.created_at.isoformat()
                if current_step["start_time"]:
                    start_time = entry.created_at
                    duration = (entry.created_at - start_time).total_seconds()
                    current_step["duration_seconds"] = duration
                steps.append(OrderStepResponse(**current_step))
                current_step = None
            elif entry.event_type.endswith('_FAILED') and current_step:
                current_step["status"] = "FAILED"
                current_step["end_time"] = entry.created_at.isoformat()
                current_step["error_message"] = entry.message
                steps.append(OrderStepResponse(**current_step))
                current_step = None
            elif not entry.event_type.endswith(('_STARTED', '_COMPLETED', '_FAILED')):
                # Standalone event
                steps.append(OrderStepResponse(
                    step_id=f"EVENT_{entry.id}",
                    step_name=entry.event_type,
                    status="COMPLETED",
                    start_time=entry.created_at.isoformat(),
                    end_time=entry.created_at.isoformat(),
                    duration_seconds=0,
                    details=entry.details
                ))
        
        # Add current step if still running
        if current_step:
            steps.append(OrderStepResponse(**current_step))
        
        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "order_status": order.status,
                "total_steps": len(steps),
                "steps": [step.dict() for step in steps]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get order steps {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get order steps: {str(e)}"
        )

@router.get("/{order_id}/summary")
async def get_order_summary(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive order summary"""
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
        
        # Get AI threads summary
        agent_service = OrderProcessingAgentService(db)
        ai_threads = await agent_service.list_order_threads(order_id)
        
        # Get tracking summary
        from app.models.tracking import OrderTracking
        tracking_result = await db.execute(
            select(OrderTracking)
            .where(OrderTracking.order_id == uuid.UUID(order_id))
            .order_by(OrderTracking.created_at.desc())
        )
        recent_tracking = tracking_result.scalars().first()
        
        summary = {
            "order_id": order_id,
            "order_number": order.order_number,
            "status": order.status,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
            "file_info": {
                "filename": order.original_filename,
                "type": order.file_type,
                "size": order.file_size
            },
            "processing_info": {
                "has_parsed_data": order.parsed_data is not None,
                "has_validation_errors": order.validation_errors is not None,
                "has_missing_fields": order.missing_fields is not None,
                "notes": order.processing_notes
            },
            "ai_processing": {
                "total_threads": len(ai_threads),
                "active_threads": len([t for t in ai_threads if t.status in ['RUNNING', 'CREATED']]),
                "completed_threads": len([t for t in ai_threads if t.status == 'COMPLETED']),
                "failed_threads": len([t for t in ai_threads if t.status == 'FAILED'])
            },
            "last_activity": {
                "event_type": recent_tracking.event_type if recent_tracking else None,
                "message": recent_tracking.message if recent_tracking else None,
                "timestamp": recent_tracking.created_at.isoformat() if recent_tracking else None
            }
        }
        
        return {
            "success": True,
            "data": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get order summary {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get order summary: {str(e)}"
        )
