from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
import uuid

from app.database.connection import get_db
from app.models.retailer import Manufacturer, Retailer, retailer_manufacturer_association
from app.models.order import Order
from app.models.user import User
from app.api.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()

class ManufacturerCreate(BaseModel):
    name: str
    code: str
    contact_email: str
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None
    lead_time_days: Optional[int] = 7
    min_order_value: Optional[int] = 0
    preferred_payment_terms: Optional[str] = None

class ManufacturerUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None
    lead_time_days: Optional[int] = None
    min_order_value: Optional[int] = None
    preferred_payment_terms: Optional[str] = None
    is_active: Optional[bool] = None

class ManufacturerResponse(BaseModel):
    id: int
    name: str
    code: str
    contact_email: str
    contact_phone: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    country: Optional[str]
    is_active: bool
    notes: Optional[str]
    lead_time_days: int
    min_order_value: int
    preferred_payment_terms: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ManufacturerWithStats(ManufacturerResponse):
    retailer_count: int
    active_orders: int
    total_orders: int

class OrderAssignmentRequest(BaseModel):
    order_id: str
    manufacturer_id: int
    retailer_id: Optional[int] = None
    assignment_notes: Optional[str] = None

@router.get("/manufacturers", response_model=List[ManufacturerWithStats])
async def get_manufacturers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all manufacturers with statistics"""
    query = select(Manufacturer).options(
        selectinload(Manufacturer.retailers),
        selectinload(Manufacturer.orders)
    )
    
    if active_only:
        query = query.where(Manufacturer.is_active == True)
    
    if search:
        query = query.where(
            or_(
                Manufacturer.name.ilike(f"%{search}%"),
                Manufacturer.code.ilike(f"%{search}%"),
                Manufacturer.contact_email.ilike(f"%{search}%")
            )
        )
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    manufacturers = result.scalars().all()
    
    manufacturers_with_stats = []
    for manufacturer in manufacturers:
        manufacturers_with_stats.append(ManufacturerWithStats(
            **manufacturer.__dict__,
            retailer_count=len(manufacturer.retailers),
            active_orders=len([o for o in manufacturer.orders if o.status not in ['DELIVERED', 'CANCELLED', 'ERROR']]),
            total_orders=len(manufacturer.orders)
        ))
    
    return manufacturers_with_stats

@router.post("/manufacturers", response_model=ManufacturerResponse)
async def create_manufacturer(
    manufacturer_data: ManufacturerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new manufacturer"""
    # Check if code already exists
    existing_query = select(Manufacturer).where(Manufacturer.code == manufacturer_data.code)
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Manufacturer code already exists")
    
    manufacturer = Manufacturer(**manufacturer_data.dict())
    db.add(manufacturer)
    await db.commit()
    await db.refresh(manufacturer)
    
    return manufacturer

