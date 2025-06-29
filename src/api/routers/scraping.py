from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from ...database import get_db
from ...database.models import ScrapingSession
from ...models import PropertySearchFilters, PropertyType, OperationType, Currency
from ...services import ScrapingService
from ...utils import app_logger

router = APIRouter()


@router.post("/start")
async def start_scraping(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    website: Optional[str] = None,
    property_type: Optional[PropertyType] = None,
    operation_type: Optional[OperationType] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    currency: Optional[Currency] = None,
    min_bedrooms: Optional[int] = None,
    max_bedrooms: Optional[int] = None,
    min_bathrooms: Optional[int] = None,
    max_bathrooms: Optional[int] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    neighborhood: Optional[str] = None,
    max_pages: Optional[int] = None
):
    """Start scraping process."""
    try:
        # Create filters
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
        
        scraping_service = ScrapingService(db)
        
        if website:
            # Scrape specific website
            if website not in ['zonaprop.com.ar', 'argenprop.com']:
                raise HTTPException(status_code=400, detail=f"Unsupported website: {website}")
            
            # Add background task
            background_tasks.add_task(
                scraping_service.scrape_website,
                website,
                filters,
                max_pages
            )
            
            return {
                "message": f"Scraping started for {website}",
                "website": website,
                "filters": filters.dict(),
                "max_pages": max_pages
            }
        else:
            # Scrape all websites
            background_tasks.add_task(
                scraping_service.scrape_all_websites,
                filters,
                max_pages
            )
            
            return {
                "message": "Scraping started for all websites",
                "websites": ["zonaprop.com.ar", "argenprop.com", "mercadolibre.com.ar", "remax.com.ar", "properati.com.ar", "inmuebles24.com", "navent.com"],
                "filters": filters.dict(),
                "max_pages": max_pages
            }
            
    except Exception as e:
        app_logger.error(f"Error starting scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start/{website}")
async def start_website_scraping(
    website: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    property_type: Optional[PropertyType] = None,
    operation_type: Optional[OperationType] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    currency: Optional[Currency] = None,
    min_bedrooms: Optional[int] = None,
    max_bedrooms: Optional[int] = None,
    min_bathrooms: Optional[int] = None,
    max_bathrooms: Optional[int] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    neighborhood: Optional[str] = None,
    max_pages: Optional[int] = None
):
    """Start scraping for a specific website."""
    try:
        supported_websites = ['zonaprop.com.ar', 'argenprop.com', 'mercadolibre.com.ar', 'remax.com.ar', 'properati.com.ar', 'inmuebles24.com', 'navent.com']
        if website not in supported_websites:
            raise HTTPException(status_code=400, detail=f"Unsupported website: {website}. Supported: {supported_websites}")
        
        # Create filters
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
        
        scraping_service = ScrapingService(db)
        
        # Add background task
        background_tasks.add_task(
            scraping_service.scrape_website,
            website,
            filters,
            max_pages
        )
        
        return {
            "message": f"Scraping started for {website}",
            "website": website,
            "filters": filters.dict(),
            "max_pages": max_pages
        }
        
    except Exception as e:
        app_logger.error(f"Error starting scraping for {website}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_scraping_sessions(
    website: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get scraping sessions."""
    try:
        scraping_service = ScrapingService(db)
        sessions = scraping_service.get_scraping_sessions(website, limit)
        
        result = []
        for session in sessions:
            result.append({
                "id": session.id,
                "website": session.website,
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "finished_at": session.finished_at.isoformat() if session.finished_at else None,
                "status": session.status,
                "total_pages": session.total_pages,
                "processed_pages": session.processed_pages,
                "total_properties": session.total_properties,
                "new_properties": session.new_properties,
                "updated_properties": session.updated_properties,
                "errors": session.errors,
                "filters": session.filters
            })
        
        return {
            "sessions": result,
            "count": len(result),
            "website_filter": website
        }
        
    except Exception as e:
        app_logger.error(f"Error getting scraping sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_scraping_session(session_id: int, db: Session = Depends(get_db)):
    """Get a specific scraping session."""
    try:
        scraping_service = ScrapingService(db)
        session = scraping_service.db.query(ScrapingSession).filter(
            ScrapingSession.id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Scraping session not found")
        
        return {
            "id": session.id,
            "website": session.website,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "finished_at": session.finished_at.isoformat() if session.finished_at else None,
            "status": session.status,
            "total_pages": session.total_pages,
            "processed_pages": session.processed_pages,
            "total_properties": session.total_properties,
            "new_properties": session.new_properties,
            "updated_properties": session.updated_properties,
            "errors": session.errors,
            "filters": session.filters,
            "error_log": session.error_log
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error getting scraping session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_scraping_status(db: Session = Depends(get_db)):
    """Get current scraping status."""
    try:
        scraping_service = ScrapingService(db)
        stats = scraping_service.get_scraping_statistics()
        
        # Get recent sessions
        recent_sessions = scraping_service.get_scraping_sessions(limit=10)
        
        sessions_data = []
        for session in recent_sessions:
            sessions_data.append({
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
            "statistics": stats,
            "recent_sessions": sessions_data
        }
        
    except Exception as e:
        app_logger.error(f"Error getting scraping status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/websites")
async def get_supported_websites():
    """Get list of supported websites."""
    return {
        "websites": [
            {
                "name": "ZonaProp",
                "url": "zonaprop.com.ar",
                "description": "Leading real estate portal in Argentina"
            },
            {
                "name": "ArgenProp",
                "url": "argenprop.com",
                "description": "Popular real estate search platform"
            },
            {
                "name": "MercadoLibre",
                "url": "mercadolibre.com.ar",
                "description": "Argentina's largest e-commerce platform with real estate section"
            },
            {
                "name": "RE/MAX",
                "url": "remax.com.ar",
                "description": "International real estate franchise with strong presence in Argentina"
            },
            {
                "name": "Properati",
                "url": "properati.com.ar",
                "description": "Modern real estate platform with advanced search features"
            },
            {
                "name": "Inmuebles24",
                "url": "inmuebles24.com",
                "description": "Popular real estate portal across Latin America"
            },
            {
                "name": "Navent",
                "url": "navent.com",
                "description": "Technology platform powering multiple real estate portals"
            }
        ]
    }