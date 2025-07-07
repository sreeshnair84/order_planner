from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of retailers with optional search and filtering."""
    query = db.query(Retailer)
    
    if active_only:
        query = query.filter(Retailer.is_active == True)
    
    if search:
        query = query.filter(
            (Retailer.name.ilike(f"%{search}%")) |
            (Retailer.code.ilike(f"%{search}%")) |
            (Retailer.contact_email.ilike(f"%{search}%"))
        )
    
    total = query.count()
    retailers = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return RetailerListResponse(
        retailers=retailers,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/retailers/{retailer_id}", response_model=RetailerResponse)
async def get_retailer(
    retailer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific retailer by ID."""
    retailer = db.query(Retailer).filter(Retailer.id == retailer_id).first()
    if not retailer:
        raise HTTPException(status_code=404, detail="Retailer not found")
    return retailer

@router.post("/retailers", response_model=RetailerResponse)
async def create_retailer(
    retailer_data: RetailerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new retailer."""
    # Check if code already exists
    existing = db.query(Retailer).filter(Retailer.code == retailer_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Retailer code already exists")
    
    # Create retailer
    retailer = Retailer(**retailer_data.model_dump(exclude={"manufacturer_ids"}))
    db.add(retailer)
    db.flush()
    
    # Link manufacturers
    if retailer_data.manufacturer_ids:
        manufacturers = db.query(Manufacturer).filter(
            Manufacturer.id.in_(retailer_data.manufacturer_ids)
        ).all()
        retailer.manufacturers.extend(manufacturers)
    
    db.commit()
    db.refresh(retailer)
    return retailer

@router.put("/retailers/{retailer_id}", response_model=RetailerResponse)
async def update_retailer(
    retailer_id: int,
    retailer_data: RetailerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing retailer."""
    retailer = db.query(Retailer).filter(Retailer.id == retailer_id).first()
    if not retailer:
        raise HTTPException(status_code=404, detail="Retailer not found")
    
    # Check if code conflicts with another retailer
    if retailer_data.code and retailer_data.code != retailer.code:
        existing = db.query(Retailer).filter(
            Retailer.code == retailer_data.code,
            Retailer.id != retailer_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Retailer code already exists")
    
    # Update fields
    update_data = retailer_data.model_dump(exclude_unset=True, exclude={"manufacturer_ids"})
    for field, value in update_data.items():
        setattr(retailer, field, value)
    
    # Update manufacturer relationships
    if retailer_data.manufacturer_ids is not None:
        manufacturers = db.query(Manufacturer).filter(
            Manufacturer.id.in_(retailer_data.manufacturer_ids)
        ).all()
        retailer.manufacturers.clear()
        retailer.manufacturers.extend(manufacturers)
    
    db.commit()
    db.refresh(retailer)
    return retailer

@router.delete("/retailers/{retailer_id}")
async def delete_retailer(
    retailer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a retailer (soft delete by setting is_active=False)."""
    retailer = db.query(Retailer).filter(Retailer.id == retailer_id).first()
    if not retailer:
        raise HTTPException(status_code=404, detail="Retailer not found")
    
    retailer.is_active = False
    db.commit()
    return {"message": "Retailer deleted successfully"}

# Manufacturer endpoints
@router.get("/manufacturers", response_model=ManufacturerListResponse)
async def get_manufacturers(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of manufacturers with optional search and filtering."""
    query = db.query(Manufacturer)
    
    if active_only:
        query = query.filter(Manufacturer.is_active == True)
    
    if search:
        query = query.filter(
            (Manufacturer.name.ilike(f"%{search}%")) |
            (Manufacturer.code.ilike(f"%{search}%")) |
            (Manufacturer.contact_email.ilike(f"%{search}%"))
        )
    
    total = query.count()
    manufacturers = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return ManufacturerListResponse(
        manufacturers=manufacturers,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/manufacturers/{manufacturer_id}", response_model=ManufacturerResponse)
async def get_manufacturer(
    manufacturer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific manufacturer by ID."""
    manufacturer = db.query(Manufacturer).filter(Manufacturer.id == manufacturer_id).first()
    if not manufacturer:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    return manufacturer

@router.post("/manufacturers", response_model=ManufacturerResponse)
async def create_manufacturer(
    manufacturer_data: ManufacturerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new manufacturer."""
    # Check if code already exists
    existing = db.query(Manufacturer).filter(Manufacturer.code == manufacturer_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Manufacturer code already exists")
    
    # Create manufacturer
    manufacturer = Manufacturer(**manufacturer_data.model_dump(exclude={"retailer_ids"}))
    db.add(manufacturer)
    db.flush()
    
    # Link retailers
    if manufacturer_data.retailer_ids:
        retailers = db.query(Retailer).filter(
            Retailer.id.in_(manufacturer_data.retailer_ids)
        ).all()
        manufacturer.retailers.extend(retailers)
    
    db.commit()
    db.refresh(manufacturer)
    return manufacturer

@router.put("/manufacturers/{manufacturer_id}", response_model=ManufacturerResponse)
async def update_manufacturer(
    manufacturer_id: int,
    manufacturer_data: ManufacturerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing manufacturer."""
    manufacturer = db.query(Manufacturer).filter(Manufacturer.id == manufacturer_id).first()
    if not manufacturer:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    
    # Check if code conflicts with another manufacturer
    if manufacturer_data.code and manufacturer_data.code != manufacturer.code:
        existing = db.query(Manufacturer).filter(
            Manufacturer.code == manufacturer_data.code,
            Manufacturer.id != manufacturer_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Manufacturer code already exists")
    
    # Update fields
    update_data = manufacturer_data.model_dump(exclude_unset=True, exclude={"retailer_ids"})
    for field, value in update_data.items():
        setattr(manufacturer, field, value)
    
    # Update retailer relationships
    if manufacturer_data.retailer_ids is not None:
        retailers = db.query(Retailer).filter(
            Retailer.id.in_(manufacturer_data.retailer_ids)
        ).all()
        manufacturer.retailers.clear()
        manufacturer.retailers.extend(retailers)
    
    db.commit()
    db.refresh(manufacturer)
    return manufacturer

@router.delete("/manufacturers/{manufacturer_id}")
async def delete_manufacturer(
    manufacturer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a manufacturer (soft delete by setting is_active=False)."""
    manufacturer = db.query(Manufacturer).filter(Manufacturer.id == manufacturer_id).first()
    if not manufacturer:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    
    manufacturer.is_active = False
    db.commit()
    return {"message": "Manufacturer deleted successfully"}

# Route endpoints
@router.get("/routes", response_model=RouteListResponse)
async def get_routes(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    manufacturer_id: Optional[int] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of routes with optional search and filtering."""
    query = db.query(Route)
    
    if active_only:
        query = query.filter(Route.is_active == True)
    
    if manufacturer_id:
        query = query.filter(Route.manufacturer_id == manufacturer_id)
    
    if search:
        query = query.filter(
            (Route.name.ilike(f"%{search}%")) |
            (Route.origin_city.ilike(f"%{search}%")) |
            (Route.destination_city.ilike(f"%{search}%"))
        )
    
    total = query.count()
    routes = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return RouteListResponse(
        routes=routes,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/routes/{route_id}", response_model=RouteResponse)
async def get_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific route by ID."""
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route

@router.post("/routes", response_model=RouteResponse)
async def create_route(
    route_data: RouteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new route."""
    # Verify manufacturer exists
    manufacturer = db.query(Manufacturer).filter(Manufacturer.id == route_data.manufacturer_id).first()
    if not manufacturer:
        raise HTTPException(status_code=400, detail="Manufacturer not found")
    
    route = Route(**route_data.model_dump())
    db.add(route)
    db.commit()
    db.refresh(route)
    return route

@router.put("/routes/{route_id}", response_model=RouteResponse)
async def update_route(
    route_id: int,
    route_data: RouteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing route."""
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Verify manufacturer exists if being updated
    if route_data.manufacturer_id:
        manufacturer = db.query(Manufacturer).filter(Manufacturer.id == route_data.manufacturer_id).first()
        if not manufacturer:
            raise HTTPException(status_code=400, detail="Manufacturer not found")
    
    # Update fields
    update_data = route_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(route, field, value)
    
    db.commit()
    db.refresh(route)
    return route

@router.delete("/routes/{route_id}")
async def delete_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a route (soft delete by setting is_active=False)."""
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    route.is_active = False
    db.commit()
    return {"message": "Route deleted successfully"}

# Utility endpoints for dropdown lists
@router.get("/retailers/dropdown")
async def get_retailers_dropdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get simplified list of retailers for dropdown menus."""
    retailers = db.query(Retailer).filter(Retailer.is_active == True).all()
    return [{"id": r.id, "name": r.name, "code": r.code} for r in retailers]

@router.get("/manufacturers/dropdown")
async def get_manufacturers_dropdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get simplified list of manufacturers for dropdown menus."""
    manufacturers = db.query(Manufacturer).filter(Manufacturer.is_active == True).all()
    return [{"id": m.id, "name": m.name, "code": m.code} for m in manufacturers]

@router.get("/routes/dropdown")
async def get_routes_dropdown(
    manufacturer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get simplified list of routes for dropdown menus."""
    query = db.query(Route).filter(Route.is_active == True)
    if manufacturer_id:
        query = query.filter(Route.manufacturer_id == manufacturer_id)
    
    routes = query.all()
    return [{"id": r.id, "name": r.name, "origin": r.origin_city, "destination": r.destination_city} for r in routes]
