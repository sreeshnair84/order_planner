from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database.connection import Base
from datetime import datetime

# Association table for retailer-manufacturer relationships
retailer_manufacturer_association = Table(
    'retailer_manufacturer_association',
    Base.metadata,
    Column('retailer_id', Integer, ForeignKey('retailers.id'), primary_key=True),
    Column('manufacturer_id', Integer, ForeignKey('manufacturers.id'), primary_key=True)
)

class Retailer(Base):
    __tablename__ = "retailers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    country = Column(String(100))
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    manufacturers = relationship(
        "Manufacturer", 
        secondary=retailer_manufacturer_association,
        back_populates="retailers"
    )
    orders = relationship("Order", back_populates="retailer")
    
    def __repr__(self):
        return f"<Retailer(name='{self.name}', code='{self.code}')>"

class Manufacturer(Base):
    __tablename__ = "manufacturers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    country = Column(String(100))
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Business details
    lead_time_days = Column(Integer, default=7)
    min_order_value = Column(Integer, default=0)
    preferred_payment_terms = Column(String(100))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    retailers = relationship(
        "Retailer", 
        secondary=retailer_manufacturer_association,
        back_populates="manufacturers"
    )
    orders = relationship("Order", back_populates="manufacturer")
    routes = relationship("Route", back_populates="manufacturer")
    
    def __repr__(self):
        return f"<Manufacturer(name='{self.name}', code='{self.code}')>"

class Route(Base):
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    manufacturer_id = Column(Integer, ForeignKey('manufacturers.id'), nullable=False)
    
    # Route details
    origin_city = Column(String(100), nullable=False)
    origin_state = Column(String(50))
    origin_country = Column(String(100))
    destination_city = Column(String(100), nullable=False)
    destination_state = Column(String(50))
    destination_country = Column(String(100))
    
    # Logistics details
    distance_km = Column(Integer)
    estimated_transit_days = Column(Integer, default=3)
    transport_mode = Column(String(50), default='truck')  # truck, rail, air, sea
    cost_per_km = Column(Integer, default=0)  # in cents
    max_weight_kg = Column(Integer)
    max_volume_m3 = Column(Integer)
    
    # Status
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    manufacturer = relationship("Manufacturer", back_populates="routes")
    
    def __repr__(self):
        return f"<Route(name='{self.name}', {self.origin_city} → {self.destination_city})>"
