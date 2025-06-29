from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generator
import time
import random
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from urllib.parse import urljoin, urlparse
import asyncio
import aiohttp

from ..models import Property, PropertySearchFilters
from ..utils import app_logger, settings


class BaseParser(ABC):
    """Base class for all property website parsers."""
    
    def __init__(self, base_url: str, name: str):
        self.base_url = base_url
        self.name = name
        self.session = requests.Session()
        self.ua = UserAgent() if settings.user_agent_rotation else None
        self.setup_session()
        
    def setup_session(self):
        """Setup requests session with headers and configuration."""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        if self.ua:
            headers['User-Agent'] = self.ua.random
        else:
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            
        self.session.headers.update(headers)
        
    def get_page(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Get a page with error handling and rate limiting."""
        try:
            # Rate limiting
            time.sleep(settings.scraping_delay + random.uniform(0, 0.5))
            
            # Rotate user agent if enabled
            if self.ua and settings.user_agent_rotation:
                self.session.headers['User-Agent'] = self.ua.random
                
            response = self.session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            
            app_logger.debug(f"Successfully fetched: {url}")
            return response
            
        except requests.exceptions.RequestException as e:
            app_logger.error(f"Error fetching {url}: {str(e)}")
            return None
            
    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content with BeautifulSoup."""
        return BeautifulSoup(html, 'lxml')
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        return ' '.join(text.strip().split())
        
    def extract_number(self, text: str) -> Optional[float]:
        """Extract numeric value from text."""
        if not text:
            return None
            
        import re
        # Remove currency symbols and common separators
        cleaned = re.sub(r'[^\d.,]', '', text)
        cleaned = cleaned.replace(',', '.')
        
        try:
            return float(cleaned)
        except ValueError:
            return None
            
    def build_absolute_url(self, relative_url: str) -> str:
        """Convert relative URL to absolute URL."""
        return urljoin(self.base_url, relative_url)
        
    @abstractmethod
    def get_search_url(self, filters: PropertySearchFilters) -> str:
        """Build search URL based on filters."""
        pass
        
    @abstractmethod
    def parse_listing_page(self, url: str) -> List[Dict[str, Any]]:
        """Parse a listing page and return property data."""
        pass
        
    @abstractmethod
    def parse_property_detail(self, url: str) -> Optional[Property]:
        """Parse individual property detail page."""
        pass
        
    @abstractmethod
    def get_total_pages(self, search_url: str) -> int:
        """Get total number of pages for a search."""
        pass
        
    def search_properties(self, filters: PropertySearchFilters, max_pages: Optional[int] = None) -> Generator[Property, None, None]:
        """Search properties with given filters."""
        search_url = self.get_search_url(filters)
        total_pages = self.get_total_pages(search_url)
        
        if max_pages:
            total_pages = min(total_pages, max_pages)
            
        app_logger.info(f"Starting search on {self.name}, total pages: {total_pages}")
        
        for page in range(1, total_pages + 1):
            app_logger.info(f"Processing page {page}/{total_pages}")
            
            page_url = f"{search_url}&page={page}" if '?' in search_url else f"{search_url}?page={page}"
            property_links = self.parse_listing_page(page_url)
            
            for link_data in property_links:
                property_url = link_data.get('url')
                if property_url:
                    property_data = self.parse_property_detail(property_url)
                    if property_data:
                        yield property_data
                        
    async def async_get_page(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Async version of get_page."""
        try:
            await asyncio.sleep(settings.scraping_delay + random.uniform(0, 0.5))
            
            headers = {}
            if self.ua and settings.user_agent_rotation:
                headers['User-Agent'] = self.ua.random
                
            async with session.get(url, headers=headers, timeout=30) as response:
                response.raise_for_status()
                content = await response.text()
                app_logger.debug(f"Successfully fetched (async): {url}")
                return content
                
        except Exception as e:
            app_logger.error(f"Error fetching (async) {url}: {str(e)}")
            return None
            
    async def async_search_properties(self, filters: PropertySearchFilters, max_pages: Optional[int] = None) -> List[Property]:
        """Async version of search_properties."""
        search_url = self.get_search_url(filters)
        total_pages = self.get_total_pages(search_url)
        
        if max_pages:
            total_pages = min(total_pages, max_pages)
            
        app_logger.info(f"Starting async search on {self.name}, total pages: {total_pages}")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for page in range(1, total_pages + 1):
                page_url = f"{search_url}&page={page}" if '?' in search_url else f"{search_url}?page={page}"
                task = self.async_process_page(session, page_url)
                tasks.append(task)
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            properties = []
            for result in results:
                if isinstance(result, list):
                    properties.extend(result)
                elif isinstance(result, Exception):
                    app_logger.error(f"Error in async processing: {result}")
                    
            return properties
            
    async def async_process_page(self, session: aiohttp.ClientSession, page_url: str) -> List[Property]:
        """Process a single page asynchronously."""
        content = await self.async_get_page(session, page_url)
        if not content:
            return []
            
        # This would need to be implemented in each specific parser
        # For now, return empty list
        return []