from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case, extract, desc

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
from pydantic import BaseModel, Field

from app.database.connection import get_db
from app.models.user import User
from app.models.order import Order
from app.models.sku_item import OrderSKUItem
from app.models.tracking import OrderTracking
from app.models.trip_planning import DeliveryRoute, Truck, TripOptimizationLog
from app.api.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response"""
    total_orders: int
    processing_orders: int
    completed_orders: int
    pending_info_orders: int
    total_revenue: float
    avg_processing_time_hours: float
    on_time_delivery_rate: float
    order_accuracy_rate: float

class OrderStatusDistribution(BaseModel):
    """Order status distribution for charts"""
    status: str
    count: int
    percentage: float

class MonthlyOrderTrends(BaseModel):
    """Monthly order trends data"""
    month: str
    order_count: int
    revenue: float
    avg_order_value: float

class PerformanceMetrics(BaseModel):
    """System performance metrics"""
    total_orders: int
    average_processing_time: float
    on_time_delivery_rate: float
    customer_satisfaction: float
    fuel_efficiency: float
    cost_per_delivery: float
    order_accuracy: float
    system_uptime: float

class AnalyticsResponse(BaseModel):
    """Comprehensive analytics response"""
    dashboard_stats: DashboardStatsResponse
    status_distribution: List[OrderStatusDistribution]
    monthly_trends: List[MonthlyOrderTrends]
    performance_metrics: PerformanceMetrics
    recent_activities: List[Dict[str, Any]]

@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    date_range: Optional[int] = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=date_range)
        
        # Total orders query
        total_orders_query = select(func.count(Order.id)).where(
            and_(
                Order.created_at >= start_date,
                Order.created_at <= end_date
            )
        )
        total_orders_result = await db.execute(total_orders_query)
        total_orders = total_orders_result.scalar() or 0
        
        # Orders by status
        status_queries = {
            'processing': select(func.count(Order.id)).where(
                and_(
                    Order.status == 'PROCESSING',
                    Order.created_at >= start_date
                )
            ),
            'completed': select(func.count(Order.id)).where(
                and_(
                    Order.status.in_(['DELIVERED', 'COMPLETED']),
                    Order.created_at >= start_date
                )
            ),
            'pending_info': select(func.count(Order.id)).where(
                and_(
                    Order.status == 'PENDING_INFO',
                    Order.created_at >= start_date
                )
            )
        }
        
        processing_result = await db.execute(status_queries['processing'])
        processing_orders = processing_result.scalar() or 0
        
        completed_result = await db.execute(status_queries['completed'])
        completed_orders = completed_result.scalar() or 0
        
        pending_result = await db.execute(status_queries['pending_info'])
        pending_info_orders = pending_result.scalar() or 0
        
        # Revenue calculation
        revenue_query = select(func.sum(Order.total)).where(
            and_(
                Order.created_at >= start_date,
                Order.created_at <= end_date
            )
        )
        revenue_result = await db.execute(revenue_query)
        total_revenue = float(revenue_result.scalar() or 0)
        
        # Average processing time (mock calculation - in real system would be based on status changes)
        avg_processing_time = 24.5 if total_orders > 0 else 0
        
        # On-time delivery rate (mock - would be calculated from delivery tracking)
        on_time_delivery_rate = 94.2 if completed_orders > 0 else 0
        
        # Order accuracy rate (mock - would be calculated from customer feedback/returns)
        order_accuracy_rate = 98.7 if total_orders > 0 else 0
        
        return DashboardStatsResponse(
            total_orders=total_orders,
            processing_orders=processing_orders,
            completed_orders=completed_orders,
            pending_info_orders=pending_info_orders,
            total_revenue=total_revenue,
            avg_processing_time_hours=avg_processing_time,
            on_time_delivery_rate=on_time_delivery_rate,
            order_accuracy_rate=order_accuracy_rate
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve dashboard statistics"
        )

@router.get("/status-distribution", response_model=List[OrderStatusDistribution])
async def get_order_status_distribution(
    date_range: Optional[int] = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get order status distribution for charts"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=date_range)
        
        # Query for status distribution
        status_query = select(
            Order.status,
            func.count(Order.id).label('count')
        ).where(
            and_(
                Order.created_at >= start_date,
                Order.created_at <= end_date
            )
        ).group_by(Order.status)
        
        result = await db.execute(status_query)
        status_data = result.fetchall()
        
        # Calculate total for percentages
        total_orders = sum(row.count for row in status_data)
        
        distribution = []
        for row in status_data:
            percentage = (row.count / total_orders * 100) if total_orders > 0 else 0
            distribution.append(OrderStatusDistribution(
                status=row.status,
                count=row.count,
                percentage=round(percentage, 1)
            ))
        
        return distribution
        
    except Exception as e:
        logger.error(f"Error getting status distribution: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve status distribution"
        )

@router.get("/monthly-trends", response_model=List[MonthlyOrderTrends])
async def get_monthly_order_trends(
    months: Optional[int] = Query(6, description="Number of months to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get monthly order trends"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=months * 30)
        
        # Query for monthly trends
        trends_query = select(
            extract('year', Order.created_at).label('year'),
            extract('month', Order.created_at).label('month'),
            func.count(Order.id).label('order_count'),
            func.sum(Order.total).label('revenue')
        ).where(
            and_(
                Order.created_at >= start_date,
                Order.created_at <= end_date
            )
        ).group_by(
            extract('year', Order.created_at),
            extract('month', Order.created_at)
        ).order_by(
            extract('year', Order.created_at),
            extract('month', Order.created_at)
        )
        
        result = await db.execute(trends_query)
        trends_data = result.fetchall()
        
        trends = []
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for row in trends_data:
            month_name = month_names[int(row.month) - 1]
            revenue = float(row.revenue or 0)
            avg_order_value = revenue / row.order_count if row.order_count > 0 else 0
            
            trends.append(MonthlyOrderTrends(
                month=f"{month_name} {int(row.year)}",
                order_count=row.order_count,
                revenue=revenue,
                avg_order_value=round(avg_order_value, 2)
            ))
        
        return trends
        
    except Exception as e:
        logger.error(f"Error getting monthly trends: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve monthly trends"
        )
    
@router.get("/performance-metrics", response_model=PerformanceMetrics)
async def get_performance_metrics(
    date_range: Optional[int] = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system performance metrics"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=date_range)
        
        # Get total orders
        total_orders_query = select(func.count(Order.id)).where(
            and_(
                Order.created_at >= start_date,
                Order.created_at <= end_date
            )
        )
        total_orders_result = await db.execute(total_orders_query)
        total_orders = total_orders_result.scalar() or 0
        
        # Get completed orders for delivery rate calculation
        completed_query = select(func.count(Order.id)).where(
            and_(
                Order.status.in_(['DELIVERED', 'COMPLETED']),
                Order.created_at >= start_date
            )
        )
        completed_result = await db.execute(completed_query)
        completed_orders = completed_result.scalar() or 0
        
        # Calculate metrics (some are real, others are derived/estimated)
        average_processing_time = 24.5  # Hours - would be calculated from status change timestamps
        on_time_delivery_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
        customer_satisfaction = 4.6  # Would come from customer feedback system
        fuel_efficiency = 89.3  # Would come from fleet management system
        cost_per_delivery = 12.45  # Would be calculated from logistics costs
        order_accuracy = 98.7  # Would be calculated from returns/complaints
        system_uptime = 99.9  # Would come from monitoring system
        
        return PerformanceMetrics(
            total_orders=total_orders,
            average_processing_time=average_processing_time,
            on_time_delivery_rate=round(on_time_delivery_rate, 1),
            customer_satisfaction=customer_satisfaction,
            fuel_efficiency=fuel_efficiency,
            cost_per_delivery=cost_per_delivery,
            order_accuracy=order_accuracy,
            system_uptime=system_uptime
        )
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve performance metrics"
        )

@router.get("/recent-activities", response_model=List[Dict[str, Any]])
async def get_recent_activities(
    limit: Optional[int] = Query(10, description="Number of recent activities to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recent system activities"""
    try:
        # Get recent orders
        recent_orders_query = select(Order).order_by(desc(Order.created_at)).limit(limit)
        result = await db.execute(recent_orders_query)
        recent_orders = result.scalars().all()
        
        activities = []
        for order in recent_orders:
            activities.append({
                "id": str(order.id),
                "type": "order",
                "title": f"Order {order.order_number}",
                "description": f"Status: {order.status}",
                "timestamp": order.created_at.isoformat(),
                "status": order.status
            })
        
        return activities
        
    except Exception as e:
        logger.error(f"Error getting recent activities: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve recent activities"
        )

