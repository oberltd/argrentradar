from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from ...database import get_db
from ...services import PropertyService, ScrapingService
from ...utils import app_logger

router = APIRouter()


@router.get("/properties")
async def get_property_statistics(db: Session = Depends(get_db)):
    """Get property statistics."""
    try:
        property_service = PropertyService(db)
        stats = property_service.get_property_statistics()
        
        return {
            "statistics": stats,
            "timestamp": "2025-06-29T00:00:00Z"  # Current timestamp would be datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        app_logger.error(f"Error getting property statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scraping")
async def get_scraping_statistics(db: Session = Depends(get_db)):
    """Get scraping statistics."""
    try:
        scraping_service = ScrapingService(db)
        stats = scraping_service.get_scraping_statistics()
        
        return {
            "statistics": stats,
            "timestamp": "2025-06-29T00:00:00Z"  # Current timestamp would be datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        app_logger.error(f"Error getting scraping statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview")
async def get_overview_statistics(db: Session = Depends(get_db)):
    """Get overview statistics combining properties and scraping data."""
    try:
        property_service = PropertyService(db)
        scraping_service = ScrapingService(db)
        
        property_stats = property_service.get_property_statistics()
        scraping_stats = scraping_service.get_scraping_statistics()
        
        # Calculate additional metrics
        overview = {
            "properties": property_stats,
            "scraping": scraping_stats,
            "summary": {
                "total_properties": property_stats.get("total_properties", 0),
                "total_scraping_sessions": scraping_stats.get("total_sessions", 0),
                "success_rate": 0,
                "active_websites": len([k for k, v in scraping_stats.get("by_website", {}).items() if v > 0])
            }
        }
        
        # Calculate success rate
        total_sessions = scraping_stats.get("total_sessions", 0)
        completed_sessions = scraping_stats.get("completed_sessions", 0)
        if total_sessions > 0:
            overview["summary"]["success_rate"] = round((completed_sessions / total_sessions) * 100, 2)
        
        return {
            "overview": overview,
            "timestamp": "2025-06-29T00:00:00Z"  # Current timestamp would be datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        app_logger.error(f"Error getting overview statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_data(db: Session = Depends(get_db)):
    """Get dashboard data for frontend."""
    try:
        property_service = PropertyService(db)
        scraping_service = ScrapingService(db)
        
        # Get statistics
        property_stats = property_service.get_property_statistics()
        scraping_stats = scraping_service.get_scraping_statistics()
        
        # Get recent data
        recent_properties = property_service.get_recent_properties(hours=24, limit=5)
        recent_sessions = scraping_service.get_scraping_sessions(limit=5)
        
        # Format recent properties
        recent_props_data = []
        for prop in recent_properties:
            recent_props_data.append({
                "id": prop.id,
                "title": prop.title,
                "property_type": prop.property_type,
                "operation_type": prop.operation_type,
                "price_amount": prop.price_amount,
                "price_currency": prop.price_currency,
                "city": prop.city,
                "neighborhood": prop.neighborhood,
                "source_website": prop.source_website,
                "first_seen": prop.first_seen.isoformat() if prop.first_seen else None
            })
        
        # Format recent sessions
        recent_sessions_data = []
        for session in recent_sessions:
            recent_sessions_data.append({
                "id": session.id,
                "website": session.website,
                "status": session.status,
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "finished_at": session.finished_at.isoformat() if session.finished_at else None,
                "new_properties": session.new_properties,
                "updated_properties": session.updated_properties,
                "errors": session.errors
            })
        
        return {
            "statistics": {
                "properties": property_stats,
                "scraping": scraping_stats
            },
            "recent_data": {
                "properties": recent_props_data,
                "sessions": recent_sessions_data
            },
            "timestamp": "2025-06-29T00:00:00Z"  # Current timestamp would be datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        app_logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))