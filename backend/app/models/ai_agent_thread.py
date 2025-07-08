from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base
import uuid

class AIAgentThread(Base):
    __tablename__ = "ai_agent_threads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    thread_id = Column(String(255), nullable=False, unique=True, index=True)
    status = Column(String(50), nullable=False, default="CREATED")
    messages = Column(JSONB, default=list)
    tools_used = Column(JSONB, default=list)
    metadata = Column(JSONB, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="ai_threads")

    def __repr__(self):
        return f"<AIAgentThread(thread_id='{self.thread_id}', status='{self.status}')>"
