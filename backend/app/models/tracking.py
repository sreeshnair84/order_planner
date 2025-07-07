from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base
import uuid

class OrderTracking(Base):
    __tablename__ = "order_tracking"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    status = Column(String(50), nullable=False)
    message = Column(Text)
    details = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="tracking_entries")

    def __repr__(self):
        return f"<OrderTracking(order_id='{self.order_id}', status='{self.status}')>"

class EmailCommunication(Base):
    __tablename__ = "email_communications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    email_type = Column(String(50), nullable=False)
    recipient = Column(String(255), nullable=False)
    sender = Column(String(255))
    subject = Column(String(255))
    body = Column(Text)
    sent_at = Column(DateTime(timezone=True))
    response_received_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), nullable=False, default="pending")
    
    # Relationships
    order = relationship("Order", back_populates="email_communications")

    def __repr__(self):
        return f"<EmailCommunication(order_id='{self.order_id}', type='{self.email_type}')>"
