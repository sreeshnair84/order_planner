from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from app.database.connection import get_db
from app.models.user import User
from app.models.order import Order
from app.models.sku_item import OrderSKUItem
from app.models.trip_planning import (
    ManufacturingLocation, 
    Truck, 
    DeliveryRoute, 
    RouteOrder, 
    ConsolidationGroup,
    TripOptimizationLog
)
from app.models.schemas import (
    TripOptimizationRequest,
    TripOptimizationResponse,
    SKUConsolidationRequest,
    SKUConsolidationResponse,
    RouteOptimizationRequest,
    RouteOptimizationResponse,
    TripInfo,
    SKUItemResponse
)
from app.api.auth import get_current_user
from app.services.trip_route_optimizer import TripRouteOptimizer, SKUDeliveryInfo, DeliveryLocation
from app.services.sku_consolidation_engine import SKUConsolidationEngine, ConsolidatedSKU, TripSKUGroup
from app.services.sku_service import SKUService

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models for API
class TripPlanningResponse(BaseModel):
    trip_id: str
    manufacturing_location_id: str
    route_stops: List[Dict[str, Any]]
    sku_items: List[Dict[str, Any]]
    total_distance_km: float
    estimated_duration_hours: float
    total_weight_kg: Decimal
    total_volume_m3: Decimal
    capacity_utilization: float
    optimization_score: float
    validation_results: Dict[str, Any]

class SKUConsolidationResponse(BaseModel):
    consolidation_id: str
    manufacturer_id: str
    total_skus: int
    total_weight_kg: Decimal
    total_volume_m3: Decimal
    trip_groups: List[Dict[str, Any]]
    optimization_efficiency: float
    estimated_cost_savings: Decimal
    created_at: datetime

class RouteOptimizationResponse(BaseModel):
    route_id: str
    route_name: str
    truck_id: str
    optimization_score: float
    total_distance_km: float
    estimated_duration_hours: float
    waypoints: List[Dict[str, Any]]
    delivery_sequence: List[Dict[str, Any]]
    constraints_satisfied: bool
    improvement_percentage: float

class TripAnalyticsResponse(BaseModel):
    period: str
    total_trips: int
    avg_capacity_utilization: float
    total_distance_km: float
    total_cost_savings: Decimal
    efficiency_metrics: Dict[str, Any]

class DeliveryRouteResponse(BaseModel):
    id: str
    route_name: str
    manufacturing_location_id: str
    truck_id: Optional[str] = None
    planned_date: Optional[date] = None
    status: str
    total_distance_km: Optional[float] = None
    estimated_duration_hours: Optional[float] = None
    capacity_utilization: Optional[float] = None
    route_waypoints: Optional[Dict[str, Any]] = None
    sku_count: int
    total_weight_kg: Optional[float] = None
    total_volume_m3: Optional[float] = None
    optimization_score: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Related data
    route_orders: List[Dict[str, Any]] = []
    manufacturing_location: Optional[Dict[str, Any]] = None
    truck: Optional[Dict[str, Any]] = None

class DeliveryRouteListResponse(BaseModel):
    routes: List[DeliveryRouteResponse]
    total: int
    page: int
    per_page: int

