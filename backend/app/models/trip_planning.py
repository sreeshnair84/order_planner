from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Numeric, Boolean, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base
import uuid

class ManufacturingLocation(Base):
    __tablename__ = "manufacturing_locations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    address = Column(JSONB, nullable=False)
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    capacity_info = Column(JSONB)
    operating_hours = Column(JSONB)
    logistics_partners = Column(ARRAY(String))
    status = Column(String(50), default='ACTIVE')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    delivery_routes = relationship("DeliveryRoute", back_populates="manufacturing_location")
    consolidation_groups = relationship("ConsolidationGroup", back_populates="manufacturing_location")

    def __repr__(self):
        return f"<ManufacturingLocation(name='{self.name}', status='{self.status}')>"

class Truck(Base):
    __tablename__ = "trucks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    truck_number = Column(String(100), unique=True, nullable=False)
    max_weight_kg = Column(Numeric(10, 2))
    max_volume_m3 = Column(Numeric(10, 2))
    current_latitude = Column(Numeric(10, 7))
    current_longitude = Column(Numeric(10, 7))
    status = Column(String(50), default='AVAILABLE')
    driver_info = Column(JSONB)
    manufacturer_location_id = Column(UUID(as_uuid=True), ForeignKey("manufacturing_locations.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    delivery_routes = relationship("DeliveryRoute", back_populates="truck")
    delivery_trackings = relationship("DeliveryTracking", back_populates="truck")

    def __repr__(self):
        return f"<Truck(number='{self.truck_number}', status='{self.status}')>"

class DeliveryRoute(Base):
    __tablename__ = "delivery_routes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_name = Column(String(255))
    manufacturing_location_id = Column(UUID(as_uuid=True), ForeignKey("manufacturing_locations.id"))
    truck_id = Column(UUID(as_uuid=True), ForeignKey("trucks.id"))
    planned_date = Column(Date)
    status = Column(String(50), default='PLANNED')
    total_distance_km = Column(Numeric(10, 2))
    estimated_duration_hours = Column(Numeric(5, 2))
    actual_duration_hours = Column(Numeric(5, 2))
    capacity_utilization = Column(Numeric(5, 2))
    route_waypoints = Column(JSONB)  # Array of coordinates and delivery info
    sku_count = Column(Integer, default=0)
    total_weight_kg = Column(Numeric(10, 2), default=0)
    total_volume_m3 = Column(Numeric(10, 2), default=0)
    optimization_score = Column(Numeric(5, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    manufacturing_location = relationship("ManufacturingLocation", back_populates="delivery_routes")
    truck = relationship("Truck", back_populates="delivery_routes")
    route_orders = relationship("RouteOrder", back_populates="delivery_route")
    delivery_trackings = relationship("DeliveryTracking", back_populates="delivery_route")

    def __repr__(self):
        return f"<DeliveryRoute(name='{self.route_name}', status='{self.status}')>"

class RouteOrder(Base):
    __tablename__ = "route_orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey("delivery_routes.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    sequence_number = Column(Integer)
    estimated_arrival_time = Column(DateTime(timezone=True))
    actual_arrival_time = Column(DateTime(timezone=True))
    delivery_status = Column(String(50), default='SCHEDULED')
    delivery_notes = Column(Text)
    sku_items_count = Column(Integer, default=0)
    delivery_weight_kg = Column(Numeric(10, 2))
    delivery_volume_m3 = Column(Numeric(10, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    delivery_route = relationship("DeliveryRoute", back_populates="route_orders")
    order = relationship("Order", back_populates="route_orders")

    def __repr__(self):
        return f"<RouteOrder(route_id='{self.route_id}', order_id='{self.order_id}', status='{self.delivery_status}')>"

class ConsolidationGroup(Base):
    __tablename__ = "consolidation_groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_name = Column(String(255))
    manufacturing_location_id = Column(UUID(as_uuid=True), ForeignKey("manufacturing_locations.id"))
    consolidation_date = Column(Date)
    status = Column(String(50), default='ACTIVE')
    total_orders = Column(Integer, default=0)
    total_sku_count = Column(Integer, default=0)
    total_weight_kg = Column(Numeric(10, 2), default=0)
    total_volume_m3 = Column(Numeric(10, 2), default=0)
    geographic_center_lat = Column(Numeric(10, 7))
    geographic_center_lon = Column(Numeric(10, 7))
    consolidation_efficiency = Column(Numeric(5, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    manufacturing_location = relationship("ManufacturingLocation", back_populates="consolidation_groups")
    consolidation_orders = relationship("ConsolidationOrder", back_populates="consolidation_group")

    def __repr__(self):
        return f"<ConsolidationGroup(name='{self.group_name}', status='{self.status}')>"

class ConsolidationOrder(Base):
    __tablename__ = "consolidation_orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consolidation_group_id = Column(UUID(as_uuid=True), ForeignKey("consolidation_groups.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    priority_score = Column(Numeric(5, 2))
    geographic_efficiency = Column(Numeric(5, 2))
    sku_compatibility_score = Column(Numeric(5, 2))
    consolidation_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    consolidation_group = relationship("ConsolidationGroup", back_populates="consolidation_orders")
    order = relationship("Order", back_populates="consolidation_orders")

    def __repr__(self):
        return f"<ConsolidationOrder(group_id='{self.consolidation_group_id}', order_id='{self.order_id}')>"

class DeliveryTracking(Base):
    __tablename__ = "delivery_tracking"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    route_id = Column(UUID(as_uuid=True), ForeignKey("delivery_routes.id"))
    truck_id = Column(UUID(as_uuid=True), ForeignKey("trucks.id"))
    status = Column(String(50), nullable=False)
    current_latitude = Column(Numeric(10, 7))
    current_longitude = Column(Numeric(10, 7))
    estimated_arrival = Column(DateTime(timezone=True))
    actual_arrival = Column(DateTime(timezone=True))
    distance_to_destination_km = Column(Numeric(10, 2))
    notes = Column(Text)
    tracking_data = Column(JSONB)  # Additional tracking information
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="delivery_trackings")
    delivery_route = relationship("DeliveryRoute", back_populates="delivery_trackings")
    truck = relationship("Truck", back_populates="delivery_trackings")

    def __repr__(self):
        return f"<DeliveryTracking(order_id='{self.order_id}', status='{self.status}')>"

class TripOptimizationLog(Base):
    __tablename__ = "trip_optimization_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey("delivery_routes.id"))
    optimization_algorithm = Column(String(100))
    input_parameters = Column(JSONB)
    optimization_results = Column(JSONB)
    execution_time_seconds = Column(Numeric(10, 3))
    improvement_percentage = Column(Numeric(5, 2))
    status = Column(String(50))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    delivery_route = relationship("DeliveryRoute")

    def __repr__(self):
        return f"<TripOptimizationLog(route_id='{self.route_id}', status='{self.status}')>"
