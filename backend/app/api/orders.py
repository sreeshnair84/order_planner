from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import aiofiles
import os
import uuid
from app.database.connection import get_db
from app.models.user import User
from app.models.order import Order
from app.models.sku_item import OrderSKUItem
from app.models.tracking import OrderTracking
from app.models.schemas import (
    OrderDetailedResponse, 
    OrderCreateRequest, 
    SKUItemResponse, 
    TripInfo,
    OrderStatusUpdateRequest
)
from app.api.auth import get_current_user
from app.services.file_processor import FileProcessor
from app.services.sku_service import SKUService
from app.utils.config import settings

router = APIRouter()

# Pydantic models
class OrderResponse(BaseModel):
    id: str
    order_number: str
    status: str
    original_filename: Optional[str]
    file_type: Optional[str]
    priority: str
    total_sku_count: int
    total_quantity: int
    subtotal: float
    total: float
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_order(cls, order: Order):
        """Factory method to create OrderResponse from Order model"""
        return cls(
            id=str(order.id),
            order_number=order.order_number,
            status=order.status,
            original_filename=order.original_filename,
            file_type=order.file_type,
            priority=order.priority or "NORMAL",
            total_sku_count=order.total_sku_count or 0,
            total_quantity=order.total_quantity or 0,
            subtotal=float(order.subtotal or 0),
            total=float(order.total or 0),
            created_at=order.created_at,
            updated_at=order.updated_at or order.created_at
        )

class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    per_page: int

# Utility functions
def generate_order_number() -> str:
    return f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

async def save_uploaded_file(file: UploadFile, user_id: str) -> str:
    """Save uploaded file to disk and return the file path"""
    # Create user-specific upload directory
    user_upload_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    os.makedirs(user_upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(user_upload_dir, unique_filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return file_path

# API endpoints
@router.post("/upload", response_model=OrderResponse)
async def upload_order(
    file: UploadFile = File(...),
    priority: str = Form("NORMAL"),
    special_instructions: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file selected"
        )
    
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {settings.ALLOWED_FILE_TYPES}"
        )
    
    # Validate file size
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
        )
    
    # Reset file pointer
    await file.seek(0)
    
    # Save file
    file_path = await save_uploaded_file(file, str(current_user.id))
    
    # Create order record
    order = Order(
        user_id=current_user.id,
        order_number=generate_order_number(),
        status="UPLOADED",
        original_filename=file.filename,
        file_path=file_path,
        file_type=file_extension,
        file_size=len(file_content),
        priority=priority,
        special_instructions=special_instructions,
        file_metadata={
            "priority": priority,
            "special_instructions": special_instructions,
            "upload_timestamp": datetime.utcnow().isoformat()
        }
    )
    
    db.add(order)
    await db.commit()
    await db.refresh(order)
    
    # Create tracking entry
    tracking = OrderTracking(
        order_id=order.id,
        status="UPLOADED",
        message="File uploaded successfully",
        details=f"File: {file.filename}, Size: {len(file_content)} bytes"
    )
    db.add(tracking)
    await db.commit()
    
    # Start background processing
    # TODO: Add background task to process file
    
    return OrderResponse.from_order(order)

@router.get("/", response_model=OrderListResponse)
async def get_orders(
    page: int = 1,
    per_page: int = 10,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Build query
    query = select(Order).where(Order.user_id == current_user.id)
    if status:
        query = query.where(Order.status == status)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(Order.created_at.desc())
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    order_responses = [
        OrderResponse.from_order(order)
        for order in orders
    ]
    
    return OrderListResponse(
        orders=order_responses,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
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
            detail="Order not found"
        )
    
    return OrderResponse.from_order(order)

@router.delete("/{order_id}")
async def cancel_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
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
            detail="Order not found"
        )
    
    # Check if order can be cancelled
    if order.status in ["DELIVERED", "CANCELLED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order cannot be cancelled"
        )
    
    order.status = "CANCELLED"
    await db.commit()
    
    # Create tracking entry
    tracking = OrderTracking(
        order_id=order.id,
        status="CANCELLED",
        message="Order cancelled by user"
    )
    db.add(tracking)
    await db.commit()
    
    return {"message": "Order cancelled successfully"}

