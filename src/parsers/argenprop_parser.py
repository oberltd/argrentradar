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


class ArgenPropParser(BaseParser):
    """Parser for ArgenProp.com"""
    
    def __init__(self):
        super().__init__("https://www.argenprop.com", "ArgenProp")
        
    def get_search_url(self, filters: PropertySearchFilters) -> str:
        """Build ArgenProp search URL based on filters."""
        params = {}
        
        # Operation type mapping
        if filters.operation_type:
            if filters.operation_type == OperationType.SALE:
                params['q'] = 'venta'
            elif filters.operation_type == OperationType.RENT:
                params['q'] = 'alquiler'
                
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
                if 'q' in params:
                    params['q'] += f"-{type_mapping[filters.property_type]}"
                else:
                    params['q'] = type_mapping[filters.property_type]
                    
        # Price range
        if filters.min_price:
            params['precio-desde'] = int(filters.min_price)
        if filters.max_price:
            params['precio-hasta'] = int(filters.max_price)
            
        # Currency
        if filters.currency:
            params['moneda'] = filters.currency.value
            
        # Bedrooms
        if filters.min_bedrooms:
            params['dormitorios-desde'] = filters.min_bedrooms
        if filters.max_bedrooms:
            params['dormitorios-hasta'] = filters.max_bedrooms
            
        # Bathrooms
        if filters.min_bathrooms:
            params['banos-desde'] = filters.min_bathrooms
        if filters.max_bathrooms:
            params['banos-hasta'] = filters.max_bathrooms
            
        # Area
        if filters.min_area:
            params['superficie-desde'] = int(filters.min_area)
        if filters.max_area:
            params['superficie-hasta'] = int(filters.max_area)
            
        # Location
        location_parts = []
        if filters.neighborhood:
            location_parts.append(filters.neighborhood)
        if filters.city:
            location_parts.append(filters.city)
        if filters.province:
            location_parts.append(filters.province)
            
        if location_parts:
            params['localidad'] = '-'.join(location_parts).lower().replace(' ', '-')
            
        base_url = f"{self.base_url}/propiedades"
        if params:
            return f"{base_url}?{urlencode(params)}"
        return base_url
        
    def parse_listing_page(self, url: str) -> List[Dict[str, Any]]:
        """Parse ArgenProp listing page and extract property links."""
        response = self.get_page(url)
        if not response:
            return []
            
        soup = self.parse_html(response.text)
        properties = []
        
        # Find property cards - ArgenProp uses different class names
        property_cards = soup.find_all('div', class_='listing__item')
        
        if not property_cards:
            # Try alternative selectors
            property_cards = soup.find_all('article', class_='card-container')
            
        for card in property_cards:
            try:
                # Extract property URL
                link_elem = card.find('a', class_='card__title-link')
                if not link_elem:
                    link_elem = card.find('a')
                    
                if not link_elem:
                    continue
                    
                property_url = self.build_absolute_url(link_elem.get('href'))
                
                # Extract basic info
                title_elem = card.find('h2', class_='card__title')
                if not title_elem:
                    title_elem = link_elem
                title = self.clean_text(title_elem.get_text()) if title_elem else ""
                
                # Extract price
                price_elem = card.find('p', class_='card__price')
                if not price_elem:
                    price_elem = card.find('span', class_='price')
                price_text = price_elem.get_text() if price_elem else ""
                
                # Extract location
                location_elem = card.find('p', class_='card__location')
                if not location_elem:
                    location_elem = card.find('span', class_='location')
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
        """Parse individual ArgenProp property detail page."""
        response = self.get_page(url)
        if not response:
            return None
            
        soup = self.parse_html(response.text)
        
        try:
            # Extract basic information
            title_elem = soup.find('h1', class_='property-title')
            if not title_elem:
                title_elem = soup.find('h1')
            title = self.clean_text(title_elem.get_text()) if title_elem else "No title"
            
            # Extract description
            description_elem = soup.find('div', class_='property-description')
            if not description_elem:
                description_elem = soup.find('section', class_='description')
            description = self.clean_text(description_elem.get_text()) if description_elem else None
            
            # Extract property type and operation type
            property_type, operation_type = self._extract_types_from_url_and_content(url, soup)
            
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
                source_website="argenprop.com",
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
                    'parser': 'ArgenPropParser'
                }
            )
            
            app_logger.info(f"Successfully parsed property: {title}")
            return property_obj
            
        except Exception as e:
            app_logger.error(f"Error parsing property detail {url}: {e}")
            return None
            
    def get_total_pages(self, search_url: str) -> int:
        """Get total number of pages for ArgenProp search."""
        response = self.get_page(search_url)
        if not response:
            return 1
            
        soup = self.parse_html(response.text)
        
        # Look for pagination
        pagination = soup.find('nav', class_='pagination')
        if not pagination:
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
                
        # Also check for "last page" indicator
        last_page_elem = pagination.find('a', class_='last')
        if last_page_elem:
            href = last_page_elem.get('href', '')
            page_match = re.search(r'pagina-(\d+)', href)
            if page_match:
                max_page = max(max_page, int(page_match.group(1)))
                
        return max_page
        
    def _extract_types_from_url_and_content(self, url: str, soup) -> tuple:
        """Extract property and operation types from URL and content."""
        property_type = PropertyType.APARTMENT  # default
        operation_type = OperationType.SALE  # default
        
        url_lower = url.lower()
        
        # Operation type from URL
        if 'alquiler' in url_lower:
            operation_type = OperationType.RENT
        elif 'venta' in url_lower:
            operation_type = OperationType.SALE
            
        # Property type from URL
        if 'departamento' in url_lower:
            property_type = PropertyType.APARTMENT
        elif 'casa' in url_lower:
            property_type = PropertyType.HOUSE
        elif 'local' in url_lower:
            property_type = PropertyType.COMMERCIAL
        elif 'terreno' in url_lower:
            property_type = PropertyType.LAND
        elif 'oficina' in url_lower:
            property_type = PropertyType.OFFICE
            
        # Also check breadcrumb or page content
        breadcrumb = soup.find('nav', class_='breadcrumb')
        if breadcrumb:
            breadcrumb_text = breadcrumb.get_text().lower()
            
            if 'alquiler' in breadcrumb_text:
                operation_type = OperationType.RENT
            elif 'venta' in breadcrumb_text:
                operation_type = OperationType.SALE
                
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
        
        # Try different location selectors
        location_elem = soup.find('div', class_='property-location')
        if not location_elem:
            location_elem = soup.find('p', class_='location')
        if not location_elem:
            location_elem = soup.find('span', class_='location')
            
        if location_elem:
            location_text = self.clean_text(location_elem.get_text())
            # ArgenProp format: "Neighborhood, City, Province"
            location_parts = [part.strip() for part in location_text.split(',')]
            
            if len(location_parts) >= 1:
                location.neighborhood = location_parts[0]
            if len(location_parts) >= 2:
                location.city = location_parts[1]
            if len(location_parts) >= 3:
                location.province = location_parts[2]
                
        # Try to extract address
        address_elem = soup.find('span', class_='address')
        if not address_elem:
            address_elem = soup.find('div', class_='address')
        if address_elem:
            location.address = self.clean_text(address_elem.get_text())
            
        return location
        
    def _extract_features(self, soup) -> PropertyFeatures:
        """Extract property features."""
        features = PropertyFeatures()
        
        # Find features section
        features_section = soup.find('div', class_='property-features')
        if not features_section:
            features_section = soup.find('section', class_='features')
        if not features_section:
            features_section = soup.find('ul', class_='features-list')
            
        if features_section:
            # Look for specific feature elements
            feature_items = features_section.find_all(['li', 'div', 'span'])
            
            for item in feature_items:
                text = self.clean_text(item.get_text()).lower()
                
                # Extract bedrooms
                if any(word in text for word in ['dormitorio', 'habitación', 'ambiente']):
                    number = self.extract_number(text)
                    if number:
                        features.bedrooms = int(number)
                        
                # Extract bathrooms
                elif 'baño' in text:
                    number = self.extract_number(text)
                    if number:
                        features.bathrooms = int(number)
                        
                # Extract parking
                elif any(word in text for word in ['cochera', 'garage', 'estacionamiento']):
                    number = self.extract_number(text)
                    if number:
                        features.parking_spaces = int(number)
                    else:
                        features.parking_spaces = 1
                        
                # Extract area
                elif 'm²' in text or 'metros' in text:
                    if any(word in text for word in ['total', 'superficie']):
                        number = self.extract_number(text)
                        if number:
                            features.total_area = number
                    elif 'cubierto' in text:
                        number = self.extract_number(text)
                        if number:
                            features.covered_area = number
                            
        # Also try to extract from structured data
        self._extract_features_from_structured_data(soup, features)
        
        return features
        
    def _extract_features_from_structured_data(self, soup, features: PropertyFeatures):
        """Extract features from structured data elements."""
        # Look for data attributes or structured elements
        bedrooms_elem = soup.find(attrs={'data-bedrooms': True})
        if bedrooms_elem:
            try:
                features.bedrooms = int(bedrooms_elem.get('data-bedrooms'))
            except:
                pass
                
        bathrooms_elem = soup.find(attrs={'data-bathrooms': True})
        if bathrooms_elem:
            try:
                features.bathrooms = int(bathrooms_elem.get('data-bathrooms'))
            except:
                pass
                
        area_elem = soup.find(attrs={'data-area': True})
        if area_elem:
            try:
                features.total_area = float(area_elem.get('data-area'))
            except:
                pass
                
    def _extract_price(self, soup) -> PropertyPrice:
        """Extract price information."""
        price = PropertyPrice()
        
        # Try different price selectors
        price_elem = soup.find('div', class_='property-price')
        if not price_elem:
            price_elem = soup.find('span', class_='price')
        if not price_elem:
            price_elem = soup.find('p', class_='price')
            
        if price_elem:
            price_text = self.clean_text(price_elem.get_text())
            
            # Determine currency
            if any(symbol in price_text for symbol in ['USD', 'U$S', 'US$']):
                price.currency = Currency.USD
            else:
                price.currency = Currency.ARS
                
            # Extract amount
            amount = self.extract_number(price_text)
            if amount:
                price.amount = amount
                
        # Extract expenses
        expenses_elem = soup.find('span', class_='expenses')
        if not expenses_elem:
            expenses_elem = soup.find('div', class_='expenses')
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
        contact_section = soup.find('div', class_='contact-info')
        if not contact_section:
            contact_section = soup.find('section', class_='contact')
            
        if contact_section:
            # Agency name
            agency_elem = contact_section.find('h3')
            if not agency_elem:
                agency_elem = contact_section.find('span', class_='agency')
            if agency_elem:
                contact.agency_name = self.clean_text(agency_elem.get_text())
                
            # Agent name
            agent_elem = contact_section.find('p', class_='agent')
            if not agent_elem:
                agent_elem = contact_section.find('span', class_='agent')
            if agent_elem:
                contact.agent_name = self.clean_text(agent_elem.get_text())
                
            # Phone
            phone_elem = contact_section.find('a', href=re.compile(r'tel:'))
            if not phone_elem:
                phone_elem = contact_section.find('span', class_='phone')
            if phone_elem:
                if phone_elem.get('href'):
                    contact.phone = phone_elem.get('href').replace('tel:', '')
                else:
                    contact.phone = self.clean_text(phone_elem.get_text())
                    
        return contact
        
    def _extract_images(self, soup) -> PropertyImages:
        """Extract image URLs."""
        images = PropertyImages()
        
        # Find image gallery
        gallery_section = soup.find('div', class_='property-gallery')
        if not gallery_section:
            gallery_section = soup.find('section', class_='gallery')
        if not gallery_section:
            gallery_section = soup.find('div', class_='images')
            
        if gallery_section:
            img_elements = gallery_section.find_all('img')
            
            image_urls = []
            for img in img_elements:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy')
                if src and 'placeholder' not in src.lower():
                    # Convert to high resolution if possible
                    if 'thumb' in src:
                        src = src.replace('thumb', 'large')
                    elif 'small' in src:
                        src = src.replace('small', 'large')
                    image_urls.append(self.build_absolute_url(src))
                    
            if image_urls:
                images.main_image = image_urls[0]
                images.gallery = image_urls
                
        return images
        
    def _extract_external_id(self, url: str, soup) -> Optional[str]:
        """Extract external property ID."""
        # Try to extract from URL
        id_match = re.search(r'/(\d+)(?:/|$)', url)
        if id_match:
            return id_match.group(1)
            
        # Try to extract from page content
        id_elem = soup.find('span', class_='property-id')
        if not id_elem:
            id_elem = soup.find(attrs={'data-property-id': True})
        if id_elem:
            if id_elem.get('data-property-id'):
                return id_elem.get('data-property-id')
            else:
                id_text = self.clean_text(id_elem.get_text())
                id_match = re.search(r'\d+', id_text)
                if id_match:
                    return id_match.group()
                    
        return None