from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

from ..models import PropertyType, OperationType, Currency, PropertyStatus

Base = declarative_base()


class PropertyDB(Base):
    __tablename__ = "properties"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(100), index=True)
    source_url = Column(String(500), unique=True, index=True)
    source_website = Column(String(100), index=True)
    
    # Basic information
    title = Column(String(500), index=True)
    description = Column(Text)
    property_type = Column(Enum(PropertyType), index=True)
    operation_type = Column(Enum(OperationType), index=True)
    status = Column(Enum(PropertyStatus), default=PropertyStatus.ACTIVE, index=True)
    
    # Location
    country = Column(String(100), default="Argentina")
    province = Column(String(100), index=True)
    city = Column(String(100), index=True)
    neighborhood = Column(String(100), index=True)
    address = Column(String(500))
    latitude = Column(Float)
    longitude = Column(Float)
    postal_code = Column(String(20))
    
    # Features
    bedrooms = Column(Integer, index=True)
    bathrooms = Column(Integer, index=True)
    parking_spaces = Column(Integer)
    total_area = Column(Float, index=True)
    covered_area = Column(Float)
    floor = Column(Integer)
    total_floors = Column(Integer)
    age = Column(Integer)
    amenities = Column(JSON)
    condition = Column(String(100))
    
    # Pricing
    price_amount = Column(Float, index=True)
    price_currency = Column(Enum(Currency), index=True)
    price_per_sqm = Column(Float)
    expenses = Column(Float)
    expenses_currency = Column(Enum(Currency))
    
    # Contact information
    agent_name = Column(String(200))
    agency_name = Column(String(200), index=True)
    phone = Column(String(50))
    email = Column(String(200))
    website = Column(String(500))
    
    # Media
    main_image = Column(String(500))
    gallery = Column(JSON)
    floor_plan = Column(String(500))
    virtual_tour = Column(String(500))
    
    # Metadata
    first_seen = Column(DateTime, default=func.now(), index=True)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)
    last_checked = Column(DateTime, default=func.now(), index=True)
    is_featured = Column(Boolean, default=False, index=True)
    is_verified = Column(Boolean, default=False, index=True)
    
    # Additional data
    raw_data = Column(JSON)
    
    def __repr__(self):
        return f"<PropertyDB(id={self.id}, title='{self.title}', source='{self.source_website}')>"


class PropertyHistory(Base):
    __tablename__ = "property_history"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, index=True)
    external_id = Column(String(100), index=True)
    source_website = Column(String(100), index=True)
    
    # What changed
    field_name = Column(String(100), index=True)
    old_value = Column(Text)
    new_value = Column(Text)
    
    # When it changed
    changed_at = Column(DateTime, default=func.now(), index=True)
    
    def __repr__(self):
        return f"<PropertyHistory(property_id={self.property_id}, field='{self.field_name}', changed_at='{self.changed_at}')>"


class ScrapingSession(Base):
    __tablename__ = "scraping_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    website = Column(String(100), index=True)
    started_at = Column(DateTime, default=func.now(), index=True)
    finished_at = Column(DateTime, index=True)
    status = Column(String(50), index=True)  # running, completed, failed
    
    # Statistics
    total_pages = Column(Integer)
    processed_pages = Column(Integer, default=0)
    total_properties = Column(Integer, default=0)
    new_properties = Column(Integer, default=0)
    updated_properties = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    
    # Configuration
    filters = Column(JSON)
    error_log = Column(Text)
    
    def __repr__(self):
        return f"<ScrapingSession(id={self.id}, website='{self.website}', status='{self.status}')>"


class PropertyAlert(Base):
    __tablename__ = "property_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True)
    user_email = Column(String(200), index=True)
    
    # Alert criteria (stored as JSON)
    criteria = Column(JSON)
    
    # Notification settings
    is_active = Column(Boolean, default=True, index=True)
    notification_frequency = Column(String(50), default="immediate")  # immediate, daily, weekly
    last_notification = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<PropertyAlert(id={self.id}, name='{self.name}', user='{self.user_email}')>"


class PropertyView(Base):
    __tablename__ = "property_views"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, index=True)
    external_id = Column(String(100), index=True)
    source_website = Column(String(100), index=True)
    
    # View details
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    viewed_at = Column(DateTime, default=func.now(), index=True)
    
    def __repr__(self):
        return f"<PropertyView(property_id={self.property_id}, viewed_at='{self.viewed_at}')>"