@router.get("/manufacturers/{manufacturer_id}", response_model=ManufacturerWithStats)
async def get_manufacturer(
    manufacturer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get manufacturer by ID"""
    query = select(Manufacturer).options(
        selectinload(Manufacturer.retailers),
        selectinload(Manufacturer.orders)
    ).where(Manufacturer.id == manufacturer_id)
    
    result = await db.execute(query)
    manufacturer = result.scalar_one_or_none()
    
    if not manufacturer:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    
    return ManufacturerWithStats(
        **manufacturer.__dict__,
        retailer_count=len(manufacturer.retailers),
        active_orders=len([o for o in manufacturer.orders if o.status not in ['DELIVERED', 'CANCELLED', 'ERROR']]),
        total_orders=len(manufacturer.orders)
    )

@router.put("/manufacturers/{manufacturer_id}", response_model=ManufacturerResponse)
async def update_manufacturer(
    manufacturer_id: int,
    manufacturer_update: ManufacturerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update manufacturer"""
    query = select(Manufacturer).where(Manufacturer.id == manufacturer_id)
    result = await db.execute(query)
    manufacturer = result.scalar_one_or_none()
    
    if not manufacturer:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    
    # Check if code already exists (if being updated)
    if manufacturer_update.code and manufacturer_update.code != manufacturer.code:
        existing_query = select(Manufacturer).where(Manufacturer.code == manufacturer_update.code)
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Manufacturer code already exists")
    
    update_data = manufacturer_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(manufacturer, field, value)
    
    manufacturer.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(manufacturer)
    
    return manufacturer

@router.delete("/manufacturers/{manufacturer_id}")
async def delete_manufacturer(
    manufacturer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete manufacturer"""
    query = select(Manufacturer).where(Manufacturer.id == manufacturer_id)
    result = await db.execute(query)
    manufacturer = result.scalar_one_or_none()
    
    if not manufacturer:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    
    # Check if manufacturer has active orders
    orders_query = select(Order).where(
        and_(
            Order.manufacturer_id == manufacturer_id,
            Order.status.not_in(['DELIVERED', 'CANCELLED', 'ERROR'])
        )
    )
    orders_result = await db.execute(orders_query)
    active_orders = orders_result.scalars().all()
    
    if active_orders:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete manufacturer with {len(active_orders)} active orders"
        )
    
    await db.delete(manufacturer)
    await db.commit()
    
    return {"message": "Manufacturer deleted successfully"}

@router.post("/manufacturers/{manufacturer_id}/assign-retailer/{retailer_id}")
async def assign_retailer_to_manufacturer(
    manufacturer_id: int,
    retailer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign retailer to manufacturer"""
    # Check if manufacturer exists
    manufacturer_query = select(Manufacturer).where(Manufacturer.id == manufacturer_id)
    manufacturer_result = await db.execute(manufacturer_query)
    manufacturer = manufacturer_result.scalar_one_or_none()
    
    if not manufacturer:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    
    # Check if retailer exists
    retailer_query = select(Retailer).where(Retailer.id == retailer_id)
    retailer_result = await db.execute(retailer_query)
    retailer = retailer_result.scalar_one_or_none()
    
    if not retailer:
        raise HTTPException(status_code=404, detail="Retailer not found")
    
    # Check if relationship already exists
    existing_query = select(retailer_manufacturer_association).where(
        and_(
            retailer_manufacturer_association.c.retailer_id == retailer_id,
            retailer_manufacturer_association.c.manufacturer_id == manufacturer_id
        )
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Retailer already assigned to manufacturer")
    
    # Create association
    stmt = retailer_manufacturer_association.insert().values(
        retailer_id=retailer_id,
        manufacturer_id=manufacturer_id
    )
    await db.execute(stmt)
    await db.commit()
    
    return {"message": "Retailer assigned to manufacturer successfully"}

@router.delete("/manufacturers/{manufacturer_id}/unassign-retailer/{retailer_id}")
async def unassign_retailer_from_manufacturer(
    manufacturer_id: int,
    retailer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unassign retailer from manufacturer"""
    # Check if relationship exists
    existing_query = select(retailer_manufacturer_association).where(
        and_(
            retailer_manufacturer_association.c.retailer_id == retailer_id,
            retailer_manufacturer_association.c.manufacturer_id == manufacturer_id
        )
    )
    existing_result = await db.execute(existing_query)
    if not existing_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Retailer not assigned to manufacturer")
    
    # Remove association
    stmt = retailer_manufacturer_association.delete().where(
        and_(
            retailer_manufacturer_association.c.retailer_id == retailer_id,
            retailer_manufacturer_association.c.manufacturer_id == manufacturer_id
        )
    )
    await db.execute(stmt)
    await db.commit()
    
    return {"message": "Retailer unassigned from manufacturer successfully"}

@router.post("/requestedorders/assign-manufacturer")
async def assign_manufacturer_to_order(
    assignment: OrderAssignmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign manufacturer to order (FMCG function)"""
    # Check if order exists
    order_query = select(Order).where(Order.id == uuid.UUID(assignment.order_id))
    order_result = await db.execute(order_query)
    order = order_result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if manufacturer exists
    manufacturer_query = select(Manufacturer).where(Manufacturer.id == assignment.manufacturer_id)
    manufacturer_result = await db.execute(manufacturer_query)
    manufacturer = manufacturer_result.scalar_one_or_none()
    
    if not manufacturer:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    
    # Check if retailer exists (if provided)
    if assignment.retailer_id:
        retailer_query = select(Retailer).where(Retailer.id == assignment.retailer_id)
        retailer_result = await db.execute(retailer_query)
        retailer = retailer_result.scalar_one_or_none()
        
        if not retailer:
            raise HTTPException(status_code=404, detail="Retailer not found")
        
        # Check if retailer is assigned to manufacturer
        association_query = select(retailer_manufacturer_association).where(
            and_(
                retailer_manufacturer_association.c.retailer_id == assignment.retailer_id,
                retailer_manufacturer_association.c.manufacturer_id == assignment.manufacturer_id
            )
        )
        association_result = await db.execute(association_query)
        if not association_result.scalar_one_or_none():
            raise HTTPException(
                status_code=400, 
                detail="Retailer is not assigned to the selected manufacturer"
            )
    
    # Update order with manufacturer assignment
    order.manufacturer_id = assignment.manufacturer_id
    order.retailer_id = assignment.retailer_id
    order.assigned_by = current_user.id
    order.assigned_at = datetime.utcnow()
    order.assignment_notes = assignment.assignment_notes
    order.status = "ASSIGNED"
    order.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(order)
    
    return {"message": "Manufacturer assigned to order successfully", "order_id": str(order.id)}

@router.get("/manufacturers/{manufacturer_id}/requestedorders")
async def get_manufacturer_orders(
    manufacturer_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get orders assigned to a manufacturer"""
    query = select(Order).options(
        selectinload(Order.retailer),
        selectinload(Order.assigner),
        selectinload(Order.sku_items)
    ).where(Order.manufacturer_id == manufacturer_id)
    
    if status:
        query = query.where(Order.status == status)
    
    query = query.offset(skip).limit(limit).order_by(Order.created_at.desc())
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return [
        {
            "id": str(order.id),
            "order_number": order.order_number,
            "status": order.status,
            "retailer": order.retailer.name if order.retailer else None,
            "assigned_by": order.assigner.username if order.assigner else None,
            "assigned_at": order.assigned_at,
            "assignment_notes": order.assignment_notes,
            "total_quantity": order.total_quantity,
            "total": float(order.total) if order.total else 0,
            "requested_delivery_date": order.requested_delivery_date,
            "created_at": order.created_at,
            "sku_count": len(order.sku_items)
        }
        for order in orders
    ]
