from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
import asyncio
from dataclasses import asdict

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
    ConsolidationOrder,
    DeliveryTracking,
    TripOptimizationLog
)
from app.models.schemas import (
    TripAnalyticsRequest,
    TripAnalyticsResponse,
    ManufacturingLocationResponse,
    TruckResponse,
    DeliveryTrackingResponse,
    OptimizationLogResponse
)
from app.api.auth import get_current_user
from app.services.trip_route_optimizer import TripRouteOptimizer, SKUDeliveryInfo, DeliveryLocation
from app.services.sku_consolidation_engine import SKUConsolidationEngine

router = APIRouter()
logger = logging.getLogger(__name__)

# Advanced Logistics Endpoints
class LogisticsOptimizationRequest(BaseModel):
    """Request for comprehensive logistics optimization"""
    manufacturing_location_ids: List[str]
    date_range: Dict[str, datetime]
    optimization_scope: str = "full"  # full, consolidation_only, routing_only
    business_objectives: List[str] = ["minimize_cost", "maximize_efficiency", "reduce_emissions"]
    constraints: Optional[Dict[str, Any]] = None

class LogisticsOptimizationResponse(BaseModel):
    """Response for comprehensive logistics optimization"""
    optimization_id: str
    total_orders_processed: int
    total_trips_optimized: int
    cost_savings_percentage: float
    efficiency_improvement: float
    emission_reduction_percentage: float
    optimization_summary: Dict[str, Any]
    recommended_actions: List[str]
    created_at: datetime

class CapacityPlanningRequest(BaseModel):
    """Request for capacity planning analysis"""
    manufacturing_location_id: str
    planning_horizon_days: int = 30
    demand_forecast: Optional[Dict[str, Any]] = None
    capacity_constraints: Optional[Dict[str, Any]] = None

class CapacityPlanningResponse(BaseModel):
    """Response for capacity planning analysis"""
    planning_id: str
    current_capacity_utilization: float
    projected_demand: Dict[str, Any]
    capacity_gaps: List[Dict[str, Any]]
    recommended_capacity_adjustments: List[str]
    resource_requirements: Dict[str, Any]
    created_at: datetime

class RealTimeTrackingRequest(BaseModel):
    """Request for real-time tracking updates"""
    route_ids: List[str]
    tracking_frequency_minutes: int = 5
    alert_thresholds: Optional[Dict[str, Any]] = None

class RealTimeTrackingResponse(BaseModel):
    """Response for real-time tracking data"""
    tracking_session_id: str
    active_routes: List[Dict[str, Any]]
    live_updates: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    system_status: str
    last_updated: datetime

