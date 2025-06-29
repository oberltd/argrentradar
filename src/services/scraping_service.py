from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..parsers import (
    ZonaPropParser, ArgenPropParser, MercadoLibreParser, 
    RemaxParser, ProperatiParser, Inmuebles24Parser, NaventParser
)
from ..database.models import ScrapingSession
from ..models import PropertySearchFilters
from .property_service import PropertyService
from ..utils import app_logger, settings


class ScrapingService:
    """Service for managing scraping operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.property_service = PropertyService(db)
        self.parsers = {
            'zonaprop.com.ar': ZonaPropParser(),
            'argenprop.com': ArgenPropParser(),
            'mercadolibre.com.ar': MercadoLibreParser(),
            'remax.com.ar': RemaxParser(),
            'properati.com.ar': ProperatiParser(),
            'inmuebles24.com': Inmuebles24Parser(),
            'navent.com': NaventParser(),
        }
        
    def start_scraping_session(self, website: str, filters: PropertySearchFilters) -> ScrapingSession:
        """Start a new scraping session."""
        try:
            session = ScrapingSession(
                website=website,
                started_at=datetime.utcnow(),
                status='running',
                filters=filters.dict() if filters else {}
            )
            
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            app_logger.info(f"Started scraping session {session.id} for {website}")
            return session
            
        except Exception as e:
            app_logger.error(f"Error starting scraping session: {e}")
            raise
            
    def finish_scraping_session(self, session_id: int, status: str = 'completed', error_log: str = None):
        """Finish a scraping session."""
        try:
            session = self.db.query(ScrapingSession).filter(ScrapingSession.id == session_id).first()
            if session:
                session.finished_at = datetime.utcnow()
                session.status = status
                if error_log:
                    session.error_log = error_log
                    
                self.db.commit()
                app_logger.info(f"Finished scraping session {session_id} with status: {status}")
                
        except Exception as e:
            app_logger.error(f"Error finishing scraping session: {e}")
            
    def update_scraping_progress(self, session_id: int, processed_pages: int = None, 
                                total_properties: int = None, new_properties: int = None,
                                updated_properties: int = None, errors: int = None):
        """Update scraping session progress."""
        try:
            session = self.db.query(ScrapingSession).filter(ScrapingSession.id == session_id).first()
            if session:
                if processed_pages is not None:
                    session.processed_pages = processed_pages
                if total_properties is not None:
                    session.total_properties = total_properties
                if new_properties is not None:
                    session.new_properties = new_properties
                if updated_properties is not None:
                    session.updated_properties = updated_properties
                if errors is not None:
                    session.errors = errors
                    
                self.db.commit()
                
        except Exception as e:
            app_logger.error(f"Error updating scraping progress: {e}")
            
    def scrape_website(self, website: str, filters: PropertySearchFilters = None, 
                      max_pages: Optional[int] = None) -> Dict[str, Any]:
        """Scrape a specific website."""
        if website not in self.parsers:
            raise ValueError(f"Parser not available for website: {website}")
            
        parser = self.parsers[website]
        
        # Start scraping session
        session = self.start_scraping_session(website, filters)
        
        try:
            # Use default filters if none provided
            if not filters:
                filters = PropertySearchFilters()
                
            app_logger.info(f"Starting scraping for {website} with filters: {filters.dict()}")
            
            # Get total pages
            search_url = parser.get_search_url(filters)
            total_pages = parser.get_total_pages(search_url)
            
            if max_pages:
                total_pages = min(total_pages, max_pages)
                
            session.total_pages = total_pages
            self.db.commit()
            
            # Scrape properties
            new_count = 0
            updated_count = 0
            error_count = 0
            processed_pages = 0
            
            for property_data in parser.search_properties(filters, max_pages):
                try:
                    # Check if property already exists
                    existing = None
                    if property_data.external_id:
                        existing = self.property_service.get_property_by_external_id(
                            property_data.external_id, website
                        )
                    
                    if not existing:
                        existing = self.property_service.get_property_by_url(property_data.source_url)
                    
                    if existing:
                        # Update existing property
                        # Here you would implement update logic
                        updated_count += 1
                        app_logger.debug(f"Updated existing property: {existing.id}")
                    else:
                        # Create new property
                        self.property_service.create_property(property_data)
                        new_count += 1
                        app_logger.debug(f"Created new property: {property_data.title}")
                        
                except Exception as e:
                    error_count += 1
                    app_logger.error(f"Error processing property: {e}")
                    
                # Update progress periodically
                if (new_count + updated_count + error_count) % 10 == 0:
                    self.update_scraping_progress(
                        session.id,
                        total_properties=new_count + updated_count,
                        new_properties=new_count,
                        updated_properties=updated_count,
                        errors=error_count
                    )
                    
            # Final update
            self.update_scraping_progress(
                session.id,
                processed_pages=total_pages,
                total_properties=new_count + updated_count,
                new_properties=new_count,
                updated_properties=updated_count,
                errors=error_count
            )
            
            self.finish_scraping_session(session.id, 'completed')
            
            result = {
                'session_id': session.id,
                'website': website,
                'total_pages': total_pages,
                'new_properties': new_count,
                'updated_properties': updated_count,
                'errors': error_count,
                'status': 'completed'
            }
            
            app_logger.info(f"Scraping completed for {website}: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Scraping failed for {website}: {str(e)}"
            app_logger.error(error_msg)
            self.finish_scraping_session(session.id, 'failed', error_msg)
            
            return {
                'session_id': session.id,
                'website': website,
                'status': 'failed',
                'error': error_msg
            }
            
    def scrape_all_websites(self, filters: PropertySearchFilters = None, 
                           max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """Scrape all configured websites."""
        results = []
        
        for website in self.parsers.keys():
            try:
                result = self.scrape_website(website, filters, max_pages)
                results.append(result)
            except Exception as e:
                app_logger.error(f"Error scraping {website}: {e}")
                results.append({
                    'website': website,
                    'status': 'failed',
                    'error': str(e)
                })
                
        return results
        
    async def async_scrape_all_websites(self, filters: PropertySearchFilters = None,
                                       max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """Scrape all websites asynchronously."""
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=len(self.parsers)) as executor:
            tasks = []
            
            for website in self.parsers.keys():
                task = loop.run_in_executor(
                    executor, 
                    self.scrape_website, 
                    website, 
                    filters, 
                    max_pages
                )
                tasks.append(task)
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            processed_results = []
            for i, result in enumerate(results):
                website = list(self.parsers.keys())[i]
                
                if isinstance(result, Exception):
                    processed_results.append({
                        'website': website,
                        'status': 'failed',
                        'error': str(result)
                    })
                else:
                    processed_results.append(result)
                    
            return processed_results
            
    def get_scraping_sessions(self, website: str = None, limit: int = 50) -> List[ScrapingSession]:
        """Get scraping sessions."""
        query = self.db.query(ScrapingSession)
        
        if website:
            query = query.filter(ScrapingSession.website == website)
            
        return query.order_by(ScrapingSession.started_at.desc()).limit(limit).all()
        
    def get_scraping_statistics(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        try:
            total_sessions = self.db.query(ScrapingSession).count()
            completed_sessions = self.db.query(ScrapingSession).filter(
                ScrapingSession.status == 'completed'
            ).count()
            failed_sessions = self.db.query(ScrapingSession).filter(
                ScrapingSession.status == 'failed'
            ).count()
            running_sessions = self.db.query(ScrapingSession).filter(
                ScrapingSession.status == 'running'
            ).count()
            
            # Recent sessions (last 24 hours)
            last_24h = datetime.utcnow() - timedelta(hours=24)
            recent_sessions = self.db.query(ScrapingSession).filter(
                ScrapingSession.started_at >= last_24h
            ).count()
            
            # Statistics by website
            by_website = {}
            for website in self.parsers.keys():
                count = self.db.query(ScrapingSession).filter(
                    ScrapingSession.website == website
                ).count()
                by_website[website] = count
                
            return {
                'total_sessions': total_sessions,
                'completed_sessions': completed_sessions,
                'failed_sessions': failed_sessions,
                'running_sessions': running_sessions,
                'recent_sessions_24h': recent_sessions,
                'by_website': by_website
            }
            
        except Exception as e:
            app_logger.error(f"Error getting scraping statistics: {e}")
            return {}