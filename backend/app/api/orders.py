from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import aiofiles
import os
import uuid
import logging
from app.database.connection import get_db
from app.models.user import User
from app.models.order import Order
from app.models.sku_item import OrderSKUItem
from app.models.tracking import OrderTracking, EmailCommunication
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
from agents.order_processing_assistant_v2 import process_order_with_assistant

# Order processing services
from app.services.azure_functions_client import AzureFunctionsClient
from app.services.order_processing_service import OrderProcessingService
from app.services.file_parser_service import FileParserService
from app.services.order_validator_service import OrderValidatorService
from app.services.email_generator_service import EmailGeneratorService

# Azure Blob upload utility
from app.services.azure_blob_service import AzureBlobService

router = APIRouter()
logger = logging.getLogger(__name__)


# Debug endpoint to check Azure configuration
@router.get("/debug/azure-config")
async def debug_azure_config():
    """Debug endpoint to check Azure configuration"""
    return {
        "azure_storage_connection_string_configured": bool(settings.AZURE_STORAGE_CONNECTION_STRING),
        "azure_storage_container": settings.AZURE_STORAGE_CONTAINER,
        "connection_string_preview": settings.AZURE_STORAGE_CONNECTION_STRING[:50] + "..." if settings.AZURE_STORAGE_CONNECTION_STRING else None,
        "connection_string_length": len(settings.AZURE_STORAGE_CONNECTION_STRING) if settings.AZURE_STORAGE_CONNECTION_STRING else 0,
        "contains_test_key": "your-account-key" in (settings.AZURE_STORAGE_CONNECTION_STRING or "")
    }

# Test Azure blob service endpoint
@router.post("/debug/test-azure-upload")
async def test_azure_upload():
    """Test Azure blob service initialization"""
    try:
        from app.services.azure_blob_service import AzureBlobService
        connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        container_name = settings.AZURE_STORAGE_CONTAINER or "uploads"
        
        if not connection_string:
            return {"error": "No connection string configured"}
        
        # Use context manager to ensure proper cleanup
        async with AzureBlobService(connection_string, container_name) as blob_service:
            # Try to get client without actually uploading
            client = await blob_service.get_client()
            return {
                "success": True,
                "message": "Azure Blob Service initialized successfully",
                "container_name": container_name
            }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__
        }

# Azure Storage diagnostic endpoint
@router.post("/debug/azure-storage-test")
async def test_azure_storage_connection():
    """Test Azure Storage connection and authentication"""
    try:
        from app.services.azure_blob_service import AzureBlobService
        connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        container_name = settings.AZURE_STORAGE_CONTAINER or "uploads"
        
        if not connection_string:
            return {"error": "No connection string configured"}
        
        if "your-account-key" in connection_string:
            return {"error": "Connection string contains placeholder values"}
        
        # Test connection
        async with AzureBlobService(connection_string, container_name) as blob_service:
            # Validate connection
            connection_valid = await blob_service.validate_connection()
            
            if not connection_valid:
                return {
                    "success": False,
                    "error": "Connection validation failed - check credentials"
                }
            
            # Try to get container properties to test permissions
            try:
                container_client = await blob_service.get_container_client()
                properties = await container_client.get_container_properties()
                
                return {
                    "success": True,
                    "message": "Azure Storage connection test successful",
                    "container_name": container_name,
                    "container_exists": True,
                    "last_modified": properties.last_modified.isoformat() if properties.last_modified else None,
                    "connection_string_preview": connection_string[:50] + "..."
                }
            except Exception as container_error:
                return {
                    "success": False,
                    "error": f"Connection valid but failed to access container: {str(container_error)}"
                }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }

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

class AssistantProcessRequest(BaseModel):
    """Request model for assistant processing"""
    user_message: Optional[str] = None
    custom_instructions: Optional[str] = None

class AssistantProcessResponse(BaseModel):
    """Response model for assistant processing"""
    success: bool
    thread_id: Optional[str] = None
    run_id: Optional[str] = None
    response: Optional[List[str]] = None
    status: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None

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



