from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

# Base schemas
class RetailerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    is_active: bool = True
    notes: Optional[str] = None

class RetailerCreate(RetailerBase):
    manufacturer_ids: Optional[List[int]] = []

class RetailerUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    manufacturer_ids: Optional[List[int]] = None

class RetailerResponse(RetailerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    manufacturers: List['ManufacturerResponse'] = []

    class Config:
        from_attributes = True

# Manufacturer schemas
class ManufacturerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    is_active: bool = True
    notes: Optional[str] = None
    lead_time_days: int = 7
    min_order_value: int = 0
    preferred_payment_terms: Optional[str] = None

class ManufacturerCreate(ManufacturerBase):
    retailer_ids: Optional[List[int]] = []

class ManufacturerUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    lead_time_days: Optional[int] = None
    min_order_value: Optional[int] = None
    preferred_payment_terms: Optional[str] = None
    retailer_ids: Optional[List[int]] = None

class ManufacturerResponse(ManufacturerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    retailers: List['RetailerResponse'] = []

    class Config:
        from_attributes = True

# Route schemas
class RouteBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    manufacturer_id: int
    origin_city: str = Field(..., min_length=1, max_length=100)
    origin_state: Optional[str] = None
    origin_country: Optional[str] = None
    destination_city: str = Field(..., min_length=1, max_length=100)
    destination_state: Optional[str] = None
    destination_country: Optional[str] = None
    distance_km: Optional[int] = None
    estimated_transit_days: int = 3
    transport_mode: str = 'truck'
    cost_per_km: int = 0
    max_weight_kg: Optional[int] = None
    max_volume_m3: Optional[int] = None
    is_active: bool = True
    notes: Optional[str] = None

class RouteCreate(RouteBase):
    pass

class RouteUpdate(BaseModel):
    name: Optional[str] = None
    manufacturer_id: Optional[int] = None
    origin_city: Optional[str] = None
    origin_state: Optional[str] = None
    origin_country: Optional[str] = None
    destination_city: Optional[str] = None
    destination_state: Optional[str] = None
    destination_country: Optional[str] = None
    distance_km: Optional[int] = None
    estimated_transit_days: Optional[int] = None
    transport_mode: Optional[str] = None
    cost_per_km: Optional[int] = None
    max_weight_kg: Optional[int] = None
    max_volume_m3: Optional[int] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

class RouteResponse(RouteBase):
    id: int
    created_at: datetime
    updated_at: datetime
    manufacturer: ManufacturerResponse

    class Config:
        from_attributes = True

# List response schemas
class RetailerListResponse(BaseModel):
    retailers: List[RetailerResponse]
    total: int
    page: int
    per_page: int

class ManufacturerListResponse(BaseModel):
    manufacturers: List[ManufacturerResponse]
    total: int
    page: int
    per_page: int

class RouteListResponse(BaseModel):
    routes: List[RouteResponse]
    total: int
    page: int
    per_page: int

# Update forward references
RetailerResponse.model_rebuild()
ManufacturerResponse.model_rebuild()
