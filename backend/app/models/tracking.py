from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
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

class AIAgentThread(Base):
    __tablename__ = "ai_agent_threads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    thread_id = Column(String(255), nullable=False, unique=True)  # Azure AI thread ID
    status = Column(String(50), nullable=False, default="CREATED")
    messages = Column(JSON, default=list)  # Store thread messages as JSON
    tools_used = Column(JSON, default=list)  # Track which tools were used
    extra_metadata = Column(JSON, default=dict)  # Additional metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="ai_agent_threads")

    def __repr__(self):
        return f"<AIAgentThread(order_id='{self.order_id}', thread_id='{self.thread_id}', status='{self.status}')>"