@router.post("/optimize-logistics", response_model=LogisticsOptimizationResponse)
async def optimize_comprehensive_logistics(
    request: LogisticsOptimizationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform comprehensive logistics optimization across multiple manufacturing locations.
    
    This endpoint orchestrates SKU consolidation, route optimization, and capacity planning
    to provide holistic logistics optimization recommendations.
    """
    try:
        # Create optimization log
        optimization_log = TripOptimizationLog(
            optimization_algorithm='ComprehensiveLogistics',
            input_parameters={
                'manufacturing_locations': request.manufacturing_location_ids,
                'date_range': {
                    'start': request.date_range['start'].isoformat(),
                    'end': request.date_range['end'].isoformat()
                },
                'optimization_scope': request.optimization_scope,
                'business_objectives': request.business_objectives
            },
            status='RUNNING'
        )
        db.add(optimization_log)
        await db.commit()
        await db.refresh(optimization_log)
        
        # Get all orders in the specified date range and locations
        orders_query = select(Order).where(
            and_(
                Order.delivery_date >= request.date_range['start'],
                Order.delivery_date <= request.date_range['end'],
                Order.status.in_(['CONFIRMED', 'PROCESSING', 'TRIP_QUEUED'])
            )
        )
        
        orders_result = await db.execute(orders_query)
        orders = orders_result.scalars().all()
        
        if not orders:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No orders found for optimization"
            )
        
        # Initialize optimization engines
        consolidation_engine = SKUConsolidationEngine(db)
        route_optimizer = TripRouteOptimizer()
        
        # Group orders by manufacturing location
        orders_by_location = {}
        for order in orders:
            # In a real system, you'd determine the manufacturing location based on order data
            # For now, we'll use the first location ID as default
            location_id = request.manufacturing_location_ids[0]
            if location_id not in orders_by_location:
                orders_by_location[location_id] = []
            orders_by_location[location_id].append(order)
        
        total_cost_savings = 0.0
        total_efficiency_improvement = 0.0
        optimization_results = []
        
        # Process each manufacturing location
        for location_id, location_orders in orders_by_location.items():
            # Perform SKU consolidation
            if request.optimization_scope in ['full', 'consolidation_only']:
                consolidated_skus = await consolidation_engine.consolidate_skus_by_manufacturer(
                    [str(order.id) for order in location_orders],
                    location_id
                )
                
                trip_groups = await consolidation_engine.create_trip_groups(
                    consolidated_skus,
                    location_id
                )
                
                # Calculate consolidation savings
                consolidation_savings = len(location_orders) - len(trip_groups)
                total_cost_savings += consolidation_savings * 0.15  # 15% cost savings per reduced trip
            
            # Perform route optimization
            if request.optimization_scope in ['full', 'routing_only']:
                for trip_group in trip_groups:
                    # Convert trip group to SKU delivery info
                    trip_skus = []
                    for consolidated_sku in trip_group.skus:
                        for location in consolidated_sku.delivery_locations:
                            trip_sku = SKUDeliveryInfo(
                                sku_code=consolidated_sku.sku_code,
                                product_name=consolidated_sku.product_name,
                                category=consolidated_sku.category,
                                brand=consolidated_sku.brand,
                                quantity=consolidated_sku.total_quantity,
                                weight_kg=consolidated_sku.total_weight_kg,
                                volume_m3=consolidated_sku.total_volume_m3,
                                temperature_requirement=consolidated_sku.temperature_requirement,
                                fragile=consolidated_sku.fragile,
                                delivery_locations=[location],
                                order_id=consolidated_sku.retailer_orders[0]  # Use first order ID
                            )
                            trip_skus.append(trip_sku)
                    
                    # Get manufacturing location details
                    manufacturing_location = await db.execute(
                        select(ManufacturingLocation).where(ManufacturingLocation.id == location_id)
                    )
                    manufacturing_location = manufacturing_location.scalar_one_or_none()
                    
                    if manufacturing_location:
                        manufacturing_location_dict = {
                            'id': str(manufacturing_location.id),
                            'name': manufacturing_location.name,
                            'latitude': float(manufacturing_location.latitude),
                            'longitude': float(manufacturing_location.longitude)
                        }
                        
                        # Optimize route
                        optimized_route = await route_optimizer.optimize_trip_route(
                            trip_skus,
                            manufacturing_location_dict
                        )
                        
                        # Calculate route efficiency improvement
                        baseline_distance = sum(
                            route_optimizer._calculate_distance(
                                manufacturing_location_dict['latitude'],
                                manufacturing_location_dict['longitude'],
                                stop.latitude,
                                stop.longitude
                            ) * 2  # Round trip
                            for stop in optimized_route.route_stops
                        )
                        
                        efficiency_improvement = (baseline_distance - optimized_route.total_distance_km) / baseline_distance
                        total_efficiency_improvement += efficiency_improvement
                        
                        optimization_results.append({
                            'location_id': location_id,
                            'trip_group_id': trip_group.group_id,
                            'optimized_distance': optimized_route.total_distance_km,
                            'efficiency_improvement': efficiency_improvement,
                            'capacity_utilization': optimized_route.capacity_utilization
                        })
        
        # Calculate overall metrics
        avg_efficiency_improvement = total_efficiency_improvement / len(optimization_results) if optimization_results else 0
        cost_savings_percentage = (total_cost_savings / len(orders)) * 100 if orders else 0
        emission_reduction = avg_efficiency_improvement * 0.8  # Approximate emission reduction
        
        # Update optimization log
        optimization_log.optimization_results = {
            'total_orders_processed': len(orders),
            'total_trips_optimized': len(optimization_results),
            'cost_savings_percentage': cost_savings_percentage,
            'efficiency_improvement': avg_efficiency_improvement,
            'emission_reduction_percentage': emission_reduction * 100,
            'optimization_details': optimization_results
        }
        optimization_log.status = 'SUCCESS'
        optimization_log.improvement_percentage = avg_efficiency_improvement * 100
        
        await db.commit()
        
        # Generate recommendations
        recommendations = []
        if cost_savings_percentage > 10:
            recommendations.append("Consider implementing automated consolidation for high-volume periods")
        if avg_efficiency_improvement > 0.15:
            recommendations.append("Route optimization shows significant potential - consider real-time implementation")
        if emission_reduction > 0.2:
            recommendations.append("Sustainability benefits are substantial - highlight in ESG reporting")
        
        return LogisticsOptimizationResponse(
            optimization_id=str(optimization_log.id),
            total_orders_processed=len(orders),
            total_trips_optimized=len(optimization_results),
            cost_savings_percentage=cost_savings_percentage,
            efficiency_improvement=avg_efficiency_improvement,
            emission_reduction_percentage=emission_reduction * 100,
            optimization_summary={
                'consolidation_groups': len(trip_groups) if 'trip_groups' in locals() else 0,
                'route_optimizations': len(optimization_results),
                'manufacturing_locations': len(orders_by_location),
                'processing_time_seconds': 0.0  # Will be calculated
            },
            recommended_actions=recommendations,
            created_at=optimization_log.created_at
        )
        
    except Exception as e:
        logger.error(f"Error in comprehensive logistics optimization: {str(e)}")
        if 'optimization_log' in locals():
            optimization_log.status = 'FAILED'
            optimization_log.error_message = str(e)
            await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform comprehensive logistics optimization"
        )

@router.post("/capacity-planning", response_model=CapacityPlanningResponse)
async def analyze_capacity_planning(
    request: CapacityPlanningRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze capacity planning for a manufacturing location.
    
    Provides insights into current capacity utilization, projected demand,
    and recommendations for capacity adjustments.
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
        
        # Calculate current capacity utilization
        current_date = date.today()
        past_30_days = current_date - timedelta(days=30)
        
        # Get historical trip data
        historical_trips = await db.execute(
            select(DeliveryRoute).where(
                and_(
                    DeliveryRoute.manufacturing_location_id == request.manufacturing_location_id,
                    DeliveryRoute.planned_date >= past_30_days,
                    DeliveryRoute.planned_date <= current_date
                )
            )
        )
        historical_trips = historical_trips.scalars().all()
        
        # Calculate current utilization
        total_capacity_utilized = sum(trip.capacity_utilization for trip in historical_trips)
        avg_capacity_utilization = total_capacity_utilized / len(historical_trips) if historical_trips else 0
        
        # Get available trucks
        available_trucks = await db.execute(
            select(Truck).where(
                Truck.manufacturer_location_id == request.manufacturing_location_id
            )
        )
        available_trucks = available_trucks.scalars().all()
        
        # Project future demand
        future_date = current_date + timedelta(days=request.planning_horizon_days)
        future_orders = await db.execute(
            select(Order).where(
                and_(
                    Order.delivery_date >= current_date,
                    Order.delivery_date <= future_date,
                    Order.status.in_(['CONFIRMED', 'PROCESSING', 'TRIP_QUEUED'])
                )
            )
        )
        future_orders = future_orders.scalars().all()
        
        # Calculate projected demand
        projected_trips_needed = len(future_orders) / 10  # Assume 10 orders per trip on average
        projected_capacity_needed = projected_trips_needed / len(available_trucks) if available_trucks else 0
        
        # Identify capacity gaps
        capacity_gaps = []
        if projected_capacity_needed > 0.8:  # 80% capacity threshold
            capacity_gaps.append({
                'type': 'high_utilization',
                'severity': 'medium' if projected_capacity_needed <= 0.95 else 'high',
                'description': f"Projected capacity utilization of {projected_capacity_needed:.1%} may cause delivery delays"
            })
        
        if len(available_trucks) < projected_trips_needed:
            capacity_gaps.append({
                'type': 'insufficient_trucks',
                'severity': 'high',
                'description': f"Need {projected_trips_needed - len(available_trucks)} additional trucks for projected demand"
            })
        
        # Generate recommendations
        recommendations = []
        if avg_capacity_utilization > 0.9:
            recommendations.append("Consider adding additional truck capacity or optimizing routes")
        if len(capacity_gaps) > 0:
            recommendations.append("Implement dynamic capacity scaling based on demand forecasts")
        if projected_capacity_needed > 1.0:
            recommendations.append("Consider outsourcing or partnership agreements for peak demand periods")
        
        return CapacityPlanningResponse(
            planning_id=f"CAPACITY-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            current_capacity_utilization=avg_capacity_utilization,
            projected_demand={
                'total_orders': len(future_orders),
                'projected_trips': projected_trips_needed,
                'capacity_required': projected_capacity_needed
            },
            capacity_gaps=capacity_gaps,
            recommended_capacity_adjustments=recommendations,
            resource_requirements={
                'current_trucks': len(available_trucks),
                'required_trucks': max(len(available_trucks), projected_trips_needed),
                'utilization_target': 0.85
            },
            created_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error in capacity planning analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze capacity planning"
        )

@router.post("/real-time-tracking", response_model=RealTimeTrackingResponse)
async def setup_real_time_tracking(
    request: RealTimeTrackingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Set up real-time tracking for active delivery routes.
    
    Provides live updates on route progress, delivery status, and alerts
    for exceptions or delays.
    """
    try:
        # Get active routes
        active_routes = await db.execute(
            select(DeliveryRoute).where(
                and_(
                    DeliveryRoute.id.in_(request.route_ids),
                    DeliveryRoute.status.in_(['IN_PROGRESS', 'ACTIVE'])
                )
            )
        )
        active_routes = active_routes.scalars().all()
        
        # Get current tracking data for each route
        tracking_data = []
        alerts = []
        
        for route in active_routes:
            # Get delivery tracking records
            delivery_trackings = await db.execute(
                select(DeliveryTracking).where(
                    DeliveryTracking.route_id == route.id
                )
            )
            delivery_trackings = delivery_trackings.scalars().all()
            
            # Calculate route progress
            total_stops = len(route.route_waypoints) if route.route_waypoints else 0
            completed_stops = len([t for t in delivery_trackings if t.status == 'DELIVERED'])
            progress_percentage = (completed_stops / total_stops) * 100 if total_stops > 0 else 0
            
            # Check for alerts
            current_time = datetime.now()
            for tracking in delivery_trackings:
                if tracking.estimated_arrival and tracking.estimated_arrival < current_time and tracking.status != 'DELIVERED':
                    alerts.append({
                        'type': 'delivery_delay',
                        'severity': 'medium',
                        'route_id': str(route.id),
                        'order_id': str(tracking.order_id),
                        'message': f"Order {tracking.order_id} is delayed beyond estimated arrival",
                        'timestamp': current_time
                    })
            
            tracking_data.append({
                'route_id': str(route.id),
                'route_name': route.route_name,
                'status': route.status,
                'progress_percentage': progress_percentage,
                'current_location': {
                    'latitude': float(delivery_trackings[-1].current_latitude) if delivery_trackings and delivery_trackings[-1].current_latitude else None,
                    'longitude': float(delivery_trackings[-1].current_longitude) if delivery_trackings and delivery_trackings[-1].current_longitude else None
                },
                'estimated_completion': route.planned_date,
                'deliveries_completed': completed_stops,
                'total_deliveries': total_stops
            })
        
        return RealTimeTrackingResponse(
            tracking_session_id=f"TRACKING-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            active_routes=tracking_data,
            live_updates=[],  # Will be populated by WebSocket in real implementation
            alerts=alerts,
            system_status='OPERATIONAL',
            last_updated=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error setting up real-time tracking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup real-time tracking"
        )

@router.get("/performance-metrics", response_model=Dict[str, Any])
async def get_performance_metrics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    manufacturing_location_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive performance metrics for logistics operations.
    
    Provides KPIs, efficiency metrics, and performance trends.
    """
    try:
        # Set default date range
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        # Build query filters
        query_filters = [
            DeliveryRoute.planned_date >= start_date,
            DeliveryRoute.planned_date <= end_date
        ]
        
        if manufacturing_location_id:
            query_filters.append(
                DeliveryRoute.manufacturing_location_id == manufacturing_location_id
            )
        
        # Get delivery routes
        routes = await db.execute(
            select(DeliveryRoute).where(and_(*query_filters))
        )
        routes = routes.scalars().all()
        
        # Calculate key metrics
        total_routes = len(routes)
        avg_capacity_utilization = sum(route.capacity_utilization for route in routes) / total_routes if total_routes > 0 else 0
        total_distance = sum(route.total_distance_km for route in routes)
        avg_optimization_score = sum(route.optimization_score or 0 for route in routes) / total_routes if total_routes > 0 else 0
        
        # Get optimization logs
        optimization_logs = await db.execute(
            select(TripOptimizationLog).where(
                and_(
                    TripOptimizationLog.created_at >= start_date,
                    TripOptimizationLog.created_at <= end_date,
                    TripOptimizationLog.status == 'SUCCESS'
                )
            )
        )
        optimization_logs = optimization_logs.scalars().all()
        
        # Calculate efficiency metrics
        avg_improvement = sum(log.improvement_percentage or 0 for log in optimization_logs) / len(optimization_logs) if optimization_logs else 0
        avg_execution_time = sum(log.execution_time_seconds or 0 for log in optimization_logs) / len(optimization_logs) if optimization_logs else 0
        
        # Get delivery performance
        completed_routes = [route for route in routes if route.status == 'COMPLETED']
        on_time_delivery_rate = len(completed_routes) / total_routes * 100 if total_routes > 0 else 0
        
        # Calculate cost metrics (simplified calculation)
        estimated_cost_per_km = 2.5  # Example cost per km
        total_operational_cost = total_distance * estimated_cost_per_km
        cost_savings = total_operational_cost * (avg_improvement / 100)
        
        return {
            'summary': {
                'total_routes': total_routes,
                'avg_capacity_utilization': round(avg_capacity_utilization, 3),
                'total_distance_km': round(total_distance, 2),
                'avg_optimization_score': round(avg_optimization_score, 2),
                'on_time_delivery_rate': round(on_time_delivery_rate, 2)
            },
            'efficiency_metrics': {
                'avg_improvement_percentage': round(avg_improvement, 2),
                'avg_execution_time_seconds': round(avg_execution_time, 2),
                'total_optimizations': len(optimization_logs),
                'success_rate': 100.0 if optimization_logs else 0.0
            },
            'cost_metrics': {
                'total_operational_cost': round(total_operational_cost, 2),
                'estimated_cost_savings': round(cost_savings, 2),
                'cost_per_km': estimated_cost_per_km,
                'roi_percentage': round((cost_savings / total_operational_cost) * 100, 2) if total_operational_cost > 0 else 0
            },
            'sustainability_metrics': {
                'emission_reduction_percentage': round(avg_improvement * 0.8, 2),
                'fuel_savings_liters': round(total_distance * 0.1 * (avg_improvement / 100), 2),
                'carbon_footprint_reduction_kg': round(total_distance * 2.3 * (avg_improvement / 100), 2)
            },
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': (end_date - start_date).days
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance metrics"
        )

@router.get("/delivery-tracking/{order_id}", response_model=DeliveryTrackingResponse)
async def get_delivery_tracking(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get real-time delivery tracking information for a specific order."""
    try:
        # Get order
        order = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = order.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Get delivery tracking
        delivery_tracking = await db.execute(
            select(DeliveryTracking).where(
                DeliveryTracking.order_id == order_id
            ).order_by(DeliveryTracking.created_at.desc())
        )
        delivery_tracking = delivery_tracking.scalar_one_or_none()
        
        if not delivery_tracking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Delivery tracking not found for this order"
            )
        
        # Get tracking history/updates
        tracking_updates = []
        if delivery_tracking.tracking_data:
            tracking_updates = delivery_tracking.tracking_data.get('updates', [])
        
        return DeliveryTrackingResponse(
            id=str(delivery_tracking.id),
            order_id=str(delivery_tracking.order_id),
            route_id=str(delivery_tracking.route_id) if delivery_tracking.route_id else None,
            truck_id=str(delivery_tracking.truck_id) if delivery_tracking.truck_id else None,
            status=delivery_tracking.status,
            current_latitude=float(delivery_tracking.current_latitude) if delivery_tracking.current_latitude else None,
            current_longitude=float(delivery_tracking.current_longitude) if delivery_tracking.current_longitude else None,
            estimated_arrival=delivery_tracking.estimated_arrival,
            actual_arrival=delivery_tracking.actual_arrival,
            distance_to_destination_km=float(delivery_tracking.distance_to_destination_km) if delivery_tracking.distance_to_destination_km else None,
            tracking_updates=tracking_updates,
            created_at=delivery_tracking.created_at
        )
        
    except Exception as e:
        logger.error(f"Error getting delivery tracking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve delivery tracking"
        )

@router.get("/optimization-logs", response_model=List[OptimizationLogResponse])
async def get_optimization_logs(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get optimization logs for monitoring and analysis."""
    try:
        query = select(TripOptimizationLog)
        
        if status:
            query = query.where(TripOptimizationLog.status == status)
        
        query = query.order_by(TripOptimizationLog.created_at.desc()).limit(limit).offset(offset)
        
        logs = await db.execute(query)
        logs = logs.scalars().all()
        
        return [
            OptimizationLogResponse(
                id=str(log.id),
                route_id=str(log.route_id) if log.route_id else None,
                optimization_algorithm=log.optimization_algorithm,
                input_parameters=log.input_parameters or {},
                optimization_results=log.optimization_results or {},
                execution_time_seconds=float(log.execution_time_seconds or 0),
                improvement_percentage=float(log.improvement_percentage or 0),
                status=log.status,
                error_message=log.error_message,
                created_at=log.created_at
            )
            for log in logs
        ]
        
    except Exception as e:
        logger.error(f"Error getting optimization logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve optimization logs"
        )
