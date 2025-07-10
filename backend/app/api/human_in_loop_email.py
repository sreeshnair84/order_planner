from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database.connection import get_db
from app.models.user import User
from app.models.order import Order
from app.models.tracking import EmailCommunication
from app.api.auth import get_current_user
from app.services.email_service import EmailService
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/requestedorders", tags=["Human-in-Loop Email"])

class EmailApprovalRequest(BaseModel):
    approved: bool
    modifications: Optional[Dict[str, Any]] = None
    send_immediately: bool = True

class EmailCorrectionRequest(BaseModel):
    missing_info: Dict[str, Any]
    retailer_response: Optional[str] = None

class StructuredOrderConfirmation(BaseModel):
    order_data: Dict[str, Any]
    confirmed: bool
    corrections: Optional[Dict[str, Any]] = None

@router.get("/{order_id}/emails/pending")
async def get_pending_emails(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pending emails awaiting human approval"""
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
        
        # Get pending emails
        email_result = await db.execute(
            select(EmailCommunication)
            .where(
                EmailCommunication.order_id == uuid.UUID(order_id),
                EmailCommunication.status == "PENDING_APPROVAL"
            )
            .order_by(EmailCommunication.created_at.desc())
        )
        pending_emails = email_result.scalars().all()
        
        emails_data = []
        for email in pending_emails:
            emails_data.append({
                "id": str(email.id),
                "email_type": email.email_type,
                "recipient": email.recipient_email,
                "subject": email.subject,
                "content": email.content,
                "metadata": email.metadata,
                "created_at": email.created_at.isoformat(),
                "requires_approval": True
            })
        
        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "pending_emails": emails_data,
                "total_pending": len(emails_data)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pending emails for order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending emails: {str(e)}"
        )

@router.post("/{order_id}/emails/{email_id}/approve")
async def approve_email(
    order_id: str,
    email_id: str,
    request: EmailApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve or modify an email before sending"""
    try:
        # Verify order and email exist
        order_result = await db.execute(
            select(Order).where(
                Order.id == uuid.UUID(order_id),
                Order.user_id == current_user.id
            )
        )
        order = order_result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or access denied"
            )
        
        email_result = await db.execute(
            select(EmailCommunication).where(
                EmailCommunication.id == uuid.UUID(email_id),
                EmailCommunication.order_id == uuid.UUID(order_id)
            )
        )
        email_comm = email_result.scalar_one_or_none()
        
        if not email_comm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        
        if request.approved:
            # Apply modifications if provided
            if request.modifications:
                if 'subject' in request.modifications:
                    email_comm.subject = request.modifications['subject']
                if 'content' in request.modifications:
                    email_comm.content = request.modifications['content']
                if 'recipient_email' in request.modifications:
                    email_comm.recipient_email = request.modifications['recipient_email']
            
            # Update status
            email_comm.status = "APPROVED"
            email_comm.approved_by = current_user.id
            email_comm.approved_at = datetime.utcnow()
            
            # Send email if requested
            if request.send_immediately:
                email_service = EmailService()
                try:
                    await email_service.send_email(
                        to_email=email_comm.recipient_email,
                        subject=email_comm.subject,
                        content=email_comm.content,
                        email_type=email_comm.email_type
                    )
                    email_comm.status = "SENT"
                    email_comm.sent_at = datetime.utcnow()
                    
                    # Log tracking
                    await _log_tracking(
                        db, order_id, "EMAIL_SENT", 
                        f"Email sent to {email_comm.recipient_email}"
                    )
                    
                except Exception as email_error:
                    logger.error(f"Failed to send email: {str(email_error)}")
                    email_comm.status = "SEND_FAILED"
                    email_comm.error_message = str(email_error)
            
            await db.commit()
            
            return {
                "success": True,
                "message": "Email approved and sent" if request.send_immediately else "Email approved",
                "data": {
                    "email_id": email_id,
                    "status": email_comm.status,
                    "sent": request.send_immediately
                }
            }
        else:
            # Email rejected
            email_comm.status = "REJECTED"
            email_comm.approved_by = current_user.id
            email_comm.approved_at = datetime.utcnow()
            if request.modifications and 'rejection_reason' in request.modifications:
                email_comm.error_message = request.modifications['rejection_reason']
            
            await db.commit()
            
            return {
                "success": True,
                "message": "Email rejected",
                "data": {
                    "email_id": email_id,
                    "status": "REJECTED"
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve email {email_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve email: {str(e)}"
        )

@router.post("/{order_id}/emails/retailer-response")
async def handle_retailer_response(
    order_id: str,
    request: EmailCorrectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Handle retailer response with missing information"""
    try:
        # Verify order exists
        result = await db.execute(
            select(Order).where(Order.id == uuid.UUID(order_id))
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Update order with provided information
        if order.parsed_data:
            # Merge the missing info into parsed data
            def update_nested_dict(target, source):
                for key, value in source.items():
                    if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                        update_nested_dict(target[key], value)
                    else:
                        target[key] = value
            
            update_nested_dict(order.parsed_data, request.missing_info)
        else:
            order.parsed_data = request.missing_info
        
        # Clear missing fields that were provided
        if order.missing_fields:
            provided_fields = set(request.missing_info.keys())
            order.missing_fields = [
                field for field in order.missing_fields 
                if field not in provided_fields
            ]
            
            # If no more missing fields, update status
            if not order.missing_fields:
                order.status = "INFORMATION_COMPLETE"
        
        # Add processing note
        note = f"Retailer provided missing information: {list(request.missing_info.keys())}"
        if request.retailer_response:
            note += f"\nRetailer note: {request.retailer_response}"
        
        if order.processing_notes:
            order.processing_notes += f"\n{note}"
        else:
            order.processing_notes = note
        
        await db.commit()
        
        # Create email communication record
        email_comm = EmailCommunication(
            id=uuid.uuid4(),
            order_id=uuid.UUID(order_id),
            email_type="RETAILER_RESPONSE",
            recipient_email=current_user.email,
            subject=f"Information received for Order {order.order_number}",
            content=f"Received missing information for order {order.order_number}",
            status="RECEIVED",
            metadata={
                "provided_info": request.missing_info,
                "retailer_response": request.retailer_response,
                "received_from": "retailer_portal"
            }
        )
        
        db.add(email_comm)
        await db.commit()
        
        # Log tracking
        await _log_tracking(
            db, order_id, "RETAILER_RESPONSE_RECEIVED",
            f"Retailer provided missing information: {list(request.missing_info.keys())}"
        )
        
        return {
            "success": True,
            "message": "Retailer response processed successfully",
            "data": {
                "order_id": order_id,
                "updated_fields": list(request.missing_info.keys()),
                "remaining_missing_fields": order.missing_fields or [],
                "order_status": order.status
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to handle retailer response for order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle retailer response: {str(e)}"
        )

@router.post("/{order_id}/structured-order/confirm")
async def confirm_structured_order(
    order_id: str,
    request: StructuredOrderConfirmation,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Confirm final structured order data (human-in-the-loop approval)"""
    try:
        # Verify order exists
        result = await db.execute(
            select(Order).where(Order.id == uuid.UUID(order_id))
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        if request.confirmed:
            # Apply any final corrections
            if request.corrections:
                if order.parsed_data:
                    def apply_corrections(target, corrections):
                        for key, value in corrections.items():
                            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                                apply_corrections(target[key], value)
                            else:
                                target[key] = value
                    
                    apply_corrections(order.parsed_data, request.corrections)
                
                # Update order fields
                if 'priority' in request.corrections:
                    order.priority = request.corrections['priority']
                if 'special_instructions' in request.corrections:
                    order.special_instructions = request.corrections['special_instructions']
            
            # Finalize the order
            order.parsed_data = request.order_data
            order.status = "CONFIRMED"
            order.missing_fields = None
            order.validation_errors = None
            
            # Add confirmation note
            confirmation_note = f"Order structure confirmed by retailer via email response"
            if request.corrections:
                confirmation_note += f" with corrections: {list(request.corrections.keys())}"
            
            if order.processing_notes:
                order.processing_notes += f"\n{confirmation_note}"
            else:
                order.processing_notes = confirmation_note
            
            await db.commit()
            
            # Create confirmation email record
            email_comm = EmailCommunication(
                id=uuid.uuid4(),
                order_id=uuid.UUID(order_id),
                email_type="ORDER_CONFIRMATION",
                recipient_email=current_user.email,
                subject=f"Order {order.order_number} Confirmed",
                content=f"Order {order.order_number} has been confirmed and is ready for processing",
                status="CONFIRMATION_RECEIVED",
                metadata={
                    "confirmed_data": request.order_data,
                    "corrections_applied": request.corrections,
                    "confirmed_by": "retailer_email"
                }
            )
            
            db.add(email_comm)
            await db.commit()
            
            # Log tracking
            await _log_tracking(
                db, order_id, "ORDER_CONFIRMED",
                f"Order structure confirmed by retailer"
            )
            
            return {
                "success": True,
                "message": "Order confirmed successfully",
                "data": {
                    "order_id": order_id,
                    "status": "CONFIRMED",
                    "confirmed_data": request.order_data,
                    "corrections_applied": request.corrections or {}
                }
            }
        else:
            # Order rejected
            order.status = "REJECTED"
            order.processing_notes = (order.processing_notes or "") + "\nOrder rejected by retailer"
            
            await db.commit()
            
            # Log tracking
            await _log_tracking(
                db, order_id, "ORDER_REJECTED",
                "Order rejected by retailer"
            )
            
            return {
                "success": True,
                "message": "Order rejection recorded",
                "data": {
                    "order_id": order_id,
                    "status": "REJECTED"
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to confirm structured order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm structured order: {str(e)}"
        )

@router.get("/{order_id}/email-thread")
async def get_email_thread(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete email communication thread for an order"""
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
        
        # Get all email communications
        email_result = await db.execute(
            select(EmailCommunication)
            .where(EmailCommunication.order_id == uuid.UUID(order_id))
            .order_by(EmailCommunication.created_at.asc())
        )
        emails = email_result.scalars().all()
        
        thread_data = []
        for email in emails:
            thread_data.append({
                "id": str(email.id),
                "email_type": email.email_type,
                "recipient": email.recipient_email,
                "subject": email.subject,
                "content": email.content,
                "status": email.status,
                "created_at": email.created_at.isoformat(),
                "sent_at": email.sent_at.isoformat() if email.sent_at else None,
                "approved_at": email.approved_at.isoformat() if email.approved_at else None,
                "metadata": email.metadata,
                "error_message": email.error_message
            })
        
        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "order_number": order.order_number,
                "email_thread": thread_data,
                "total_emails": len(thread_data)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get email thread for order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email thread: {str(e)}"
        )

    async def _log_tracking(self, order_id: str, event_type: str, message: str):
        """Helper method to log tracking events"""
        try:
            from app.models.tracking import OrderTracking
            tracking_entry = OrderTracking(
                id=uuid.uuid4(),
                order_id=uuid.UUID(order_id),
                event_type=event_type,
                message=message,
                details={"source": "email_workflow"},
                created_at=datetime.utcnow()
            )
            
            self.db.add(tracking_entry)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log tracking: {str(e)}")

async def _log_tracking(db: AsyncSession, order_id: str, event_type: str, message: str):
    """Helper function to log tracking events"""
    try:
        from app.models.tracking import OrderTracking
        tracking_entry = OrderTracking(
            id=uuid.uuid4(),
            order_id=uuid.UUID(order_id),
            event_type=event_type,
            message=message,
            details={"source": "email_workflow"},
            created_at=datetime.utcnow()
        )
        
        db.add(tracking_entry)
        await db.commit()
        
    except Exception as e:
        logger.error(f"Failed to log tracking: {str(e)}")
