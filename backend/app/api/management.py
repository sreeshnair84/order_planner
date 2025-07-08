from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.database.connection import get_db
from app.models.retailer import Retailer, Manufacturer, Route
from app.models.retailer_schemas import (
    RetailerCreate, RetailerUpdate, RetailerResponse, RetailerListResponse,
    ManufacturerCreate, ManufacturerUpdate, ManufacturerResponse, ManufacturerListResponse,
    RouteCreate, RouteUpdate, RouteResponse, RouteListResponse
)
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter()

# Retailer endpoints
@router.get("/retailers", response_model=RetailerListResponse)
async def get_retailers(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of retailers with optional search and filtering."""
    query = select(Retailer).options(selectinload(Retailer.manufacturers))
    
    if active_only:
        query = query.where(Retailer.is_active == True)
    
    if search:
        query = query.where(
            (Retailer.name.ilike(f"%{search}%")) |
            (Retailer.code.ilike(f"%{search}%")) |
            (Retailer.contact_email.ilike(f"%{search}%"))
        )
    
    # Get total count
    total_query = select(func.count(Retailer.id))
    if active_only:
        total_query = total_query.where(Retailer.is_active == True)
    if search:
        total_query = total_query.where(
            (Retailer.name.ilike(f"%{search}%")) |
            (Retailer.code.ilike(f"%{search}%")) |
            (Retailer.contact_email.ilike(f"%{search}%"))
        )
    
    total_result = await db.execute(total_query)
    total = total_result.scalar()
    
    # Get paginated results
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    retailers = result.scalars().all()
    
    return RetailerListResponse(
        retailers=retailers,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/retailers/dropdown")
async def get_retailers_dropdown(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get simplified list of retailers for dropdown menus."""
    query = select(Retailer).where(Retailer.is_active == True)
    result = await db.execute(query)
    retailers = result.scalars().all()
    return [{"id": r.id, "name": r.name, "code": r.code} for r in retailers]

@router.get("/retailers/{retailer_id}", response_model=RetailerResponse)
async def get_retailer(
    retailer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific retailer by ID."""
    query = select(Retailer).options(selectinload(Retailer.manufacturers)).where(Retailer.id == retailer_id)
    result = await db.execute(query)
    retailer = result.scalar_one_or_none()
    if not retailer:
        raise HTTPException(status_code=404, detail="Retailer not found")
    return retailer

@router.post("/retailers", response_model=RetailerResponse)
async def create_retailer(
    retailer_data: RetailerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new retailer."""
    # Check if code already exists
    existing_query = select(Retailer).where(Retailer.code == retailer_data.code)
    existing_result = await db.execute(existing_query)
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Retailer code already exists")
    
    # Create retailer
    retailer = Retailer(**retailer_data.model_dump(exclude={"manufacturer_ids"}))
    db.add(retailer)
    await db.flush()
    
    # Link manufacturers
    if retailer_data.manufacturer_ids:
        manufacturers_query = select(Manufacturer).where(
            Manufacturer.id.in_(retailer_data.manufacturer_ids)
        )
        manufacturers_result = await db.execute(manufacturers_query)
        manufacturers = manufacturers_result.scalars().all()
        retailer.manufacturers.extend(manufacturers)
    
    await db.commit()
    await db.refresh(retailer)
    
    # Load manufacturers for proper serialization
    retailer_query = select(Retailer).options(
        selectinload(Retailer.manufacturers)
    ).where(Retailer.id == retailer.id)
    retailer_result = await db.execute(retailer_query)
    retailer = retailer_result.scalar_one()
    
    return retailer

@router.put("/retailers/{retailer_id}", response_model=RetailerResponse)
async def update_retailer(
    retailer_id: int,
    retailer_data: RetailerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing retailer."""
    retailer_query = select(Retailer).where(Retailer.id == retailer_id)
    retailer_result = await db.execute(retailer_query)
    retailer = retailer_result.scalar_one_or_none()
    if not retailer:
        raise HTTPException(status_code=404, detail="Retailer not found")
    
    # Check if code conflicts with another retailer
    if retailer_data.code and retailer_data.code != retailer.code:
        existing_query = select(Retailer).where(
            Retailer.code == retailer_data.code,
            Retailer.id != retailer_id
        )
        existing_result = await db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Retailer code already exists")
    
    # Update fields
    update_data = retailer_data.model_dump(exclude_unset=True, exclude={"manufacturer_ids"})
    for field, value in update_data.items():
        setattr(retailer, field, value)
    
    # Update manufacturer relationships
    if retailer_data.manufacturer_ids is not None:
        manufacturers_query = select(Manufacturer).where(
            Manufacturer.id.in_(retailer_data.manufacturer_ids)
        )
        manufacturers_result = await db.execute(manufacturers_query)
        manufacturers = manufacturers_result.scalars().all()
        retailer.manufacturers.clear()
        retailer.manufacturers.extend(manufacturers)
    
    await db.commit()
    await db.refresh(retailer)
    
    # Load manufacturers for proper serialization
    retailer_query = select(Retailer).options(
        selectinload(Retailer.manufacturers)
    ).where(Retailer.id == retailer_id)
    retailer_result = await db.execute(retailer_query)
    retailer = retailer_result.scalar_one()
    
    return retailer

@router.delete("/retailers/{retailer_id}")
async def delete_retailer(
    retailer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a retailer (soft delete by setting is_active=False)."""
    retailer_query = select(Retailer).where(Retailer.id == retailer_id)
    retailer_result = await db.execute(retailer_query)
    retailer = retailer_result.scalar_one_or_none()
    if not retailer:
        raise HTTPException(status_code=404, detail="Retailer not found")
    
    retailer.is_active = False
    await db.commit()
    return {"message": "Retailer deleted successfully"}

# Manufacturer endpoints
@router.get("/manufacturers", response_model=ManufacturerListResponse)
async def get_manufacturers(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of manufacturers with optional search and filtering."""
    query = select(Manufacturer).options(selectinload(Manufacturer.retailers))
    
    if active_only:
        query = query.where(Manufacturer.is_active == True)
    
    if search:
        query = query.where(
            (Manufacturer.name.ilike(f"%{search}%")) |
            (Manufacturer.code.ilike(f"%{search}%")) |
            (Manufacturer.contact_email.ilike(f"%{search}%"))
        )
    
    # Get total count
    total_query = select(func.count(Manufacturer.id))
    if active_only:
        total_query = total_query.where(Manufacturer.is_active == True)
    if search:
        total_query = total_query.where(
            (Manufacturer.name.ilike(f"%{search}%")) |
            (Manufacturer.code.ilike(f"%{search}%")) |
            (Manufacturer.contact_email.ilike(f"%{search}%"))
        )
    
    total_result = await db.execute(total_query)
    total = total_result.scalar()
    
    # Get paginated results
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    manufacturers = result.scalars().all()
    
    return ManufacturerListResponse(
        manufacturers=manufacturers,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/manufacturers/dropdown")
async def get_manufacturers_dropdown(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get simplified list of manufacturers for dropdown menus."""
    query = select(Manufacturer).where(Manufacturer.is_active == True)
    result = await db.execute(query)
    manufacturers = result.scalars().all()
    return [{"id": m.id, "name": m.name, "code": m.code} for m in manufacturers]

@router.get("/manufacturers/{manufacturer_id}", response_model=ManufacturerResponse)
async def get_manufacturer(
    manufacturer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific manufacturer by ID."""
    query = select(Manufacturer).options(selectinload(Manufacturer.retailers)).where(Manufacturer.id == manufacturer_id)
    result = await db.execute(query)
    manufacturer = result.scalar_one_or_none()
    if not manufacturer:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    return manufacturer

@router.post("/manufacturers", response_model=ManufacturerResponse)
async def create_manufacturer(
    manufacturer_data: ManufacturerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new manufacturer."""
    # Check if code already exists
    existing_query = select(Manufacturer).where(Manufacturer.code == manufacturer_data.code)
    existing_result = await db.execute(existing_query)
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Manufacturer code already exists")
    
    # Create manufacturer
    manufacturer = Manufacturer(**manufacturer_data.model_dump(exclude={"retailer_ids"}))
    db.add(manufacturer)
    await db.flush()
    
    # Link retailers
    if manufacturer_data.retailer_ids:
        retailers_query = select(Retailer).where(
            Retailer.id.in_(manufacturer_data.retailer_ids)
        )
        retailers_result = await db.execute(retailers_query)
        retailers = retailers_result.scalars().all()
        manufacturer.retailers.extend(retailers)
    
    await db.commit()
    await db.refresh(manufacturer)
    
    # Load retailers for proper serialization
    manufacturer_query = select(Manufacturer).options(
        selectinload(Manufacturer.retailers)
    ).where(Manufacturer.id == manufacturer.id)
    manufacturer_result = await db.execute(manufacturer_query)
    manufacturer = manufacturer_result.scalar_one()
    
    return manufacturer

@router.put("/manufacturers/{manufacturer_id}", response_model=ManufacturerResponse)
async def update_manufacturer(
    manufacturer_id: int,
    manufacturer_data: ManufacturerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing manufacturer."""
    manufacturer_query = select(Manufacturer).where(Manufacturer.id == manufacturer_id)
    manufacturer_result = await db.execute(manufacturer_query)
    manufacturer = manufacturer_result.scalar_one_or_none()
    if not manufacturer:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    
    # Check if code conflicts with another manufacturer
    if manufacturer_data.code and manufacturer_data.code != manufacturer.code:
        existing_query = select(Manufacturer).where(
            Manufacturer.code == manufacturer_data.code,
            Manufacturer.id != manufacturer_id
        )
        existing_result = await db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Manufacturer code already exists")
    
    # Update fields
    update_data = manufacturer_data.model_dump(exclude_unset=True, exclude={"retailer_ids"})
    for field, value in update_data.items():
        setattr(manufacturer, field, value)
    
    # Update retailer relationships
    if manufacturer_data.retailer_ids is not None:
        retailers_query = select(Retailer).where(
            Retailer.id.in_(manufacturer_data.retailer_ids)
        )
        retailers_result = await db.execute(retailers_query)
        retailers = retailers_result.scalars().all()
        manufacturer.retailers.clear()
        manufacturer.retailers.extend(retailers)
    
    await db.commit()
    await db.refresh(manufacturer)
    
    # Load retailers for proper serialization
    manufacturer_query = select(Manufacturer).options(
        selectinload(Manufacturer.retailers)
    ).where(Manufacturer.id == manufacturer_id)
    manufacturer_result = await db.execute(manufacturer_query)
    manufacturer = manufacturer_result.scalar_one()
    
    return manufacturer

@router.delete("/manufacturers/{manufacturer_id}")
async def delete_manufacturer(
    manufacturer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a manufacturer (soft delete by setting is_active=False)."""
    manufacturer_query = select(Manufacturer).where(Manufacturer.id == manufacturer_id)
    manufacturer_result = await db.execute(manufacturer_query)
    manufacturer = manufacturer_result.scalar_one_or_none()
    if not manufacturer:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    
    manufacturer.is_active = False
    await db.commit()
    return {"message": "Manufacturer deleted successfully"}

# Route endpoints
@router.get("/routes", response_model=RouteListResponse)
async def get_routes(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    manufacturer_id: Optional[int] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of routes with optional search and filtering."""
    query = select(Route).options(
        selectinload(Route.manufacturer).selectinload(Manufacturer.retailers)
    )
    
    if active_only:
        query = query.where(Route.is_active == True)
    
    if manufacturer_id:
        query = query.where(Route.manufacturer_id == manufacturer_id)
    
    if search:
        query = query.where(
            (Route.name.ilike(f"%{search}%")) |
            (Route.origin_city.ilike(f"%{search}%")) |
            (Route.destination_city.ilike(f"%{search}%"))
        )
    
    # Get total count
    total_query = select(func.count(Route.id))
    if active_only:
        total_query = total_query.where(Route.is_active == True)
    if manufacturer_id:
        total_query = total_query.where(Route.manufacturer_id == manufacturer_id)
    if search:
        total_query = total_query.where(
            (Route.name.ilike(f"%{search}%")) |
            (Route.origin_city.ilike(f"%{search}%")) |
            (Route.destination_city.ilike(f"%{search}%"))
        )
    
    total_result = await db.execute(total_query)
    total = total_result.scalar()
    
    # Get paginated results
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    routes = result.scalars().all()
    
    return RouteListResponse(
        routes=routes,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/routes/{route_id}", response_model=RouteResponse)
async def get_route(
    route_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific route by ID."""
    query = select(Route).options(
        selectinload(Route.manufacturer).selectinload(Manufacturer.retailers)
    ).where(Route.id == route_id)
    result = await db.execute(query)
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route

@router.post("/routes", response_model=RouteResponse)
async def create_route(
    route_data: RouteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new route."""
    # Verify manufacturer exists
    manufacturer_query = select(Manufacturer).where(Manufacturer.id == route_data.manufacturer_id)
    manufacturer_result = await db.execute(manufacturer_query)
    manufacturer = manufacturer_result.scalar_one_or_none()
    if not manufacturer:
        raise HTTPException(status_code=400, detail="Manufacturer not found")
    
    route = Route(**route_data.model_dump())
    db.add(route)
    await db.commit()
    await db.refresh(route)
    
    # Load manufacturer with retailers for proper serialization
    route_query = select(Route).options(
        selectinload(Route.manufacturer).selectinload(Manufacturer.retailers)
    ).where(Route.id == route.id)
    route_result = await db.execute(route_query)
    route = route_result.scalar_one()
    
    return route

@router.put("/routes/{route_id}", response_model=RouteResponse)
async def update_route(
    route_id: int,
    route_data: RouteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing route."""
    route_query = select(Route).where(Route.id == route_id)
    route_result = await db.execute(route_query)
    route = route_result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Verify manufacturer exists if being updated
    if route_data.manufacturer_id:
        manufacturer_query = select(Manufacturer).where(Manufacturer.id == route_data.manufacturer_id)
        manufacturer_result = await db.execute(manufacturer_query)
        manufacturer = manufacturer_result.scalar_one_or_none()
        if not manufacturer:
            raise HTTPException(status_code=400, detail="Manufacturer not found")
    
    # Update fields
    update_data = route_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(route, field, value)
    
    await db.commit()
    await db.refresh(route)
    
    # Load manufacturer with retailers for proper serialization
    route_query = select(Route).options(
        selectinload(Route.manufacturer).selectinload(Manufacturer.retailers)
    ).where(Route.id == route_id)
    route_result = await db.execute(route_query)
    route = route_result.scalar_one()
    
    return route

@router.delete("/routes/{route_id}")
async def delete_route(
    route_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a route (soft delete by setting is_active=False)."""
    route_query = select(Route).where(Route.id == route_id)
    route_result = await db.execute(route_query)
    route = route_result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    route.is_active = False
    await db.commit()
    return {"message": "Route deleted successfully"}

# Utility endpoints for dropdown lists




@router.get("/routes/dropdown")
async def get_routes_dropdown(
    manufacturer_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get simplified list of routes for dropdown menus."""
    query = select(Route).where(Route.is_active == True)
    if manufacturer_id:
        query = query.where(Route.manufacturer_id == manufacturer_id)
    
    result = await db.execute(query)
    routes = result.scalars().all()
    return [{"id": r.id, "name": r.name, "origin": r.origin_city, "destination": r.destination_city} for r in routes]
