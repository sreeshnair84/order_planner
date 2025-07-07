from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base
import uuid

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    order_number = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="UPLOADED")
    original_filename = Column(String(255))
    file_path = Column(String(500))
    file_type = Column(String(20))
    file_size = Column(Integer)
    file_metadata = Column(JSONB)
    parsed_data = Column(JSONB)
    missing_fields = Column(JSONB)
    validation_errors = Column(JSONB)
    processing_notes = Column(Text)
    
    # Enhanced order details
    priority = Column(String(20), default="NORMAL")
    special_instructions = Column(Text)
    requested_delivery_date = Column(DateTime(timezone=True))
    delivery_address = Column(JSONB)
    retailer_info = Column(JSONB)
    
    # FMCG assignment fields
    retailer_id = Column(Integer, ForeignKey("retailers.id"), nullable=True)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=True)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True))
    assignment_notes = Column(Text)
    
    # Order summary fields
    total_sku_count = Column(Integer, default=0)
    total_quantity = Column(Integer, default=0)
    total_weight_kg = Column(Numeric(10, 2), default=0)
    total_volume_m3 = Column(Numeric(10, 2), default=0)
    subtotal = Column(Numeric(10, 2), default=0)
    tax = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), default=0)
    
    # Trip/logistics information
    trip_id = Column(String(100))
    trip_status = Column(String(50))
    estimated_delivery_date = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="orders", foreign_keys=[user_id])
    retailer = relationship("Retailer", back_populates="orders")
    manufacturer = relationship("Manufacturer", back_populates="orders")
    assigner = relationship("User", foreign_keys=[assigned_by])
    tracking_entries = relationship("OrderTracking", back_populates="order")
    email_communications = relationship("EmailCommunication", back_populates="order")
    sku_items = relationship("OrderSKUItem", back_populates="order")
    route_orders = relationship("RouteOrder", back_populates="order")
    consolidation_orders = relationship("ConsolidationOrder", back_populates="order")
    delivery_trackings = relationship("DeliveryTracking", back_populates="order")

    def __repr__(self):
        return f"<Order(number='{self.order_number}', status='{self.status}')>"
