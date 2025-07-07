from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base
import uuid

class OrderSKUItem(Base):
    __tablename__ = "order_sku_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    sku_code = Column(String(100), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    category = Column(String(100))
    brand = Column(String(100))
    quantity_ordered = Column(Integer, nullable=False)
    unit_of_measure = Column(String(50))
    unit_price = Column(Numeric(10, 2))
    total_price = Column(Numeric(10, 2))
    weight_kg = Column(Numeric(10, 2))
    volume_m3 = Column(Numeric(10, 2))
    temperature_requirement = Column(String(50))
    fragile = Column(Boolean, default=False)
    product_attributes = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="sku_items")

    def __repr__(self):
        return f"<OrderSKUItem(sku_code='{self.sku_code}', product_name='{self.product_name}', quantity={self.quantity_ordered})>"
