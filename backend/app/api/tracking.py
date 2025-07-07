from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid
from app.database.connection import get_db
from app.models.user import User
from app.models.order import Order
from app.models.tracking import OrderTracking
from app.api.auth import get_current_user

router = APIRouter()

# Enhanced Pydantic models with new status flow
class TrackingEntry(BaseModel):
    id: str
    status: str = Field(..., pattern="^(UPLOADED|PROCESSING|PENDING_INFO|INFO_RECEIVED|VALIDATED|TRIP_QUEUED|TRIP_PLANNED|SUBMITTED|CONFIRMED|IN_TRANSIT|DELIVERED|REJECTED|CANCELLED)$")
    message: Optional[str]
    details: Optional[str]
    created_at: datetime

class OrderTrackingResponse(BaseModel):
    order_id: str
    order_number: str
    current_status: str
    tracking_entries: List[TrackingEntry]
    trip_info: Optional[dict] = None

class OrderStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(UPLOADED|PROCESSING|PENDING_INFO|INFO_RECEIVED|VALIDATED|TRIP_QUEUED|TRIP_PLANNED|SUBMITTED|CONFIRMED|IN_TRANSIT|DELIVERED|REJECTED|CANCELLED)$")
    message: Optional[str] = None
    details: Optional[str] = None

# Status flow validation
VALID_STATUS_TRANSITIONS = {
    "UPLOADED": ["PROCESSING", "CANCELLED"],
    "PROCESSING": ["PENDING_INFO", "VALIDATED", "REJECTED"],
    "PENDING_INFO": ["INFO_RECEIVED", "CANCELLED"],
    "INFO_RECEIVED": ["PROCESSING", "VALIDATED"],
    "VALIDATED": ["TRIP_QUEUED", "SUBMITTED"],
    "TRIP_QUEUED": ["TRIP_PLANNED", "CANCELLED"],
    "TRIP_PLANNED": ["SUBMITTED", "CANCELLED"],
    "SUBMITTED": ["CONFIRMED", "REJECTED"],
    "CONFIRMED": ["IN_TRANSIT"],
    "IN_TRANSIT": ["DELIVERED"],
    "DELIVERED": [],  # Final state
    "REJECTED": [],   # Final state
    "CANCELLED": []   # Final state
}

def validate_status_transition(current_status: str, new_status: str) -> bool:
    """Validate if status transition is allowed"""
    return new_status in VALID_STATUS_TRANSITIONS.get(current_status, [])

# API endpoints
@router.get("/{order_id}", response_model=OrderTrackingResponse)
async def get_order_tracking(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get order
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
            detail="Order not found"
        )
    
    # Get tracking entries
    tracking_result = await db.execute(
        select(OrderTracking)
        .where(OrderTracking.order_id == uuid.UUID(order_id))
        .order_by(OrderTracking.created_at.desc())
    )
    tracking_entries = tracking_result.scalars().all()
    
    tracking_list = [
        TrackingEntry(
            id=str(entry.id),
            status=entry.status,
            message=entry.message,
            details=entry.details,
            created_at=entry.created_at
        )
        for entry in tracking_entries
    ]
    
    return OrderTrackingResponse(
        order_id=str(order.id),
        order_number=order.order_number,
        current_status=order.status,
        tracking_entries=tracking_list
    )

@router.get("/", response_model=List[OrderTrackingResponse])
async def get_all_orders_tracking(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get all orders for user
    orders_result = await db.execute(
        select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    )
    orders = orders_result.scalars().all()
    
    tracking_responses = []
    for order in orders:
        # Get tracking entries for each order
        tracking_result = await db.execute(
            select(OrderTracking)
            .where(OrderTracking.order_id == order.id)
            .order_by(OrderTracking.created_at.desc())
        )
        tracking_entries = tracking_result.scalars().all()
        
        tracking_list = [
            TrackingEntry(
                id=str(entry.id),
                status=entry.status,
                message=entry.message,
                details=entry.details,
                created_at=entry.created_at
            )
            for entry in tracking_entries
        ]
        
        tracking_responses.append(
            OrderTrackingResponse(
                order_id=str(order.id),
                order_number=order.order_number,
                current_status=order.status,
                tracking_entries=tracking_list
            )
        )
    
    return tracking_responses

@router.post("/{order_id}/status", response_model=TrackingEntry)
async def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get order
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
            detail="Order not found"
        )
    
    # Validate status transition
    if not validate_status_transition(order.status, status_update.status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from {order.status} to {status_update.status}"
        )
    
    # Update order status
    order.status = status_update.status
    
    # Handle specific status logic
    if status_update.status == "TRIP_PLANNED":
        # Generate trip ID if not exists
        if not order.trip_id:
            order.trip_id = f"TRIP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            order.trip_status = "PLANNED"
    
    elif status_update.status == "IN_TRANSIT":
        order.trip_status = "IN_TRANSIT"
    
    elif status_update.status == "DELIVERED":
        order.trip_status = "COMPLETED"
    
    # Create tracking entry
    tracking = OrderTracking(
        order_id=order.id,
        status=status_update.status,
        message=status_update.message,
        details=status_update.details
    )
    
    db.add(tracking)
    await db.commit()
    await db.refresh(tracking)
    
    return TrackingEntry(
        id=str(tracking.id),
        status=tracking.status,
        message=tracking.message,
        details=tracking.details,
        created_at=tracking.created_at
    )
