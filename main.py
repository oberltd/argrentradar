#!/usr/bin/env python3
"""
Argentina Real Estate Parser
Main entry point for the application
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils import app_logger, settings
from src.database import init_database


def run_api():
    """Run the FastAPI web server."""
    import uvicorn
    
    app_logger.info("Starting Argentina Real Estate Parser API")
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,  # Disable reload for now
        log_level=settings.log_level.lower()
    )


def run_scraper():
    """Run the scraper manually."""
    from src.database import db_manager
    from src.services import ScrapingService
    from src.models import PropertySearchFilters
    
    app_logger.info("Starting manual scraping")
    
    with db_manager.get_session() as db:
        scraping_service = ScrapingService(db)
        
        # Create basic filters
        filters = PropertySearchFilters()
        
        # Scrape all websites
        results = scraping_service.scrape_all_websites(filters, max_pages=5)
        
        for result in results:
            app_logger.info(f"Scraping result: {result}")


def init_db():
    """Initialize the database."""
    app_logger.info("Initializing database")
    init_database()
    app_logger.info("Database initialized successfully")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Argentina Real Estate Parser")
    parser.add_argument(
        "command",
        choices=["api", "scrape", "init-db"],
        help="Command to run"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        settings.api_debug = True
        settings.log_level = "DEBUG"
    
    try:
        if args.command == "api":
            run_api()
        elif args.command == "scrape":
            run_scraper()
        elif args.command == "init-db":
            init_db()
    except KeyboardInterrupt:
        app_logger.info("Application interrupted by user")
    except Exception as e:
        app_logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()