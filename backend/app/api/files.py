from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
from app.database.connection import get_db
from app.models.user import User
from app.models.order import Order
from app.api.auth import get_current_user
from app.utils.config import settings

router = APIRouter()

# Pydantic models
class FileInfo(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    upload_date: str

class FileListResponse(BaseModel):
    files: List[FileInfo]
    total: int

# API endpoints
@router.get("/", response_model=FileListResponse)
async def list_files(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get all orders with files for the current user
    result = await db.execute(
        select(Order)
        .where(Order.user_id == current_user.id)
        .where(Order.original_filename.isnot(None))
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    
    files = [
        FileInfo(
            id=str(order.id),
            filename=order.original_filename,
            file_type=order.file_type,
            file_size=order.file_size or 0,
            upload_date=order.created_at.isoformat()
        )
        for order in orders
    ]
    
    return FileListResponse(
        files=files,
        total=len(files)
    )

@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get order
    result = await db.execute(
        select(Order).where(
            Order.id == uuid.UUID(file_id),
            Order.user_id == current_user.id
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if not order.file_path or not os.path.exists(order.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        path=order.file_path,
        filename=order.original_filename,
        media_type='application/octet-stream'
    )

@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get order
    result = await db.execute(
        select(Order).where(
            Order.id == uuid.UUID(file_id),
            Order.user_id == current_user.id
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check if order can be deleted
    if order.status in ["DELIVERED", "IN_TRANSIT", "SUBMITTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete file for orders in this status"
        )
    
    # Delete file from disk
    if order.file_path and os.path.exists(order.file_path):
        try:
            os.remove(order.file_path)
        except OSError as e:
            # Log error but don't fail the request
            pass
    
    # Delete order record
    await db.delete(order)
    await db.commit()
    
    return {"message": "File deleted successfully"}

@router.get("/{file_id}/info", response_model=FileInfo)
async def get_file_info(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get order
    result = await db.execute(
        select(Order).where(
            Order.id == uuid.UUID(file_id),
            Order.user_id == current_user.id
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileInfo(
        id=str(order.id),
        filename=order.original_filename,
        file_type=order.file_type,
        file_size=order.file_size or 0,
        upload_date=order.created_at.isoformat()
    )