# New API endpoints for enhanced functionality

@router.get("/{order_id}/details", response_model=OrderDetailedResponse)
async def get_order_details(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed order information including SKU items"""
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
            detail="Order not found"
        )
    
    # Get SKU items
    sku_service = SKUService(db)
    sku_items = await sku_service.get_sku_items_by_order(str(order.id))
    sku_responses = [sku_service.convert_to_response(item) for item in sku_items]
    
    return OrderDetailedResponse(
        id=str(order.id),
        order_number=order.order_number,
        status=order.status,
        original_filename=order.original_filename,
        file_type=order.file_type,
        priority=order.priority or "NORMAL",
        special_instructions=order.special_instructions,
        requested_delivery_date=order.requested_delivery_date,
        delivery_address=order.delivery_address,
        retailer_info=order.retailer_info,
        total_sku_count=order.total_sku_count or 0,
        total_quantity=order.total_quantity or 0,
        total_weight_kg=order.total_weight_kg or 0,
        total_volume_m3=order.total_volume_m3 or 0,
        subtotal=order.subtotal or 0,
        tax=order.tax or 0,
        total=order.total or 0,
        trip_id=order.trip_id,
        trip_status=order.trip_status,
        estimated_delivery_date=order.estimated_delivery_date,
        sku_items=sku_responses,
        missing_fields=order.missing_fields,
        validation_errors=order.validation_errors,
        processing_notes=order.processing_notes,
        created_at=order.created_at,
        updated_at=order.updated_at or order.created_at
    )

@router.get("/{order_id}/sku-details", response_model=List[SKUItemResponse])
async def get_order_sku_details(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed SKU information for an order"""
    # Verify order exists and belongs to user
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
            detail="Order not found"
        )
    
    sku_service = SKUService(db)
    sku_items = await sku_service.get_sku_items_by_order(order_id)
    
    return [sku_service.convert_to_response(item) for item in sku_items]

@router.get("/{order_id}/trip-info", response_model=TripInfo)
async def get_order_trip_info(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get trip information for an order"""
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
            detail="Order not found"
        )
    
    if not order.trip_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip information not available"
        )
    
    # In a real implementation, this would fetch from a logistics system
    # For now, return mock data based on order information
    return TripInfo(
        trip_id=order.trip_id,
        trip_status=order.trip_status or "PLANNED",
        estimated_delivery_date=order.estimated_delivery_date,
        actual_delivery_date=None,
        driver_name="To be assigned",
        driver_contact=None,
        vehicle_info=None,
        route_info=None
    )

@router.post("/{order_id}/reschedule")
async def reschedule_order(
    order_id: str,
    reschedule_request: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reschedule order delivery"""
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
            detail="Order not found"
        )
    
    # Check if order can be rescheduled
    if order.status in ["DELIVERED", "CANCELLED", "REJECTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order cannot be rescheduled"
        )
    
    # Update delivery date
    new_delivery_date = reschedule_request.get("requested_delivery_date")
    if new_delivery_date:
        order.requested_delivery_date = datetime.fromisoformat(new_delivery_date)
        order.estimated_delivery_date = datetime.fromisoformat(new_delivery_date)
    
    # Add tracking entry
    tracking = OrderTracking(
        order_id=order.id,
        status="RESCHEDULED",
        message=f"Order rescheduled to {new_delivery_date}",
        details=f"Rescheduled by {current_user.email}"
    )
    
    db.add(tracking)
    await db.commit()
    
    return {"message": "Order rescheduled successfully"}

@router.post("/{order_id}/update-status")
async def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update order status with logistics information"""
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
            detail="Order not found"
        )
    
    # Update order status
    order.status = status_update.status
    
    # Update trip information if provided
    if status_update.trip_id:
        order.trip_id = status_update.trip_id
        order.trip_status = "ASSIGNED"
    
    if status_update.estimated_delivery_date:
        order.estimated_delivery_date = status_update.estimated_delivery_date
    
    # Create tracking entry
    tracking = OrderTracking(
        order_id=order.id,
        status=status_update.status,
        message=status_update.message,
        details=status_update.details
    )
    
    db.add(tracking)
    await db.commit()
    
    return {"message": "Order status updated successfully"}