# Trip Route Optimization Endpoints
@router.post("/optimize-routes", response_model=RouteOptimizationResponse)
async def optimize_trip_routes(
    request: RouteOptimizationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Optimize delivery routes for multiple orders using advanced algorithms.
    
    This endpoint uses the Trip Route Optimizer to create optimal delivery routes
    considering distance, capacity, time windows, and SKU consolidation.
    """
    try:
        # Get manufacturing location
        manufacturing_location = await db.execute(
            select(ManufacturingLocation).where(
                ManufacturingLocation.id == request.manufacturing_location_id
            )
        )
        manufacturing_location = manufacturing_location.scalar_one_or_none()
        
        if not manufacturing_location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manufacturing location not found"
            )
        
        # Get orders and their SKU items
        orders_query = select(Order).where(
            Order.id.in_(request.order_ids),
            Order.status.in_(['CONFIRMED', 'PROCESSING'])
        )
        orders_result = await db.execute(orders_query)
        orders = orders_result.scalars().all()
        
        if not orders:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid orders found for optimization"
            )
        
        # Collect all SKU items for optimization
        trip_skus = []
        for order in orders:
            # Get SKU items for this order
            sku_items_query = select(OrderSKUItem).where(
                OrderSKUItem.order_id == order.id
            )
            sku_items_result = await db.execute(sku_items_query)
            sku_items = sku_items_result.scalars().all()
            
            for sku_item in sku_items:
                # Convert to SKUDeliveryInfo
                delivery_location = DeliveryLocation(
                    id=str(order.id),
                    name=order.delivery_address or "Unknown Address",
                    address=order.delivery_address or "",
                    latitude=float(order.delivery_latitude or 0.0),
                    longitude=float(order.delivery_longitude or 0.0),
                    retailer_id=order.retailer_id or "",
                    delivery_window_start=order.delivery_date,
                    delivery_window_end=order.delivery_date
                )
                
                trip_sku = SKUDeliveryInfo(
                    sku_code=sku_item.sku_code,
                    product_name=sku_item.product_name,
                    category=sku_item.category,
                    brand=sku_item.brand,
                    quantity=sku_item.quantity,
                    weight_kg=sku_item.weight_kg or Decimal('0'),
                    volume_m3=sku_item.volume_m3 or Decimal('0'),
                    temperature_requirement=sku_item.temperature_requirement,
                    fragile=sku_item.fragile or False,
                    delivery_locations=[delivery_location],
                    order_id=str(order.id)
                )
                trip_skus.append(trip_sku)
        
        # Initialize trip optimizer
        optimizer = TripRouteOptimizer()
        
        # Create manufacturing location dict
        manufacturing_location_dict = {
            'id': str(manufacturing_location.id),
            'name': manufacturing_location.name,
            'address': manufacturing_location.address,
            'latitude': float(manufacturing_location.latitude),
            'longitude': float(manufacturing_location.longitude)
        }
        
        # Optimize trip route
        optimized_trip = await optimizer.optimize_trip_route(
            trip_skus, 
            manufacturing_location_dict
        )
        
        # Validate trip constraints
        validation_results = await optimizer.validate_trip_constraints(optimized_trip)
        
        # Create delivery route record
        delivery_route = DeliveryRoute(
            route_name=f"Route-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            manufacturing_location_id=manufacturing_location.id,
            planned_date=request.planned_date or date.today(),
            status='PLANNED',
            total_distance_km=optimized_trip.total_distance_km,
            estimated_duration_hours=optimized_trip.estimated_duration_hours,
            capacity_utilization=optimized_trip.capacity_utilization,
            route_waypoints=[
                {
                    'id': stop.id,
                    'name': stop.name,
                    'latitude': stop.latitude,
                    'longitude': stop.longitude,
                    'address': stop.address
                }
                for stop in optimized_trip.route_stops
            ],
            sku_count=len(optimized_trip.sku_items),
            total_weight_kg=optimized_trip.total_weight_kg,
            total_volume_m3=optimized_trip.total_volume_m3,
            optimization_score=validation_results.get('optimization_score', 0.0)
        )
        
        db.add(delivery_route)
        await db.commit()
        await db.refresh(delivery_route)
        
        # Create route orders
        for i, order in enumerate(orders):
            route_order = RouteOrder(
                route_id=delivery_route.id,
                order_id=order.id,
                sequence_number=i + 1,
                delivery_status='SCHEDULED',
                sku_items_count=len([sku for sku in trip_skus if sku.order_id == str(order.id)]),
                delivery_weight_kg=sum(sku.weight_kg * sku.quantity for sku in trip_skus if sku.order_id == str(order.id)),
                delivery_volume_m3=sum(sku.volume_m3 * sku.quantity for sku in trip_skus if sku.order_id == str(order.id))
            )
            db.add(route_order)
        
        # Log optimization
        optimization_log = TripOptimizationLog(
            route_id=delivery_route.id,
            optimization_algorithm='TripRouteOptimizer',
            input_parameters={
                'order_count': len(orders),
                'sku_count': len(trip_skus),
                'manufacturing_location_id': str(manufacturing_location.id)
            },
            optimization_results={
                'total_distance_km': optimized_trip.total_distance_km,
                'estimated_duration_hours': optimized_trip.estimated_duration_hours,
                'capacity_utilization': optimized_trip.capacity_utilization,
                'validation_results': validation_results
            },
            status='SUCCESS',
            improvement_percentage=validation_results.get('improvement_percentage', 0.0)
        )
        db.add(optimization_log)
        
        await db.commit()
        
        return RouteOptimizationResponse(
            route_id=str(delivery_route.id),
            route_name=delivery_route.route_name,
            truck_id=str(delivery_route.truck_id) if delivery_route.truck_id else "",
            optimization_score=delivery_route.optimization_score or 0.0,
            total_distance_km=delivery_route.total_distance_km,
            estimated_duration_hours=delivery_route.estimated_duration_hours,
            waypoints=delivery_route.route_waypoints,
            delivery_sequence=[
                {
                    'order_id': str(order.id),
                    'sequence': i + 1,
                    'address': order.delivery_address,
                    'estimated_arrival': None  # Will be calculated later
                }
                for i, order in enumerate(orders)
            ],
            constraints_satisfied=validation_results.get('is_valid', False),
            improvement_percentage=validation_results.get('improvement_percentage', 0.0)
        )
        
    except Exception as e:
        logger.error(f"Error optimizing trip routes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize trip routes"
        )

@router.post("/optimize-skus", response_model=SKUConsolidationResponse)
async def optimize_sku_consolidation(
    request: SKUConsolidationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Optimize SKU consolidation across multiple orders for efficient trip planning.
    
    This endpoint analyzes multiple orders and creates consolidated SKU groups
    optimized for manufacturing locations and delivery efficiency.
    """
    try:
        # Initialize SKU consolidation engine
        consolidation_engine = SKUConsolidationEngine(db)
        
        # Get orders for consolidation
        orders_query = select(Order).where(
            Order.retailer_id == request.retailer_id,
            Order.status.in_(['CONFIRMED', 'PROCESSING']),
            Order.delivery_date >= request.start_date,
            Order.delivery_date <= request.end_date
        )
        orders_result = await db.execute(orders_query)
        orders = orders_result.scalars().all()
        
        if not orders:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No orders found for consolidation"
            )
        
        # Perform SKU consolidation
        consolidated_skus = await consolidation_engine.consolidate_skus_by_manufacturer(
            [str(order.id) for order in orders],
            request.manufacturing_location_id
        )
        
        # Create trip groups
        trip_groups = await consolidation_engine.create_trip_groups(
            consolidated_skus,
            request.manufacturing_location_id
        )
        
        # Calculate optimization metrics
        total_skus = sum(len(group.skus) for group in trip_groups)
        total_weight = sum(group.total_weight_kg for group in trip_groups)
        total_volume = sum(group.total_volume_m3 for group in trip_groups)
        
        # Create consolidation group record
        consolidation_group = ConsolidationGroup(
            group_name=f"Consolidation-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            manufacturer_id=request.manufacturing_location_id,
            total_orders=len(orders),
            total_skus=total_skus,
            total_weight_kg=total_weight,
            total_volume_m3=total_volume,
            consolidation_efficiency=sum(group.delivery_efficiency for group in trip_groups) / len(trip_groups),
            status='ACTIVE',
            optimization_parameters={
                'retailer_id': request.retailer_id,
                'date_range': f"{request.start_date} to {request.end_date}",
                'manufacturing_location_id': request.manufacturing_location_id
            }
        )
        
        db.add(consolidation_group)
        await db.commit()
        await db.refresh(consolidation_group)
        
        # Add orders to consolidation group
        for order in orders:
            # Note: You would typically have a ConsolidationOrder model to link orders to groups
            # This is simplified for the example
            pass
        
        return SKUConsolidationResponse(
            consolidation_id=str(consolidation_group.id),
            manufacturer_id=request.manufacturing_location_id,
            total_skus=total_skus,
            total_weight_kg=total_weight,
            total_volume_m3=total_volume,
            trip_groups=[
                {
                    'group_id': group.group_id,
                    'sku_count': group.total_sku_count,
                    'total_weight_kg': float(group.total_weight_kg),
                    'total_volume_m3': float(group.total_volume_m3),
                    'delivery_efficiency': group.delivery_efficiency,
                    'geographic_center': group.geographic_center
                }
                for group in trip_groups
            ],
            optimization_efficiency=consolidation_group.consolidation_efficiency,
            estimated_cost_savings=Decimal('0.00'),  # Will be calculated based on business logic
            created_at=consolidation_group.created_at
        )
        
    except Exception as e:
        logger.error(f"Error optimizing SKU consolidation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize SKU consolidation"
        )

