from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database.connection import get_db
from app.models.user import User
from app.models.order import Order
from app.models.tracking import OrderTracking, EmailCommunication
from app.api.auth import get_current_user
from app.services.order_processing_service import OrderProcessingService
from app.services.file_parser_service import FileParserService
from app.services.order_validator_service import OrderValidatorService
from app.services.email_generator_service import EmailGeneratorService
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["Order Processing"])

@router.post("/{order_id}/process")
async def process_order(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Process an uploaded order with comprehensive validation and email generation"""
    try:
        service = OrderProcessingService(db)
        result = await service.process_uploaded_order(order_id)
        
        return {
            "success": True,
            "message": "Order processed successfully",
            "data": result
        }
    
    except Exception as e:
        logger.error(f"Error processing order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing order: {str(e)}"
        )

@router.get("/{order_id}/tracking")
async def get_order_tracking(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive order tracking history for UI display"""
    try:
        service = OrderProcessingService(db)
        tracking_history = await service.get_order_tracking_history(order_id)
        
        return {
            "success": True,
            "message": "Order tracking retrieved successfully",
            "data": {
                "order_id": order_id,
                "tracking_history": tracking_history,
                "total_entries": len(tracking_history)
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting order tracking for {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving order tracking: {str(e)}"
        )

@router.get("/{order_id}/validation-summary")
async def get_order_validation_summary(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get order validation summary for UI dashboard"""
    try:
        service = OrderProcessingService(db)
        summary = await service.get_order_validation_summary(order_id)
        
        return {
            "success": True,
            "message": "Order validation summary retrieved successfully",
            "data": summary
        }
    
    except Exception as e:
        logger.error(f"Error getting validation summary for {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving validation summary: {str(e)}"
        )

@router.post("/{order_id}/validate")
async def validate_order(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Validate order completeness and identify missing fields"""
    try:
        # Get order and parsed data
        service = OrderProcessingService(db)
        validator_service = OrderValidatorService(db)
        
        # Get order details
        from app.models.order import Order
        
        result = await db.execute(
            select(Order).where(Order.id == uuid.UUID(order_id))
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found"
            )
        
        if not order.parsed_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order has no parsed data. Please upload and parse file first."
            )
        
        # Validate order completeness
        validation_result = await validator_service.validate_order_completeness(order_id, order.parsed_data)
        
        return {
            "success": True,
            "message": "Order validation completed",
            "data": validation_result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating order: {str(e)}"
        )

@router.post("/{order_id}/generate-email")
async def generate_missing_info_email(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate draft email for missing information"""
    try:
        # Get order and validation result
        from app.models.order import Order
        
        result = await db.execute(
            select(Order).where(Order.id == uuid.UUID(order_id))
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found"
            )
        
        if not order.parsed_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order has no parsed data. Please process order first."
            )
        
        # Validate order first to get validation result
        validator_service = OrderValidatorService(db)
        validation_result = await validator_service.validate_order_completeness(order_id, order.parsed_data)
        
        # Generate email
        email_service = EmailGeneratorService(db)
        email_result = await email_service.generate_missing_info_email(
            order_id, validation_result, order.parsed_data
        )
        
        return {
            "success": True,
            "message": "Draft email generated successfully",
            "data": email_result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating email for order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating email: {str(e)}"
        )

@router.post("/{order_id}/parse-file")
async def parse_order_file(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Parse order file with enhanced parser"""
    try:
        # Get order
        from app.models.order import Order
        
        result = await db.execute(
            select(Order).where(Order.id == uuid.UUID(order_id))
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found"
            )
        
        if not order.file_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order has no file to parse"
            )
        
        # Parse file
        parser_service = FileParserService(db)
        parsed_data = await parser_service.parse_file(order_id, order.file_path, order.file_type)
        
        # Update order with parsed data
        order.parsed_data = parsed_data
        await db.commit()
        
        return {
            "success": True,
            "message": "File parsed successfully",
            "data": {
                "order_id": order_id,
                "parsed_data": parsed_data
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing file for order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing file: {str(e)}"
        )

@router.get("/{order_id}/emails")
async def get_order_emails(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all emails related to an order"""
    try:
        from app.models.tracking import EmailCommunication
        
        result = await db.execute(
            select(EmailCommunication)
            .where(EmailCommunication.order_id == uuid.UUID(order_id))
            .order_by(EmailCommunication.created_at.desc())
        )
        emails = result.scalars().all()
        
        email_list = []
        for email in emails:
            email_list.append({
                "id": str(email.id),
                "email_type": email.email_type,
                "recipient": email.recipient,
                "sender": email.sender,
                "subject": email.subject,
                "body": email.body,
                "sent_at": email.sent_at.isoformat() if email.sent_at else None,
                "response_received_at": email.response_received_at.isoformat() if email.response_received_at else None,
                "created_at": email.created_at.isoformat()
            })
        
        return {
            "success": True,
            "message": "Order emails retrieved successfully",
            "data": {
                "order_id": order_id,
                "emails": email_list,
                "total_emails": len(email_list)
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting emails for order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving emails: {str(e)}"
        )

@router.get("/tracking/dashboard")
async def get_tracking_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """Get tracking dashboard data for all orders"""
    try:
        from app.models.order import Order
        from app.models.tracking import OrderTracking
        
        # Get order statistics
        order_stats_result = await db.execute(
            select(
                Order.status,
                func.count(Order.id).label('count')
            ).group_by(Order.status)
        )
        order_stats = order_stats_result.fetchall()
        
        # Get recent tracking activities
        recent_tracking_result = await db.execute(
            select(OrderTracking)
            .order_by(OrderTracking.created_at.desc())
            .limit(50)
        )
        recent_tracking = recent_tracking_result.scalars().all()
        
        # Compile dashboard data
        dashboard_data = {
            "order_statistics": [
                {"status": stat.status, "count": stat.count}
                for stat in order_stats
            ],
            "recent_activities": [
                {
                    "id": str(activity.id),
                    "order_id": str(activity.order_id),
                    "status": activity.status,
                    "message": activity.message,
                    "timestamp": activity.created_at.isoformat()
                }
                for activity in recent_tracking
            ],
            "dashboard_generated_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "message": "Tracking dashboard data retrieved successfully",
            "data": dashboard_data
        }
    
    except Exception as e:
        logger.error(f"Error getting tracking dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving dashboard data: {str(e)}"
        )

# Add these comprehensive endpoints for enhanced UI tracking and missing info management

@router.get("/{order_id}/processing-status")
async def get_processing_status(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get real-time processing status with step-by-step details"""
    try:
        # Get order details
        order_result = await db.execute(
            select(Order).where(Order.id == uuid.UUID(order_id))
        )
        order = order_result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get tracking history
        tracking_query = select(OrderTracking).where(
            OrderTracking.order_id == uuid.UUID(order_id)
        ).order_by(OrderTracking.created_at.asc())
        tracking_result = await db.execute(tracking_query)
        tracking_history = tracking_result.scalars().all()
        
        # Get validation summary
        processing_service = OrderProcessingService(db)
        validation_summary = await processing_service.get_validation_summary(order_id)
        
        # Get missing info details
        missing_info = await processing_service.get_missing_info_details(order_id)
        
        # Get email communications
        email_query = select(EmailCommunication).where(
            EmailCommunication.order_id == uuid.UUID(order_id)
        ).order_by(EmailCommunication.created_at.desc())
        email_result = await db.execute(email_query)
        emails = email_result.scalars().all()
        
        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "current_status": order.status,
                "progress_percentage": _calculate_progress_percentage(order.status, tracking_history),
                "processing_steps": [
                    {
                        "id": str(track.id),
                        "step": track.status,
                        "message": track.message,
                        "details": track.details,
                        "timestamp": track.created_at.isoformat(),
                        "category": _categorize_step(track.status),
                        "is_completed": _is_step_completed(track.status),
                        "is_error": "ERROR" in track.status or "FAILED" in track.status,
                        "can_retry": _can_retry_step(track.status)
                    }
                    for track in tracking_history
                ],
                "validation_summary": validation_summary,
                "missing_info": missing_info,
                "emails": [
                    {
                        "id": str(email.id),
                        "type": email.email_type,
                        "subject": email.subject,
                        "recipient": email.recipient,
                        "status": getattr(email, 'status', 'draft'),
                        "sent_at": email.sent_at.isoformat() if email.sent_at else None,
                        "created_at": email.created_at.isoformat()
                    }
                    for email in emails
                ],
                "can_edit": order.status in ["PENDING_INFO", "MISSING_INFO", "VALIDATION_FAILED"],
                "next_actions": _get_next_actions(order.status, validation_summary)
            }
        }
    except Exception as e:
        logger.error(f"Error getting processing status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{order_id}/correct-info")
async def correct_missing_info(
    order_id: str,
    corrections: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit corrections for missing information"""
    try:
        order = await db.execute(
            select(Order).where(Order.id == uuid.UUID(order_id))
        )
        order = order.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order.status not in ["PENDING_INFO", "MISSING_INFO", "VALIDATION_FAILED"]:
            raise HTTPException(status_code=400, detail="Order is not in a correctable state")
        
        # Process corrections
        processing_service = OrderProcessingService(db)
        result = await processing_service.apply_corrections(order_id, corrections, current_user.id)
        
        # Log the correction
        await processing_service._log_tracking(
            order_id, 
            "INFO_CORRECTION_APPLIED", 
            f"User corrections applied: {len(corrections)} fields updated"
        )
        
        return {
            "success": True,
            "message": "Corrections applied successfully",
            "data": result
        }
    except Exception as e:
        logger.error(f"Error applying corrections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{order_id}/regenerate-email")
async def regenerate_email_draft(
    order_id: str,
    email_type: str = "missing_info",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Regenerate email draft with current missing info"""
    try:
        processing_service = OrderProcessingService(db)
        
        # Get current validation status
        validation_result = await processing_service.get_validation_summary(order_id)
        
        # Generate new email
        email_generator = EmailGeneratorService(db)
        result = await email_generator.generate_missing_info_email(
            order_id, validation_result, validation_result.get("parsed_data", {})
        )
        
        return {
            "success": True,
            "message": "Email draft regenerated",
            "data": result
        }
    except Exception as e:
        logger.error(f"Error regenerating email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{order_id}/retry-step")
async def retry_processing_step(
    order_id: str,
    step: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retry a specific processing step"""
    try:
        processing_service = OrderProcessingService(db)
        
        if step == "file_parsing":
            result = await processing_service.retry_file_parsing(order_id)
        elif step == "validation":
            result = await processing_service.retry_validation(order_id)
        elif step == "sku_processing":
            result = await processing_service.retry_sku_processing(order_id)
        elif step == "email_generation":
            result = await processing_service.retry_email_generation(order_id)
        else:
            raise ValueError(f"Unknown step: {step}")
        
        return {
            "success": True,
            "message": f"Step {step} retried successfully",
            "data": result
        }
    except Exception as e:
        logger.error(f"Error retrying step {step}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _calculate_progress_percentage(status: str, tracking_history: list) -> int:
    """Calculate processing progress percentage"""
    status_progress = {
        "UPLOADED": 10,
        "PROCESSING": 25,
        "PENDING_INFO": 50,
        "MISSING_INFO": 40,
        "INFO_RECEIVED": 60,
        "VALIDATED": 80,
        "COMPLETED": 100,
        "VALIDATION_FAILED": 35,
        "ERROR": 25
    }
    return status_progress.get(status, 0)

def _categorize_step(status: str) -> str:
    """Categorize processing step"""
    if "FILE" in status:
        return "file_processing"
    elif "VALIDATION" in status:
        return "validation"
    elif "EMAIL" in status:
        return "communication"
    elif "SKU" in status:
        return "sku_processing"
    else:
        return "general"

def _is_step_completed(status: str) -> bool:
    """Check if step is completed"""
    return "COMPLETED" in status or "PASSED" in status or "SENT" in status

def _can_retry_step(status: str) -> bool:
    """Check if step can be retried"""
    return "ERROR" in status or "FAILED" in status

def _get_next_actions(status: str, validation_summary: dict) -> list:
    """Get available next actions based on current status"""
    actions = []
    
    if status == "PENDING_INFO":
        actions.append({"action": "correct_info", "label": "Provide Missing Information"})
        actions.append({"action": "regenerate_email", "label": "Regenerate Email Draft"})
    elif status == "MISSING_INFO":
        actions.append({"action": "correct_info", "label": "Correct Information"})
    elif status == "VALIDATION_FAILED":
        actions.append({"action": "retry_validation", "label": "Retry Validation"})
        actions.append({"action": "correct_info", "label": "Correct Data"})
    elif "ERROR" in status:
        actions.append({"action": "retry_processing", "label": "Retry Processing"})
    
    return actions
