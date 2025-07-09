from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from decimal import Decimal

class ProductAttributes(BaseModel):
    weight_kg: Optional[float] = None
    volume_m3: Optional[float] = None
    temperature_requirement: Optional[str] = None
    fragile: bool = False
    additional_attributes: Optional[Dict[str, Any]] = None

class SKUItemCreate(BaseModel):
    sku_code: str = Field(..., max_length=100)
    product_name: str = Field(..., max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    quantity_ordered: int = Field(..., gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=50)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    total_price: Optional[Decimal] = Field(None, ge=0)
    weight_kg: Optional[Decimal] = Field(None, ge=0)
    volume_m3: Optional[Decimal] = Field(None, ge=0)
    temperature_requirement: Optional[str] = Field(None, max_length=50)
    fragile: bool = False
    product_attributes: Optional[Dict[str, Any]] = None
    processing_remarks: Optional[str] = None

class SKUItemResponse(BaseModel):
    id: str
    sku_code: str
    product_name: str
    category: Optional[str] = None
    brand: Optional[str] = None
    quantity_ordered: int
    unit_of_measure: Optional[str] = None
    unit_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    weight_kg: Optional[Decimal] = None
    volume_m3: Optional[Decimal] = None
    temperature_requirement: Optional[str] = None
    fragile: bool = False
    product_attributes: Optional[Dict[str, Any]] = None
    processing_remarks: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class RetailerInfo(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None

class DeliveryAddress(BaseModel):
    street: str
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str = "USA"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class OrderSummary(BaseModel):
    total_sku_count: int
    total_quantity: int
    total_weight_kg: Decimal
    total_volume_m3: Decimal
    subtotal: Decimal
    tax: Decimal
    total: Decimal

class OrderCreateRequest(BaseModel):
    priority: str = Field("NORMAL", pattern="^(LOW|NORMAL|HIGH|URGENT)$")
    special_instructions: Optional[str] = None
    requested_delivery_date: Optional[datetime] = None
    delivery_address: Optional[DeliveryAddress] = None
    retailer_info: Optional[RetailerInfo] = None

class OrderDetailedResponse(BaseModel):
    id: str
    order_number: str
    status: str
    original_filename: Optional[str] = None
    file_type: Optional[str] = None
    priority: str
    special_instructions: Optional[str] = None
    requested_delivery_date: Optional[datetime] = None
    delivery_address: Optional[Dict[str, Any]] = None
    retailer_info: Optional[Dict[str, Any]] = None
    
    # Order summary
    total_sku_count: Optional[int] = None
    total_quantity: Optional[int] = None
    total_weight_kg: Optional[Decimal] = None
    total_volume_m3: Optional[Decimal] = None
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    total: Optional[Decimal] = None
    # Trip information
    trip_id: Optional[str] = None
    trip_status: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None
    
    # SKU items
    sku_items: Optional[List[SKUItemResponse]] = []
    
    # Metadata
    missing_fields: Optional[List[str]] = None
    validation_errors: Optional[List[str]] = None
    processing_notes: Optional[str] = None
    
    created_at: datetime
    updated_at: Optional[datetime] = None

class TripInfo(BaseModel):
    trip_id: str
    trip_status: str
    estimated_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    driver_name: Optional[str] = None
    driver_contact: Optional[str] = None
    vehicle_info: Optional[Dict[str, Any]] = None
    route_info: Optional[Dict[str, Any]] = None

class OrderStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(UPLOADED|PROCESSING|PENDING_INFO|INFO_RECEIVED|VALIDATED|TRIP_QUEUED|TRIP_PLANNED|SUBMITTED|CONFIRMED|IN_TRANSIT|DELIVERED|REJECTED|CANCELLED)$")
    message: Optional[str] = None
    details: Optional[str] = None
    trip_id: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None

# Trip Optimization Models
class TripOptimizationRequest(BaseModel):
    """Request model for trip optimization"""
    order_ids: List[str] = Field(..., min_items=1)
    manufacturing_location_id: str
    planned_date: Optional[datetime] = None
    optimization_objectives: Optional[List[str]] = Field(default=["minimize_distance", "maximize_capacity"])
    constraints: Optional[Dict[str, Any]] = None

class TripOptimizationResponse(BaseModel):
    """Response model for trip optimization"""
    trip_id: str
    optimization_id: str
    total_distance_km: float
    estimated_duration_hours: float
    capacity_utilization: float
    optimization_score: float
    routes: List[Dict[str, Any]]
    constraints_satisfied: bool
    improvement_percentage: float
    created_at: datetime

class SKUConsolidationRequest(BaseModel):
    """Request model for SKU consolidation optimization"""
    retailer_id: str
    manufacturing_location_id: str
    start_date: datetime
    end_date: datetime
    consolidation_strategy: str = Field(default="optimize_capacity", pattern="^(optimize_capacity|minimize_trips|balance_efficiency)$")
    max_consolidation_groups: Optional[int] = Field(default=10, ge=1, le=50)

class SKUConsolidationResponse(BaseModel):
    """Response model for SKU consolidation"""
    consolidation_id: str
    manufacturer_id: str
    total_skus: int
    total_weight_kg: Decimal
    total_volume_m3: Decimal
    consolidation_groups: List[Dict[str, Any]]
    optimization_efficiency: float
    estimated_cost_savings: Decimal
    processing_time_seconds: float
    created_at: datetime

class RouteOptimizationRequest(BaseModel):
    """Request model for route optimization"""
    order_ids: List[str] = Field(..., min_items=1)
    manufacturing_location_id: str
    truck_id: Optional[str] = None
    planned_date: Optional[datetime] = None
    optimization_algorithm: str = Field(default="advanced_tsp", pattern="^(nearest_neighbor|advanced_tsp|genetic_algorithm)$")
    time_windows: Optional[List[Dict[str, Any]]] = None
    
class RouteOptimizationResponse(BaseModel):
    """Response model for route optimization"""
    route_id: str
    route_name: str
    truck_id: Optional[str] = None
    optimization_score: float
    total_distance_km: float
    estimated_duration_hours: float
    waypoints: List[Dict[str, Any]]
    delivery_sequence: List[Dict[str, Any]]
    constraints_satisfied: bool
    improvement_percentage: float
    optimization_algorithm: str
    created_at: datetime

class TripPlanningRequest(BaseModel):
    """Request model for comprehensive trip planning"""
    consolidation_request: SKUConsolidationRequest
    route_optimization_request: RouteOptimizationRequest
    integration_preferences: Optional[Dict[str, Any]] = None

class TripPlanningResponse(BaseModel):
    """Response model for comprehensive trip planning"""
    planning_id: str
    consolidation_result: SKUConsolidationResponse
    route_optimization_result: RouteOptimizationResponse
    integration_summary: Dict[str, Any]
    overall_efficiency_score: float
    recommendations: List[str]
    created_at: datetime

class TripAnalyticsRequest(BaseModel):
    """Request model for trip analytics"""
    date_range: Dict[str, datetime]
    manufacturing_location_ids: Optional[List[str]] = None
    analytics_type: str = Field(default="efficiency", pattern="^(efficiency|cost|performance|utilization)$")
    aggregation_level: str = Field(default="daily", pattern="^(hourly|daily|weekly|monthly)$")

class TripAnalyticsResponse(BaseModel):
    """Response model for trip analytics"""
    analytics_id: str
    period: str
    total_trips: int
    avg_capacity_utilization: float
    total_distance_km: float
    total_cost_savings: Decimal
    efficiency_metrics: Dict[str, Any]
    performance_trends: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: datetime

class ManufacturingLocationResponse(BaseModel):
    """Response model for manufacturing location"""
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    capacity_trucks: int
    operating_hours: Dict[str, Any]
    current_utilization: float
    available_trucks: int
    created_at: datetime

class TruckResponse(BaseModel):
    """Response model for truck information"""
    id: str
    truck_number: str
    max_weight_kg: float
    max_volume_m3: float
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    status: str
    driver_info: Optional[Dict[str, Any]] = None
    manufacturing_location_id: str
    current_route_id: Optional[str] = None
    availability_schedule: Optional[Dict[str, Any]] = None

class DeliveryTrackingResponse(BaseModel):
    """Response model for delivery tracking"""
    id: str
    order_id: str
    route_id: Optional[str] = None
    truck_id: Optional[str] = None
    status: str
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    estimated_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    distance_to_destination_km: Optional[float] = None
    tracking_updates: List[Dict[str, Any]]
    created_at: datetime

class OptimizationLogResponse(BaseModel):
    """Response model for optimization log"""
    id: str
    route_id: Optional[str] = None
    optimization_algorithm: str
    input_parameters: Dict[str, Any]
    optimization_results: Dict[str, Any]
    execution_time_seconds: float
    improvement_percentage: float
    status: str
    error_message: Optional[str] = None
    created_at: datetime