@router.get("/routes/{route_id}", response_model=RouteOptimizationResponse)
async def get_route_details(
    route_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific delivery route."""
    try:
        route = await db.execute(
            select(DeliveryRoute).where(DeliveryRoute.id == route_id)
        )
        route = route.scalar_one_or_none()
        
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )
        
        # Get route orders
        route_orders = await db.execute(
            select(RouteOrder).where(RouteOrder.route_id == route_id)
        )
        route_orders = route_orders.scalars().all()
        
        return RouteOptimizationResponse(
            route_id=str(route.id),
            route_name=route.route_name,
            truck_id=str(route.truck_id) if route.truck_id else "",
            optimization_score=route.optimization_score or 0.0,
            total_distance_km=route.total_distance_km,
            estimated_duration_hours=route.estimated_duration_hours,
            waypoints=route.route_waypoints or [],
            delivery_sequence=[
                {
                    'order_id': str(ro.order_id),
                    'sequence': ro.sequence_number,
                    'delivery_status': ro.delivery_status,
                    'estimated_arrival': ro.estimated_arrival_time.isoformat() if ro.estimated_arrival_time else None
                }
                for ro in route_orders
            ],
            constraints_satisfied=True,  # Will be calculated based on validation
            improvement_percentage=0.0  # Will be calculated from optimization log
        )
        
    except Exception as e:
        logger.error(f"Error getting route details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve route details"
        )

@router.get("/analytics", response_model=TripAnalyticsResponse)
async def get_trip_analytics(
    period: str = "weekly",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get trip optimization analytics and performance metrics."""
    try:
        # Set default date range if not provided
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        # Get trip statistics
        trips_query = select(
            func.count(DeliveryRoute.id).label('total_trips'),
            func.avg(DeliveryRoute.capacity_utilization).label('avg_capacity_utilization'),
            func.sum(DeliveryRoute.total_distance_km).label('total_distance_km'),
            func.avg(DeliveryRoute.optimization_score).label('avg_optimization_score')
        ).where(
            DeliveryRoute.planned_date >= start_date,
            DeliveryRoute.planned_date <= end_date
        )
        
        stats_result = await db.execute(trips_query)
        stats = stats_result.one()
        
        # Get optimization logs for efficiency metrics
        optimization_logs = await db.execute(
            select(TripOptimizationLog).where(
                TripOptimizationLog.created_at >= start_date,
                TripOptimizationLog.created_at <= end_date,
                TripOptimizationLog.status == 'SUCCESS'
            )
        )
        optimization_logs = optimization_logs.scalars().all()
        
        # Calculate efficiency metrics
        efficiency_metrics = {
            'avg_improvement_percentage': sum(log.improvement_percentage or 0 for log in optimization_logs) / len(optimization_logs) if optimization_logs else 0,
            'total_optimizations': len(optimization_logs),
            'avg_execution_time': sum(log.execution_time_seconds or 0 for log in optimization_logs) / len(optimization_logs) if optimization_logs else 0,
            'success_rate': 100.0 if optimization_logs else 0.0
        }
        
        return TripAnalyticsResponse(
            period=period,
            total_trips=stats.total_trips or 0,
            avg_capacity_utilization=float(stats.avg_capacity_utilization or 0),
            total_distance_km=float(stats.total_distance_km or 0),
            total_cost_savings=Decimal('0.00'),  # Will be calculated based on business metrics
            efficiency_metrics=efficiency_metrics
        )
        
    except Exception as e:
        logger.error(f"Error getting trip analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trip analytics"
        )

@router.get("/manufacturing-locations", response_model=List[Dict[str, Any]])
async def get_manufacturing_locations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all available manufacturing locations."""
    try:
        locations = await db.execute(select(ManufacturingLocation))
        locations = locations.scalars().all()
        
        return [
            {
                'id': str(location.id),
                'name': location.name,
                'address': location.address,
                'latitude': float(location.latitude),
                'longitude': float(location.longitude),
                'capacity_trucks': location.capacity_trucks,
                'operating_hours': location.operating_hours
            }
            for location in locations
        ]
        
    except Exception as e:
        logger.error(f"Error getting manufacturing locations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve manufacturing locations"
        )

@router.get("/trucks", response_model=List[Dict[str, Any]])
async def get_available_trucks(
    manufacturing_location_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available trucks for trip assignment."""
    try:
        trucks_query = select(Truck).where(Truck.status == 'AVAILABLE')
        
        if manufacturing_location_id:
            trucks_query = trucks_query.where(
                Truck.manufacturer_location_id == manufacturing_location_id
            )
        
        trucks = await db.execute(trucks_query)
        trucks = trucks.scalars().all()
        
        return [
            {
                'id': str(truck.id),
                'truck_number': truck.truck_number,
                'max_weight_kg': float(truck.max_weight_kg),
                'max_volume_m3': float(truck.max_volume_m3),
                'current_latitude': float(truck.current_latitude) if truck.current_latitude else None,
                'current_longitude': float(truck.current_longitude) if truck.current_longitude else None,
                'status': truck.status,
                'driver_info': truck.driver_info
            }
            for truck in trucks
        ]
        
    except Exception as e:
        logger.error(f"Error getting available trucks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available trucks"
        )

@router.post("/routes/{route_id}/assign-truck")
async def assign_truck_to_route(
    route_id: str,
    truck_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Assign a truck to a delivery route."""
    try:
        # Get route
        route = await db.execute(
            select(DeliveryRoute).where(DeliveryRoute.id == route_id)
        )
        route = route.scalar_one_or_none()
        
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )
        
        # Get truck
        truck = await db.execute(
            select(Truck).where(Truck.id == truck_id, Truck.status == 'AVAILABLE')
        )
        truck = truck.scalar_one_or_none()
        
        if not truck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Truck not found or not available"
            )
        
        # Assign truck to route
        route.truck_id = truck.id
        truck.status = 'ASSIGNED'
        
        await db.commit()
        
        return {"message": "Truck assigned to route successfully"}
        
    except Exception as e:
        logger.error(f"Error assigning truck to route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign truck to route"
        )

@router.put("/routes/{route_id}/reorder")
async def reorder_route_deliveries(
    route_id: str,
    new_sequence: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reorder delivery sequence for a route."""
    try:
        # Get the route
        route_query = select(DeliveryRoute).where(DeliveryRoute.id == route_id)
        route_result = await db.execute(route_query)
        route = route_result.scalar_one_or_none()
        
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )
        
        # Update route order sequence
        for item in new_sequence:
            await db.execute(
                update(RouteOrder)
                .where(
                    RouteOrder.route_id == route_id,
                    RouteOrder.order_id == item['order_id']
                )
                .values(sequence_number=item['sequence'])
            )
        
        await db.commit()
        
        return {"message": "Route reordered successfully"}
        
    except Exception as e:
        logger.error(f"Error reordering route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reorder route"
        )

@router.post("/routes/{route_id}/optimize-realtime")
async def optimize_route_realtime(
    route_id: str,
    conditions: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Optimize route based on real-time conditions."""
    try:
        # Get route and current orders
        route_query = select(DeliveryRoute).where(DeliveryRoute.id == route_id)
        route_result = await db.execute(route_query)
        route = route_result.scalar_one_or_none()
        
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )
        
        # Get route orders
        orders_query = select(RouteOrder).where(RouteOrder.route_id == route_id)
        orders_result = await db.execute(orders_query)
        route_orders = orders_result.scalars().all()
        
        # Update estimated times based on conditions
        for route_order in route_orders:
            if conditions.get('traffic_conditions', {}).get('heavy'):
                # Add delay for heavy traffic
                current_time = route_order.estimated_arrival_time or datetime.now()
                route_order.estimated_arrival_time = current_time + timedelta(minutes=30)
            
            if str(route_order.order_id) in conditions.get('delivery_delays', {}):
                delay_info = conditions['delivery_delays'][str(route_order.order_id)]
                current_time = route_order.estimated_arrival_time or datetime.now()
                route_order.estimated_arrival_time = current_time + timedelta(minutes=delay_info['estimatedDelay'])
        
        await db.commit()
        
        return {"message": "Route optimized for real-time conditions"}
        
    except Exception as e:
        logger.error(f"Error optimizing route for real-time conditions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize route"
        )

@router.post("/resolve-time-conflict")
async def resolve_time_window_conflict(
    conflict_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resolve time window conflicts automatically."""
    try:
        affected_orders = conflict_data.get('affected_orders', [])
        
        # Simple resolution: extend time windows
        updated_windows = []
        for order_id in affected_orders:
            # Extend the time window by 1 hour
            updated_windows.append({
                'order_id': order_id,
                'start': '08:00',  # Earlier start
                'end': '19:00'     # Later end
            })
        
        return {
            'resolution_type': 'time_window_extension',
            'updated_windows': updated_windows,
            'message': 'Time windows extended to resolve conflicts'
        }
        
    except Exception as e:
        logger.error(f"Error resolving time conflict: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve time conflict"
        )
