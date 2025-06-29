import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, urlparse, parse_qs
from datetime import datetime

from .base_parser import BaseParser
from ..models import (
    Property, PropertyType, OperationType, Currency, PropertyStatus,
    Location, PropertyFeatures, PropertyPrice, PropertyContact, 
    PropertyImages, PropertySearchFilters
)
from ..utils import app_logger


class ZonaPropParser(BaseParser):
    """Parser for ZonaProp.com.ar"""
    
    def __init__(self):
        super().__init__("https://www.zonaprop.com.ar", "ZonaProp")
        
    def get_search_url(self, filters: PropertySearchFilters) -> str:
        """Build ZonaProp search URL based on filters."""
        params = {}
        
        # Operation type mapping
        if filters.operation_type:
            if filters.operation_type == OperationType.SALE:
                params['tipo_operacion'] = 'venta'
            elif filters.operation_type == OperationType.RENT:
                params['tipo_operacion'] = 'alquiler'
                
        # Property type mapping
        if filters.property_type:
            type_mapping = {
                PropertyType.APARTMENT: 'departamento',
                PropertyType.HOUSE: 'casa',
                PropertyType.COMMERCIAL: 'local',
                PropertyType.LAND: 'terreno',
                PropertyType.OFFICE: 'oficina'
            }
            if filters.property_type in type_mapping:
                params['tipo_propiedad'] = type_mapping[filters.property_type]
                
        # Price range
        if filters.min_price:
            params['precio_desde'] = int(filters.min_price)
        if filters.max_price:
            params['precio_hasta'] = int(filters.max_price)
            
        # Currency
        if filters.currency:
            params['moneda'] = filters.currency.value.lower()
            
        # Bedrooms
        if filters.min_bedrooms:
            params['dormitorios_desde'] = filters.min_bedrooms
        if filters.max_bedrooms:
            params['dormitorios_hasta'] = filters.max_bedrooms
            
        # Bathrooms
        if filters.min_bathrooms:
            params['banos_desde'] = filters.min_bathrooms
        if filters.max_bathrooms:
            params['banos_hasta'] = filters.max_bathrooms
            
        # Area
        if filters.min_area:
            params['superficie_desde'] = int(filters.min_area)
        if filters.max_area:
            params['superficie_hasta'] = int(filters.max_area)
            
        # Location
        if filters.province:
            params['provincia'] = filters.province
        if filters.city:
            params['localidad'] = filters.city
        if filters.neighborhood:
            params['barrio'] = filters.neighborhood
            
        base_url = f"{self.base_url}/propiedades"
        if params:
            return f"{base_url}?{urlencode(params)}"
        return base_url
        
    def parse_listing_page(self, url: str) -> List[Dict[str, Any]]:
        """Parse ZonaProp listing page and extract property links."""
        response = self.get_page(url)
        if not response:
            return []
            
        soup = self.parse_html(response.text)
        properties = []
        
        # Find property cards
        property_cards = soup.find_all('div', class_='posting-card')
        
        for card in property_cards:
            try:
                # Extract property URL
                link_elem = card.find('a', class_='posting-card-title')
                if not link_elem:
                    continue
                    
                property_url = self.build_absolute_url(link_elem.get('href'))
                
                # Extract basic info for quick filtering
                title = self.clean_text(link_elem.get_text())
                
                # Extract price
                price_elem = card.find('span', class_='posting-card-price')
                price_text = price_elem.get_text() if price_elem else ""
                
                # Extract location
                location_elem = card.find('span', class_='posting-card-location')
                location_text = location_elem.get_text() if location_elem else ""
                
                properties.append({
                    'url': property_url,
                    'title': title,
                    'price_text': price_text,
                    'location_text': location_text
                })
                
            except Exception as e:
                app_logger.warning(f"Error parsing property card: {e}")
                continue
                
        app_logger.info(f"Found {len(properties)} properties on page: {url}")
        return properties
        
    def parse_property_detail(self, url: str) -> Optional[Property]:
        """Parse individual ZonaProp property detail page."""
        response = self.get_page(url)
        if not response:
            return None
            
        soup = self.parse_html(response.text)
        
        try:
            # Extract basic information
            title_elem = soup.find('h1', class_='posting-title')
            title = self.clean_text(title_elem.get_text()) if title_elem else "No title"
            
            # Extract description
            description_elem = soup.find('div', class_='posting-description')
            description = self.clean_text(description_elem.get_text()) if description_elem else None
            
            # Extract property type and operation type
            breadcrumb = soup.find('nav', class_='breadcrumb')
            property_type, operation_type = self._extract_types_from_breadcrumb(breadcrumb)
            
            # Extract location
            location = self._extract_location(soup)
            
            # Extract features
            features = self._extract_features(soup)
            
            # Extract price
            price = self._extract_price(soup)
            
            # Extract contact information
            contact = self._extract_contact(soup)
            
            # Extract images
            images = self._extract_images(soup)
            
            # Extract external ID
            external_id = self._extract_external_id(url, soup)
            
            property_obj = Property(
                external_id=external_id,
                source_url=url,
                source_website="zonaprop.com.ar",
                title=title,
                description=description,
                property_type=property_type,
                operation_type=operation_type,
                location=location,
                features=features,
                price=price,
                contact=contact,
                images=images,
                raw_data={
                    'scraped_at': datetime.utcnow().isoformat(),
                    'parser': 'ZonaPropParser'
                }
            )
            
            app_logger.info(f"Successfully parsed property: {title}")
            return property_obj
            
        except Exception as e:
            app_logger.error(f"Error parsing property detail {url}: {e}")
            return None
            
    def get_total_pages(self, search_url: str) -> int:
        """Get total number of pages for ZonaProp search."""
        response = self.get_page(search_url)
        if not response:
            return 1
            
        soup = self.parse_html(response.text)
        
        # Look for pagination
        pagination = soup.find('div', class_='pagination')
        if not pagination:
            return 1
            
        page_links = pagination.find_all('a')
        max_page = 1
        
        for link in page_links:
            try:
                page_text = link.get_text().strip()
                if page_text.isdigit():
                    max_page = max(max_page, int(page_text))
            except:
                continue
                
        return max_page
        
    def _extract_types_from_breadcrumb(self, breadcrumb) -> tuple:
        """Extract property and operation types from breadcrumb."""
        property_type = PropertyType.APARTMENT  # default
        operation_type = OperationType.SALE  # default
        
        if not breadcrumb:
            return property_type, operation_type
            
        breadcrumb_text = breadcrumb.get_text().lower()
        
        # Operation type
        if 'alquiler' in breadcrumb_text:
            operation_type = OperationType.RENT
        elif 'venta' in breadcrumb_text:
            operation_type = OperationType.SALE
            
        # Property type
        if 'departamento' in breadcrumb_text:
            property_type = PropertyType.APARTMENT
        elif 'casa' in breadcrumb_text:
            property_type = PropertyType.HOUSE
        elif 'local' in breadcrumb_text:
            property_type = PropertyType.COMMERCIAL
        elif 'terreno' in breadcrumb_text:
            property_type = PropertyType.LAND
        elif 'oficina' in breadcrumb_text:
            property_type = PropertyType.OFFICE
            
        return property_type, operation_type
        
    def _extract_location(self, soup) -> Location:
        """Extract location information."""
        location = Location()
        
        # Try to find location in different places
        location_elem = soup.find('div', class_='posting-location')
        if location_elem:
            location_text = self.clean_text(location_elem.get_text())
            location_parts = [part.strip() for part in location_text.split(',')]
            
            if len(location_parts) >= 1:
                location.neighborhood = location_parts[0]
            if len(location_parts) >= 2:
                location.city = location_parts[1]
            if len(location_parts) >= 3:
                location.province = location_parts[2]
                
        # Try to extract address
        address_elem = soup.find('span', class_='posting-address')
        if address_elem:
            location.address = self.clean_text(address_elem.get_text())
            
        return location
        
    def _extract_features(self, soup) -> PropertyFeatures:
        """Extract property features."""
        features = PropertyFeatures()
        
        # Find features section
        features_section = soup.find('div', class_='posting-features')
        if features_section:
            feature_items = features_section.find_all('li')
            
            for item in feature_items:
                text = self.clean_text(item.get_text()).lower()
                
                # Extract bedrooms
                if 'dormitorio' in text or 'habitación' in text:
                    number = self.extract_number(text)
                    if number:
                        features.bedrooms = int(number)
                        
                # Extract bathrooms
                elif 'baño' in text:
                    number = self.extract_number(text)
                    if number:
                        features.bathrooms = int(number)
                        
                # Extract parking
                elif 'cochera' in text or 'garage' in text:
                    number = self.extract_number(text)
                    if number:
                        features.parking_spaces = int(number)
                    else:
                        features.parking_spaces = 1
                        
                # Extract area
                elif 'm²' in text or 'metros' in text:
                    if 'total' in text:
                        number = self.extract_number(text)
                        if number:
                            features.total_area = number
                    elif 'cubierto' in text:
                        number = self.extract_number(text)
                        if number:
                            features.covered_area = number
                            
        return features
        
    def _extract_price(self, soup) -> PropertyPrice:
        """Extract price information."""
        price = PropertyPrice()
        
        price_elem = soup.find('span', class_='posting-price')
        if price_elem:
            price_text = self.clean_text(price_elem.get_text())
            
            # Determine currency
            if 'USD' in price_text or 'U$S' in price_text:
                price.currency = Currency.USD
            else:
                price.currency = Currency.ARS
                
            # Extract amount
            amount = self.extract_number(price_text)
            if amount:
                price.amount = amount
                
        # Extract expenses
        expenses_elem = soup.find('span', class_='posting-expenses')
        if expenses_elem:
            expenses_text = self.clean_text(expenses_elem.get_text())
            expenses_amount = self.extract_number(expenses_text)
            if expenses_amount:
                price.expenses = expenses_amount
                
        return price
        
    def _extract_contact(self, soup) -> PropertyContact:
        """Extract contact information."""
        contact = PropertyContact()
        
        # Find contact section
        contact_section = soup.find('div', class_='posting-contact')
        if contact_section:
            # Agency name
            agency_elem = contact_section.find('span', class_='agency-name')
            if agency_elem:
                contact.agency_name = self.clean_text(agency_elem.get_text())
                
            # Agent name
            agent_elem = contact_section.find('span', class_='agent-name')
            if agent_elem:
                contact.agent_name = self.clean_text(agent_elem.get_text())
                
            # Phone
            phone_elem = contact_section.find('a', href=re.compile(r'tel:'))
            if phone_elem:
                contact.phone = phone_elem.get('href').replace('tel:', '')
                
        return contact
        
    def _extract_images(self, soup) -> PropertyImages:
        """Extract image URLs."""
        images = PropertyImages()
        
        # Find image gallery
        gallery_section = soup.find('div', class_='posting-gallery')
        if gallery_section:
            img_elements = gallery_section.find_all('img')
            
            image_urls = []
            for img in img_elements:
                src = img.get('src') or img.get('data-src')
                if src:
                    # Convert to high resolution if possible
                    if 'thumb' in src:
                        src = src.replace('thumb', 'large')
                    image_urls.append(self.build_absolute_url(src))
                    
            if image_urls:
                images.main_image = image_urls[0]
                images.gallery = image_urls
                
        return images
        
    def _extract_external_id(self, url: str, soup) -> Optional[str]:
        """Extract external property ID."""
        # Try to extract from URL
        url_parts = url.split('/')
        for part in url_parts:
            if part.isdigit():
                return part
                
        # Try to extract from page content
        id_elem = soup.find('span', class_='posting-id')
        if id_elem:
            id_text = self.clean_text(id_elem.get_text())
            id_match = re.search(r'\d+', id_text)
            if id_match:
                return id_match.group()
                
        return None