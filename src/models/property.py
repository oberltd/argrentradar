from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class PropertyType(str, Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    COMMERCIAL = "commercial"
    LAND = "land"
    OFFICE = "office"
    WAREHOUSE = "warehouse"


class OperationType(str, Enum):
    SALE = "sale"
    RENT = "rent"
    TEMPORARY_RENT = "temporary_rent"


class Currency(str, Enum):
    ARS = "ARS"  # Argentine Peso
    USD = "USD"  # US Dollar


class PropertyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SOLD = "sold"
    RENTED = "rented"


class Location(BaseModel):
    country: str = "Argentina"
    province: Optional[str] = None
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    postal_code: Optional[str] = None


class PropertyFeatures(BaseModel):
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    parking_spaces: Optional[int] = None
    total_area: Optional[float] = None  # in square meters
    covered_area: Optional[float] = None  # in square meters
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    age: Optional[int] = None  # in years
    amenities: List[str] = Field(default_factory=list)
    condition: Optional[str] = None


class PropertyPrice(BaseModel):
    amount: Optional[float] = None
    currency: Currency = Currency.ARS
    price_per_sqm: Optional[float] = None
    expenses: Optional[float] = None  # monthly expenses
    expenses_currency: Currency = Currency.ARS


class PropertyContact(BaseModel):
    agent_name: Optional[str] = None
    agency_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None


class PropertyImages(BaseModel):
    main_image: Optional[str] = None
    gallery: List[str] = Field(default_factory=list)
    floor_plan: Optional[str] = None
    virtual_tour: Optional[str] = None


class Property(BaseModel):
    # Unique identifiers
    id: Optional[str] = None
    external_id: Optional[str] = None  # ID from source website
    source_url: str
    source_website: str
    
    # Basic information
    title: str
    description: Optional[str] = None
    property_type: PropertyType
    operation_type: OperationType
    status: PropertyStatus = PropertyStatus.ACTIVE
    
    # Location
    location: Location
    
    # Features
    features: PropertyFeatures
    
    # Pricing
    price: PropertyPrice
    
    # Contact information
    contact: PropertyContact
    
    # Media
    images: PropertyImages
    
    # Metadata
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    is_featured: bool = False
    is_verified: bool = False
    
    # Additional data
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PropertySearchFilters(BaseModel):
    property_type: Optional[PropertyType] = None
    operation_type: Optional[OperationType] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    currency: Optional[Currency] = None
    min_bedrooms: Optional[int] = None
    max_bedrooms: Optional[int] = None
    min_bathrooms: Optional[int] = None
    max_bathrooms: Optional[int] = None
    min_area: Optional[float] = None
    max_area: Optional[float] = None
    province: Optional[str] = None
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    amenities: List[str] = Field(default_factory=list)
    
    
class PropertyUpdate(BaseModel):
    price: Optional[PropertyPrice] = None
    status: Optional[PropertyStatus] = None
    description: Optional[str] = None
    images: Optional[PropertyImages] = None
    features: Optional[PropertyFeatures] = None
    contact: Optional[PropertyContact] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)