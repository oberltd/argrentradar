from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, timedelta

from ..database.models import PropertyDB, PropertyHistory, PropertyView
from ..models import Property, PropertySearchFilters, PropertyUpdate
from ..utils import app_logger


class PropertyService:
    """Service for property-related operations."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def create_property(self, property_data: Property) -> PropertyDB:
        """Create a new property in the database."""
        try:
            # Check if property already exists
            existing = self.get_property_by_url(property_data.source_url)
            if existing:
                app_logger.warning(f"Property already exists: {property_data.source_url}")
                return existing
                
            # Convert Pydantic model to SQLAlchemy model
            db_property = PropertyDB(
                external_id=property_data.external_id,
                source_url=property_data.source_url,
                source_website=property_data.source_website,
                title=property_data.title,
                description=property_data.description,
                property_type=property_data.property_type,
                operation_type=property_data.operation_type,
                status=property_data.status,
                
                # Location
                country=property_data.location.country,
                province=property_data.location.province,
                city=property_data.location.city,
                neighborhood=property_data.location.neighborhood,
                address=property_data.location.address,
                latitude=property_data.location.latitude,
                longitude=property_data.location.longitude,
                postal_code=property_data.location.postal_code,
                
                # Features
                bedrooms=property_data.features.bedrooms,
                bathrooms=property_data.features.bathrooms,
                parking_spaces=property_data.features.parking_spaces,
                total_area=property_data.features.total_area,
                covered_area=property_data.features.covered_area,
                floor=property_data.features.floor,
                total_floors=property_data.features.total_floors,
                age=property_data.features.age,
                amenities=property_data.features.amenities,
                condition=property_data.features.condition,
                
                # Pricing
                price_amount=property_data.price.amount,
                price_currency=property_data.price.currency,
                price_per_sqm=property_data.price.price_per_sqm,
                expenses=property_data.price.expenses,
                expenses_currency=property_data.price.expenses_currency,
                
                # Contact
                agent_name=property_data.contact.agent_name,
                agency_name=property_data.contact.agency_name,
                phone=property_data.contact.phone,
                email=property_data.contact.email,
                website=property_data.contact.website,
                
                # Media
                main_image=property_data.images.main_image,
                gallery=property_data.images.gallery,
                floor_plan=property_data.images.floor_plan,
                virtual_tour=property_data.images.virtual_tour,
                
                # Metadata
                first_seen=property_data.first_seen,
                last_updated=property_data.last_updated,
                last_checked=property_data.last_checked,
                is_featured=property_data.is_featured,
                is_verified=property_data.is_verified,
                raw_data=property_data.raw_data
            )
            
            self.db.add(db_property)
            self.db.commit()
            self.db.refresh(db_property)
            
            app_logger.info(f"Created new property: {db_property.id} - {db_property.title}")
            return db_property
            
        except Exception as e:
            self.db.rollback()
            app_logger.error(f"Error creating property: {e}")
            raise
            
    def update_property(self, property_id: int, update_data: PropertyUpdate) -> Optional[PropertyDB]:
        """Update an existing property."""
        try:
            db_property = self.db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
            if not db_property:
                return None
                
            # Track changes for history
            changes = []
            
            # Update fields if provided
            if update_data.price:
                if update_data.price.amount != db_property.price_amount:
                    changes.append(('price_amount', db_property.price_amount, update_data.price.amount))
                    db_property.price_amount = update_data.price.amount
                    
                if update_data.price.currency != db_property.price_currency:
                    changes.append(('price_currency', db_property.price_currency, update_data.price.currency))
                    db_property.price_currency = update_data.price.currency
                    
                if update_data.price.expenses != db_property.expenses:
                    changes.append(('expenses', db_property.expenses, update_data.price.expenses))
                    db_property.expenses = update_data.price.expenses
                    
            if update_data.status and update_data.status != db_property.status:
                changes.append(('status', db_property.status, update_data.status))
                db_property.status = update_data.status
                
            if update_data.description and update_data.description != db_property.description:
                changes.append(('description', db_property.description, update_data.description))
                db_property.description = update_data.description
                
            # Update timestamps
            db_property.last_updated = update_data.last_updated
            db_property.last_checked = datetime.utcnow()
            
            self.db.commit()
            
            # Record changes in history
            for field_name, old_value, new_value in changes:
                self.record_property_change(db_property.id, field_name, old_value, new_value)
                
            app_logger.info(f"Updated property: {property_id} - {len(changes)} changes")
            return db_property
            
        except Exception as e:
            self.db.rollback()
            app_logger.error(f"Error updating property {property_id}: {e}")
            raise
            
    def get_property_by_id(self, property_id: int) -> Optional[PropertyDB]:
        """Get property by ID."""
        return self.db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
        
    def get_property_by_url(self, source_url: str) -> Optional[PropertyDB]:
        """Get property by source URL."""
        return self.db.query(PropertyDB).filter(PropertyDB.source_url == source_url).first()
        
    def get_property_by_external_id(self, external_id: str, source_website: str) -> Optional[PropertyDB]:
        """Get property by external ID and source website."""
        return self.db.query(PropertyDB).filter(
            and_(
                PropertyDB.external_id == external_id,
                PropertyDB.source_website == source_website
            )
        ).first()
        
    def search_properties(self, filters: PropertySearchFilters, skip: int = 0, limit: int = 100) -> List[PropertyDB]:
        """Search properties with filters."""
        query = self.db.query(PropertyDB)
        
        # Apply filters
        if filters.property_type:
            query = query.filter(PropertyDB.property_type == filters.property_type)
            
        if filters.operation_type:
            query = query.filter(PropertyDB.operation_type == filters.operation_type)
            
        if filters.min_price:
            query = query.filter(PropertyDB.price_amount >= filters.min_price)
            
        if filters.max_price:
            query = query.filter(PropertyDB.price_amount <= filters.max_price)
            
        if filters.currency:
            query = query.filter(PropertyDB.price_currency == filters.currency)
            
        if filters.min_bedrooms:
            query = query.filter(PropertyDB.bedrooms >= filters.min_bedrooms)
            
        if filters.max_bedrooms:
            query = query.filter(PropertyDB.bedrooms <= filters.max_bedrooms)
            
        if filters.min_bathrooms:
            query = query.filter(PropertyDB.bathrooms >= filters.min_bathrooms)
            
        if filters.max_bathrooms:
            query = query.filter(PropertyDB.bathrooms <= filters.max_bathrooms)
            
        if filters.min_area:
            query = query.filter(PropertyDB.total_area >= filters.min_area)
            
        if filters.max_area:
            query = query.filter(PropertyDB.total_area <= filters.max_area)
            
        if filters.province:
            query = query.filter(PropertyDB.province.ilike(f"%{filters.province}%"))
            
        if filters.city:
            query = query.filter(PropertyDB.city.ilike(f"%{filters.city}%"))
            
        if filters.neighborhood:
            query = query.filter(PropertyDB.neighborhood.ilike(f"%{filters.neighborhood}%"))
            
        # Order by last updated
        query = query.order_by(desc(PropertyDB.last_updated))
        
        return query.offset(skip).limit(limit).all()
        
    def get_recent_properties(self, hours: int = 24, limit: int = 50) -> List[PropertyDB]:
        """Get recently added properties."""
        since = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(PropertyDB).filter(
            PropertyDB.first_seen >= since
        ).order_by(desc(PropertyDB.first_seen)).limit(limit).all()
        
    def get_updated_properties(self, hours: int = 24, limit: int = 50) -> List[PropertyDB]:
        """Get recently updated properties."""
        since = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(PropertyDB).filter(
            PropertyDB.last_updated >= since
        ).order_by(desc(PropertyDB.last_updated)).limit(limit).all()
        
    def record_property_change(self, property_id: int, field_name: str, old_value: Any, new_value: Any):
        """Record a property change in history."""
        try:
            history_entry = PropertyHistory(
                property_id=property_id,
                field_name=field_name,
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(new_value) if new_value is not None else None,
                changed_at=datetime.utcnow()
            )
            
            self.db.add(history_entry)
            self.db.commit()
            
        except Exception as e:
            app_logger.error(f"Error recording property change: {e}")
            
    def record_property_view(self, property_id: int, ip_address: str = None, user_agent: str = None):
        """Record a property view."""
        try:
            property_obj = self.get_property_by_id(property_id)
            if not property_obj:
                return
                
            view_entry = PropertyView(
                property_id=property_id,
                external_id=property_obj.external_id,
                source_website=property_obj.source_website,
                ip_address=ip_address,
                user_agent=user_agent,
                viewed_at=datetime.utcnow()
            )
            
            self.db.add(view_entry)
            self.db.commit()
            
        except Exception as e:
            app_logger.error(f"Error recording property view: {e}")
            
    def get_property_statistics(self) -> Dict[str, Any]:
        """Get property statistics."""
        try:
            total_properties = self.db.query(PropertyDB).count()
            
            # Properties by type
            by_type = {}
            for prop_type in ['apartment', 'house', 'commercial', 'land', 'office']:
                count = self.db.query(PropertyDB).filter(PropertyDB.property_type == prop_type).count()
                by_type[prop_type] = count
                
            # Properties by operation
            by_operation = {}
            for op_type in ['sale', 'rent']:
                count = self.db.query(PropertyDB).filter(PropertyDB.operation_type == op_type).count()
                by_operation[op_type] = count
                
            # Properties by source
            by_source = {}
            for website in ['zonaprop.com.ar', 'argenprop.com', 'remax.com.ar']:
                count = self.db.query(PropertyDB).filter(PropertyDB.source_website == website).count()
                by_source[website] = count
                
            # Recent activity
            last_24h = datetime.utcnow() - timedelta(hours=24)
            new_last_24h = self.db.query(PropertyDB).filter(PropertyDB.first_seen >= last_24h).count()
            updated_last_24h = self.db.query(PropertyDB).filter(PropertyDB.last_updated >= last_24h).count()
            
            return {
                'total_properties': total_properties,
                'by_type': by_type,
                'by_operation': by_operation,
                'by_source': by_source,
                'activity': {
                    'new_last_24h': new_last_24h,
                    'updated_last_24h': updated_last_24h
                }
            }
            
        except Exception as e:
            app_logger.error(f"Error getting property statistics: {e}")
            return {}