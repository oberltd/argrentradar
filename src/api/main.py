from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from ..database import get_db, init_database
from ..models import PropertySearchFilters
from ..services import PropertyService, ScrapingService
from ..utils import app_logger, settings
from .routers import properties, scraping, statistics

# Initialize database
init_database()

# Create FastAPI app
app = FastAPI(
    title="Argentina Real Estate Parser",
    description="API for parsing and managing real estate data from Argentine websites",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(properties.router, prefix="/api/v1/properties", tags=["properties"])
app.include_router(scraping.router, prefix="/api/v1/scraping", tags=["scraping"])
app.include_router(statistics.router, prefix="/api/v1/statistics", tags=["statistics"])

# Setup templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)
templates = Jinja2Templates(directory=templates_dir)

# Setup static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    """Main dashboard page."""
    property_service = PropertyService(db)
    scraping_service = ScrapingService(db)
    
    # Get basic statistics
    property_stats = property_service.get_property_statistics()
    scraping_stats = scraping_service.get_scraping_statistics()
    
    # Get recent properties
    recent_properties = property_service.get_recent_properties(hours=24, limit=10)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "property_stats": property_stats,
        "scraping_stats": scraping_stats,
        "recent_properties": recent_properties
    })


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Argentina Real Estate Parser",
        "version": "1.0.0"
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    app_logger.info("Starting Argentina Real Estate Parser API")
    app_logger.info(f"API running on {settings.api_host}:{settings.api_port}")
    app_logger.info(f"Database URL: {settings.database_url}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    app_logger.info("Shutting down Argentina Real Estate Parser API")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
        log_level=settings.log_level.lower()
    )