async def upload_file_to_azure_blob(file: UploadFile, user_id: str) -> str:
    """Upload file to Azure Blob Storage and return the blob URL"""
    try:
        # Get Azure Storage connection info from settings
        connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        logger.info(f"Azure Storage Connection String configured: {bool(connection_string)}")
        if connection_string:
            logger.info(f"Connection string preview: {connection_string[:100]}...")
        
        if not connection_string or "your-account-key" in connection_string or len(connection_string) < 50:
            # Fallback to local storage if Azure not configured
            logger.warning("Azure Storage not configured properly, falling back to local storage")
            logger.warning(f"Connection string length: {len(connection_string) if connection_string else 0}")
            return await save_uploaded_file(file, user_id)
        
        logger.info(f"Using Azure Blob Storage with connection string: {connection_string[:50]}...")
        container_name = settings.AZURE_STORAGE_CONTAINER or "uploads"
        logger.info(f"Container name: {container_name}")
        
        # Use context manager to ensure proper cleanup
        async with AzureBlobService(connection_string, container_name) as blob_service:
            file_extension = os.path.splitext(file.filename)[1]
            blob_name = f"{user_id}/{uuid.uuid4()}{file_extension}"
            logger.info(f"Generated blob name: {blob_name}")
            
            await file.seek(0)
            
            # Upload to Azure Blob
            logger.info("Starting Azure Blob upload...")
            await blob_service.upload_fileobj(file, blob_name)
            url = await blob_service.get_blob_url(blob_name)
            logger.info(f"Successfully uploaded file to Azure Blob: {url}")
            return url
        
    except Exception as e:
        logger.error(f"Failed to upload to Azure Blob Storage: {str(e)}", exc_info=True)
        # Fallback to local storage
        logger.warning("Falling back to local storage due to error")
        return await save_uploaded_file(file, user_id)

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
    
    # Reset file pointer for upload
    await file.seek(0)
    
    # Save file to Azure Blob Storage
    logger.info(f"Uploading file {file.filename} for user {current_user.id}")
    file_url = await upload_file_to_azure_blob(file, str(current_user.id))
    logger.info(f"File uploaded, URL: {file_url}")
    
    # Create order record
    order = Order(
        user_id=current_user.id,
        order_number=generate_order_number(),
        status="UPLOADED",
        original_filename=file.filename,
        file_path=file_url,  # Store Azure Blob URL
        file_type=file_extension,
        file_size=len(file_content),
        priority=priority,
        special_instructions=special_instructions,
        file_metadata={
            "priority": priority,
            "special_instructions": special_instructions,
            "upload_timestamp": datetime.utcnow().isoformat(),
            "cloud_storage": "azure_blob" if file_url.startswith("https://") else "local_storage"
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

@router.get("/all", response_model=OrderListResponse)
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

@router.post("/{order_id}/process-with-assistant", response_model=AssistantProcessResponse)
async def process_order_with_ai_assistant(
    order_id: str,
    request: AssistantProcessRequest = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process an order using the AI assistant.
    
    The assistant will:
    1. Get order summary and current status
    2. Parse order file if needed
    3. Validate order data
    4. Generate emails for missing information
    5. Process SKU items and calculate totals
    6. Calculate logistics and shipping costs
    7. Apply any necessary corrections
    """
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
    
    # Check if order is in a processable status
    if order.status in ["CANCELLED", "DELIVERED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be processed in {order.status} status"
        )
    
    try:
        # Prepare user message
        user_message = None
        if request and request.user_message:
            user_message = request.user_message
        elif request and request.custom_instructions:
            user_message = f"Please process order {order_id} with these custom instructions: {request.custom_instructions}"

        # Download file from Azure Blob if needed
        # The order.file_path is now a blob URL
        # If your assistant needs the file, download it using Azure SDK
        # Example: download and pass file content to the assistant
        # (Implement as needed in process_order_with_assistant)

        result = await process_order_with_assistant(db, order_id, user_message)

        # Create tracking entry for assistant processing
        tracking = OrderTracking(
            order_id=order.id,
            status="AI_PROCESSING",
            message="Order processed with AI assistant",
            details=f"Thread ID: {result.get('thread_id', 'N/A')}, Success: {result.get('success', False)}"
        )
        db.add(tracking)

        # Update order status if processing was successful
        if result.get("success"):
            order.status = "AI_PROCESSED"
            order.updated_at = datetime.utcnow()

        await db.commit()

        return AssistantProcessResponse(**result)

    except Exception as e:
        # Create error tracking entry
        tracking = OrderTracking(
            order_id=order.id,
            status="AI_PROCESSING_ERROR",
            message="AI assistant processing failed",
            details=f"Error: {str(e)}"
        )
        db.add(tracking)
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assistant processing failed: {str(e)}"
        )

# ============================================================
# ORDER PROCESSING ENDPOINTS (merged from order_processing.py)
# ============================================================

@router.post("/{order_id}/process")
async def process_order(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Process an uploaded order with comprehensive validation and email generation"""
    return await AzureFunctionsClient().process_order_file(order_id)

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

        # Extract missing fields for email body
        missing_fields = validation_result.get("missing_fields") or validation_result.get("missing_info") or validation_result.get("missing", [])
        if missing_fields:
            missing_info_text = "\n".join(f"- {field}" for field in missing_fields)
            extra_note = f"\n\nThe following information is missing and required to process your order:\n{missing_info_text}"
        else:
            extra_note = ""

        # Generate email
        email_service = EmailGeneratorService(db)
        email_result = await email_service.generate_missing_info_email(
            order_id, validation_result, order.parsed_data, extra_note=extra_note
        )

        return {
            "success": True,
            "message": "Draft email generated successfully",
            "data": email_result,
            "missing_fields": missing_fields
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

# ============================================================
# UTILITY FUNCTIONS FOR ORDER PROCESSING
# ============================================================

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
