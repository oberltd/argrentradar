from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from ...database import get_db
from ...models import PropertySearchFilters, PropertyType, OperationType, Currency
from ...services import PropertyService
from ...utils import app_logger

router = APIRouter()


@router.get("/")
async def search_properties(
    request: Request,
    db: Session = Depends(get_db),
    property_type: Optional[PropertyType] = Query(None, description="Type of property"),
    operation_type: Optional[OperationType] = Query(None, description="Operation type (sale/rent)"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    currency: Optional[Currency] = Query(None, description="Currency"),
    min_bedrooms: Optional[int] = Query(None, description="Minimum bedrooms"),
    max_bedrooms: Optional[int] = Query(None, description="Maximum bedrooms"),
    min_bathrooms: Optional[int] = Query(None, description="Minimum bathrooms"),
    max_bathrooms: Optional[int] = Query(None, description="Maximum bathrooms"),
    min_area: Optional[float] = Query(None, description="Minimum area in m²"),
    max_area: Optional[float] = Query(None, description="Maximum area in m²"),
    province: Optional[str] = Query(None, description="Province"),
    city: Optional[str] = Query(None, description="City"),
    neighborhood: Optional[str] = Query(None, description="Neighborhood"),
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return")
):
    """Search properties with filters."""
    try:
        # Create filters object
        filters = PropertySearchFilters(
            property_type=property_type,
            operation_type=operation_type,
            min_price=min_price,
            max_price=max_price,
            currency=currency,
            min_bedrooms=min_bedrooms,
            max_bedrooms=max_bedrooms,
            min_bathrooms=min_bathrooms,
            max_bathrooms=max_bathrooms,
            min_area=min_area,
            max_area=max_area,
            province=province,
            city=city,
            neighborhood=neighborhood
        )
        
        property_service = PropertyService(db)
        properties = property_service.search_properties(filters, skip, limit)
        
        # Convert to dict format for JSON response
        result = []
        for prop in properties:
            result.append({
                "id": prop.id,
                "external_id": prop.external_id,
                "source_url": prop.source_url,
                "source_website": prop.source_website,
                "title": prop.title,
                "description": prop.description,
                "property_type": prop.property_type,
                "operation_type": prop.operation_type,
                "status": prop.status,
                "location": {
                    "country": prop.country,
                    "province": prop.province,
                    "city": prop.city,
                    "neighborhood": prop.neighborhood,
                    "address": prop.address,
                    "latitude": prop.latitude,
                    "longitude": prop.longitude,
                    "postal_code": prop.postal_code
                },
                "features": {
                    "bedrooms": prop.bedrooms,
                    "bathrooms": prop.bathrooms,
                    "parking_spaces": prop.parking_spaces,
                    "total_area": prop.total_area,
                    "covered_area": prop.covered_area,
                    "floor": prop.floor,
                    "total_floors": prop.total_floors,
                    "age": prop.age,
                    "amenities": prop.amenities,
                    "condition": prop.condition
                },
                "price": {
                    "amount": prop.price_amount,
                    "currency": prop.price_currency,
                    "price_per_sqm": prop.price_per_sqm,
                    "expenses": prop.expenses,
                    "expenses_currency": prop.expenses_currency
                },
                "contact": {
                    "agent_name": prop.agent_name,
                    "agency_name": prop.agency_name,
                    "phone": prop.phone,
                    "email": prop.email,
                    "website": prop.website
                },
                "images": {
                    "main_image": prop.main_image,
                    "gallery": prop.gallery,
                    "floor_plan": prop.floor_plan,
                    "virtual_tour": prop.virtual_tour
                },
                "metadata": {
                    "first_seen": prop.first_seen.isoformat() if prop.first_seen else None,
                    "last_updated": prop.last_updated.isoformat() if prop.last_updated else None,
                    "last_checked": prop.last_checked.isoformat() if prop.last_checked else None,
                    "is_featured": prop.is_featured,
                    "is_verified": prop.is_verified
                }
            })
        
        return {
            "properties": result,
            "count": len(result),
            "filters": filters.dict(),
            "pagination": {
                "skip": skip,
                "limit": limit
            }
        }
        
    except Exception as e:
        app_logger.error(f"Error searching properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{property_id}")
async def get_property(property_id: int, request: Request, db: Session = Depends(get_db)):
    """Get a specific property by ID."""
    try:
        property_service = PropertyService(db)
        property_obj = property_service.get_property_by_id(property_id)
        
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Record property view
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent")
        property_service.record_property_view(property_id, client_ip, user_agent)
        
        # Convert to dict format
        result = {
            "id": property_obj.id,
            "external_id": property_obj.external_id,
            "source_url": property_obj.source_url,
            "source_website": property_obj.source_website,
            "title": property_obj.title,
            "description": property_obj.description,
            "property_type": property_obj.property_type,
            "operation_type": property_obj.operation_type,
            "status": property_obj.status,
            "location": {
                "country": property_obj.country,
                "province": property_obj.province,
                "city": property_obj.city,
                "neighborhood": property_obj.neighborhood,
                "address": property_obj.address,
                "latitude": property_obj.latitude,
                "longitude": property_obj.longitude,
                "postal_code": property_obj.postal_code
            },
            "features": {
                "bedrooms": property_obj.bedrooms,
                "bathrooms": property_obj.bathrooms,
                "parking_spaces": property_obj.parking_spaces,
                "total_area": property_obj.total_area,
                "covered_area": property_obj.covered_area,
                "floor": property_obj.floor,
                "total_floors": property_obj.total_floors,
                "age": property_obj.age,
                "amenities": property_obj.amenities,
                "condition": property_obj.condition
            },
            "price": {
                "amount": property_obj.price_amount,
                "currency": property_obj.price_currency,
                "price_per_sqm": property_obj.price_per_sqm,
                "expenses": property_obj.expenses,
                "expenses_currency": property_obj.expenses_currency
            },
            "contact": {
                "agent_name": property_obj.agent_name,
                "agency_name": property_obj.agency_name,
                "phone": property_obj.phone,
                "email": property_obj.email,
                "website": property_obj.website
            },
            "images": {
                "main_image": property_obj.main_image,
                "gallery": property_obj.gallery,
                "floor_plan": property_obj.floor_plan,
                "virtual_tour": property_obj.virtual_tour
            },
            "metadata": {
                "first_seen": property_obj.first_seen.isoformat() if property_obj.first_seen else None,
                "last_updated": property_obj.last_updated.isoformat() if property_obj.last_updated else None,
                "last_checked": property_obj.last_checked.isoformat() if property_obj.last_checked else None,
                "is_featured": property_obj.is_featured,
                "is_verified": property_obj.is_verified,
                "raw_data": property_obj.raw_data
            }
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error getting property {property_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent/new")
async def get_recent_properties(
    hours: int = Query(24, description="Hours to look back"),
    limit: int = Query(50, description="Maximum number of properties"),
    db: Session = Depends(get_db)
):
    """Get recently added properties."""
    try:
        property_service = PropertyService(db)
        properties = property_service.get_recent_properties(hours, limit)
        
        result = []
        for prop in properties:
            result.append({
                "id": prop.id,
                "title": prop.title,
                "property_type": prop.property_type,
                "operation_type": prop.operation_type,
                "price_amount": prop.price_amount,
                "price_currency": prop.price_currency,
                "location": {
                    "city": prop.city,
                    "neighborhood": prop.neighborhood
                },
                "source_website": prop.source_website,
                "first_seen": prop.first_seen.isoformat() if prop.first_seen else None,
                "main_image": prop.main_image
            })
        
        return {
            "properties": result,
            "count": len(result),
            "hours": hours
        }
        
    except Exception as e:
        app_logger.error(f"Error getting recent properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent/updated")
async def get_updated_properties(
    hours: int = Query(24, description="Hours to look back"),
    limit: int = Query(50, description="Maximum number of properties"),
    db: Session = Depends(get_db)
):
    """Get recently updated properties."""
    try:
        property_service = PropertyService(db)
        properties = property_service.get_updated_properties(hours, limit)
        
        result = []
        for prop in properties:
            result.append({
                "id": prop.id,
                "title": prop.title,
                "property_type": prop.property_type,
                "operation_type": prop.operation_type,
                "price_amount": prop.price_amount,
                "price_currency": prop.price_currency,
                "location": {
                    "city": prop.city,
                    "neighborhood": prop.neighborhood
                },
                "source_website": prop.source_website,
                "last_updated": prop.last_updated.isoformat() if prop.last_updated else None,
                "main_image": prop.main_image
            })
        
        return {
            "properties": result,
            "count": len(result),
            "hours": hours
        }
        
    except Exception as e:
        app_logger.error(f"Error getting updated properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))