@router.get("/comprehensive", response_model=AnalyticsResponse)
async def get_comprehensive_analytics(
    date_range: Optional[int] = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive analytics data in one call"""
    try:
        # Get all analytics data
        dashboard_stats = await get_dashboard_stats(date_range, current_user, db)
        status_distribution = await get_order_status_distribution(date_range, current_user, db)
        monthly_trends = await get_monthly_order_trends(6, current_user, db)
        performance_metrics = await get_performance_metrics(date_range, current_user, db)
        recent_activities = await get_recent_activities(5, current_user, db)
        
        return AnalyticsResponse(
            dashboard_stats=dashboard_stats,
            status_distribution=status_distribution,
            monthly_trends=monthly_trends,
            performance_metrics=performance_metrics,
            recent_activities=recent_activities
        )
        
    except Exception as e:
        logger.error(f"Error getting comprehensive analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve comprehensive analytics"
        )

@router.get("/fleet/metrics")
async def get_fleet_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get fleet and logistics metrics"""
    try:
        # Query truck data
        trucks_query = select(func.count(Truck.id))
        trucks_result = await db.execute(trucks_query)
        active_vehicles = trucks_result.scalar() or 0
        
        # Query routes data
        routes_query = select(func.count(DeliveryRoute.id))
        routes_result = await db.execute(routes_query)
        active_routes = routes_result.scalar() or 0
        
        # Mock some metrics that would come from IoT/fleet management
        metrics = {
            "active_vehicles": active_vehicles,
            "active_routes": active_routes,
            "fuel_efficiency": 89.3,
            "system_uptime": 99.9,
            "average_delivery_time": 23.5,
            "route_optimization_savings": 15.2
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting fleet metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve fleet metrics"
        )

@router.get("/delivery-performance")
async def get_delivery_performance(
    date_range: Optional[int] = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get delivery performance trends by week"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=date_range)
        
        # For now, return mock weekly data
        # In a real system, this would calculate from delivery tracking data
        weeks = []
        for i in range(4):
            week_start = start_date + timedelta(days=i * 7)
            week_end = week_start + timedelta(days=7)
            
            # Mock calculations - in real system would query delivery data
            on_time_delivery = 92 + (i * 1)  # Trending upward
            avg_delivery_time = 24 - (i * 0.5)  # Trending downward (better)
            
            weeks.append({
                "week": f"Week {i + 1}",
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "on_time_delivery": on_time_delivery,
                "avg_delivery_time": avg_delivery_time
            })
        
        return weeks
        
    except Exception as e:
        logger.error(f"Error getting delivery performance: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve delivery performance"
        )

@router.get("/order-aggregation")
async def get_order_aggregation(
    group_by: Optional[str] = Query('category', description="Group by field"),
    date_range: Optional[int] = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get order aggregation data"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=date_range)
        
        # For now, return mock aggregation data based on orders
        # In a real system, this would aggregate by the specified field
        total_orders_query = select(func.count(Order.id)).where(
            and_(
                Order.created_at >= start_date,
                Order.created_at <= end_date
            )
        )
        total_orders_result = await db.execute(total_orders_query)
        total_orders = total_orders_result.scalar() or 0
        
        # Mock aggregation data - in real system would group by actual categories
        if total_orders > 0:
            aggregation_data = [
                {
                    "category": "Electronics",
                    "total_orders": max(1, total_orders // 4),
                    "total_value": 125000,
                    "status": "Completed",
                    "percentage": 35.5
                },
                {
                    "category": "Home & Garden", 
                    "total_orders": max(1, total_orders // 5),
                    "total_value": 89500,
                    "status": "In Progress",
                    "percentage": 25.2
                },
                {
                    "category": "Health & Beauty",
                    "total_orders": max(1, total_orders // 6),
                    "total_value": 67800,
                    "status": "Completed",
                    "percentage": 22.1
                },
                {
                    "category": "Sports & Outdoors",
                    "total_orders": max(1, total_orders // 7),
                    "total_value": 45600,
                    "status": "Pending",
                    "percentage": 17.2
                }
            ]
        else:
            aggregation_data = []
        
        return aggregation_data
        
    except Exception as e:
        logger.error(f"Error getting order aggregation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve order aggregation"
        )

@router.get("/notifications")
async def get_system_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system notifications"""
    try:
        # For now, return mock notifications
        # In a real system, this would come from a notifications table
        notifications = [
            {
                "id": 1,
                "message": "New order received",
                "type": "info",
                "timestamp": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
                "read": False
            },
            {
                "id": 2,
                "message": "Trip optimization completed",
                "type": "success", 
                "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "read": False
            },
            {
                "id": 3,
                "message": "System maintenance scheduled",
                "type": "warning",
                "timestamp": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
                "read": True
            }
        ]
        
        return notifications
        
    except Exception as e:
        logger.error(f"Error getting system notifications: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve system notifications"
        )
