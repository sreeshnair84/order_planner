from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
import uuid

from app.database.connection import get_db
from app.models.tracking import EmailCommunication
from app.models.order import Order
from app.models.user import User
from app.api.auth import get_current_user
from app.services.email_service import EmailService
from app.services.order_processing_service import OrderProcessingService
from pydantic import BaseModel

router = APIRouter()

class EmailResponse(BaseModel):
    id: str
    order_id: str
    email_type: str
    subject: str
    recipient: str
    sender: Optional[str]
    body: str
    sent_at: Optional[datetime]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class EmailSendRequest(BaseModel):
    order_id: str
    email_type: str
    recipient: str
    subject: str
    body: str

class OrderConsolidationRequest(BaseModel):
    order_ids: List[str]
    consolidation_notes: Optional[str] = None

@router.get("/emails", response_model=List[EmailResponse])
async def get_emails(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    order_id: Optional[str] = Query(None),
    email_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get email communications"""
    query = select(EmailCommunication).options(
        selectinload(EmailCommunication.order)
    )
    
    if order_id:
        query = query.where(EmailCommunication.order_id == uuid.UUID(order_id))
    
    if email_type:
        query = query.where(EmailCommunication.email_type == email_type)
    
    if status:
        query = query.where(EmailCommunication.status == status)
    
    query = query.offset(skip).limit(limit).order_by(EmailCommunication.created_at.desc())
    result = await db.execute(query)
    emails = result.scalars().all()
    
    return [
        EmailResponse(
            id=str(email.id),
            order_id=str(email.order_id),
            email_type=email.email_type,
            subject=email.subject or "",
            recipient=email.recipient,
            sender=email.sender,
            body=email.body or "",
            sent_at=email.sent_at,
            status=email.status,
            created_at=email.created_at
        )
        for email in emails
    ]

@router.get("/emails/{email_id}", response_model=EmailResponse)
async def get_email(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get email by ID"""
    query = select(EmailCommunication).options(
        selectinload(EmailCommunication.order)
    ).where(EmailCommunication.id == uuid.UUID(email_id))
    
    result = await db.execute(query)
    email = result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return EmailResponse(
        id=str(email.id),
        order_id=str(email.order_id),
        email_type=email.email_type,
        subject=email.subject or "",
        recipient=email.recipient,
        sender=email.sender,
        body=email.body or "",
        sent_at=email.sent_at,
        status=email.status,
        created_at=email.created_at
    )

@router.post("/emails/send")
async def send_email(
    email_request: EmailSendRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send email for an order"""
    # Check if order exists
    order_query = select(Order).where(Order.id == uuid.UUID(email_request.order_id))
    order_result = await db.execute(order_query)
    order = order_result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Create email communication record
    email_communication = EmailCommunication(
        order_id=order.id,
        email_type=email_request.email_type,
        subject=email_request.subject,
        recipient=email_request.recipient,
        sender=current_user.email,
        body=email_request.body,
        status="PENDING"
    )
    
    db.add(email_communication)
    await db.commit()
    await db.refresh(email_communication)
    
    # Send email in background
    email_service = EmailService()
    background_tasks.add_task(
        email_service.send_email,
        email_communication.id,
        db
    )
    
    return {
        "message": "Email queued for sending",
        "email_id": str(email_communication.id)
    }

@router.post("/emails/{email_id}/resend")
async def resend_email(
    email_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resend an email"""
    query = select(EmailCommunication).where(EmailCommunication.id == uuid.UUID(email_id))
    result = await db.execute(query)
    email = result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Update status to pending
    email.status = "PENDING"
    email.sent_at = None
    await db.commit()
    
    # Send email in background
    email_service = EmailService()
    background_tasks.add_task(
        email_service.send_email,
        email.id,
        db
    )
    
    return {"message": "Email queued for resending"}

@router.post("/requestedorders/{order_id}/trigger-processing")
async def trigger_order_processing(
    order_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger order processing"""
    # Check if order exists
    order_query = select(Order).where(Order.id == uuid.UUID(order_id))
    order_result = await db.execute(order_query)
    order = order_result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if order can be processed
    if order.status in ["PROCESSING", "COMPLETED", "DELIVERED"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Order cannot be processed from status: {order.status}"
        )
    
    # Update order status
    order.status = "PROCESSING"
    order.updated_at = datetime.utcnow()
    await db.commit()
    
    # Trigger processing in background
    processing_service = OrderProcessingService(db)
    background_tasks.add_task(
        processing_service.process_order,
        str(order.id)
    )
    
    return {"message": "Order processing triggered", "order_id": str(order.id)}

@router.post("/requestedorders/consolidate")
async def consolidate_orders(
    consolidation_request: OrderConsolidationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Consolidate multiple orders"""
    order_ids = [uuid.UUID(order_id) for order_id in consolidation_request.order_ids]
    
    # Check if all orders exist
    orders_query = select(Order).where(Order.id.in_(order_ids))
    orders_result = await db.execute(orders_query)
    orders = orders_result.scalars().all()
    
    if len(orders) != len(order_ids):
        raise HTTPException(status_code=404, detail="One or more orders not found")
    
    # Check if orders can be consolidated
    for order in orders:
        if order.status not in ["UPLOADED", "PARSED", "VALIDATED", "ASSIGNED"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Order {order.order_number} cannot be consolidated from status: {order.status}"
            )
    
    # Check if orders have same manufacturer (if assigned)
    manufacturers = set(order.manufacturer_id for order in orders if order.manufacturer_id)
    if len(manufacturers) > 1:
        raise HTTPException(
            status_code=400, 
            detail="Orders must have the same manufacturer to be consolidated"
        )
    
    # Update order statuses
    for order in orders:
        order.status = "CONSOLIDATING"
        order.updated_at = datetime.utcnow()
    
    await db.commit()
    
    # Trigger consolidation in background
    processing_service = OrderProcessingService(db)
    background_tasks.add_task(
        processing_service.consolidate_orders,
        consolidation_request.order_ids,
        consolidation_request.consolidation_notes
    )
    
    return {
        "message": "Order consolidation triggered",
        "order_ids": consolidation_request.order_ids,
        "order_count": len(consolidation_request.order_ids)
    }

@router.get("/requestedorders/{order_id}/emails", response_model=List[EmailResponse])
async def get_order_emails(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all emails for a specific order"""
    query = select(EmailCommunication).where(
        EmailCommunication.order_id == uuid.UUID(order_id)
    ).order_by(EmailCommunication.created_at.desc())
    
    result = await db.execute(query)
    emails = result.scalars().all()
    
    return [
        EmailResponse(
            id=str(email.id),
            order_id=str(email.order_id),
            email_type=email.email_type,
            subject=email.subject or "",
            recipient=email.recipient,
            sender=email.sender,
            body=email.body or "",
            sent_at=email.sent_at,
            status=email.status,
            created_at=email.created_at
        )
        for email in emails
    ]

@router.get("/email-types")
async def get_email_types():
    """Get available email types"""
    return [
        {"value": "ORDER_CONFIRMATION", "label": "Order Confirmation"},
        {"value": "ORDER_UPDATE", "label": "Order Update"},
        {"value": "DELIVERY_NOTIFICATION", "label": "Delivery Notification"},
        {"value": "INVOICE", "label": "Invoice"},
        {"value": "PAYMENT_REMINDER", "label": "Payment Reminder"},
        {"value": "CUSTOMER_INQUIRY", "label": "Customer Inquiry"},
        {"value": "MANUFACTURER_NOTIFICATION", "label": "Manufacturer Notification"},
        {"value": "CONSOLIDATION_NOTICE", "label": "Consolidation Notice"},
        {"value": "ERROR_NOTIFICATION", "label": "Error Notification"}
    ]

@router.get("/requestedorders/{order_id}/actions")
async def get_order_actions(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available actions for an order"""
    order_query = select(Order).where(Order.id == uuid.UUID(order_id))
    order_result = await db.execute(order_query)
    order = order_result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    actions = []
    
    # Determine available actions based on order status
    if order.status in ["UPLOADED", "PARSED", "VALIDATED", "ERROR"]:
        actions.append({
            "action": "trigger_processing",
            "label": "Trigger Processing",
            "description": "Start order processing"
        })
    
    if order.status in ["UPLOADED", "PARSED", "VALIDATED", "ASSIGNED"]:
        actions.append({
            "action": "consolidate",
            "label": "Consolidate Orders",
            "description": "Consolidate with other orders"
        })
    
    if order.status != "CANCELLED":
        actions.append({
            "action": "send_email",
            "label": "Send Email",
            "description": "Send email notification"
        })
    
    if order.status in ["ASSIGNED", "PROCESSING"]:
        actions.append({
            "action": "assign_manufacturer",
            "label": "Reassign Manufacturer",
            "description": "Change manufacturer assignment"
        })
    
    return {
        "order_id": str(order.id),
        "order_number": order.order_number,
        "status": order.status,
        "actions": actions
    }
