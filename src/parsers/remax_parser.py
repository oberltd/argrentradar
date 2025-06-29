import re
import json
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, urlparse, parse_qs
from datetime import datetime

from bs4 import BeautifulSoup
from .base_parser import BaseParser
from ..models import (
    Property, PropertyType, OperationType, Currency, PropertyStatus,
    Location, PropertyFeatures, PropertyPrice, PropertyContact, 
    PropertyImages, PropertySearchFilters
)
from ..utils import app_logger


class RemaxParser(BaseParser):
    """Parser for RE/MAX Argentina"""
    
    def __init__(self):
        super().__init__("https://www.remax.com.ar", "RE/MAX")
        
    def get_search_url(self, filters: PropertySearchFilters) -> str:
        """Build RE/MAX search URL based on filters."""
        params = {}
        
        # Operation type mapping
        if filters.operation_type:
            if filters.operation_type == OperationType.SALE:
                params['transactionType'] = 'sale'
            elif filters.operation_type == OperationType.RENT:
                params['transactionType'] = 'rental'
        
        # Property type mapping
        if filters.property_type:
            type_mapping = {
                PropertyType.APARTMENT: 'apartment',
                PropertyType.HOUSE: 'house',
                PropertyType.COMMERCIAL: 'commercial',
                PropertyType.OFFICE: 'office',
                PropertyType.LAND: 'land'
            }
            if filters.property_type in type_mapping:
                params['propertyType'] = type_mapping[filters.property_type]
        
        # Location
        if filters.city:
            params['city'] = filters.city
        if filters.neighborhood:
            params['neighborhood'] = filters.neighborhood
        
        # Price range
        if filters.min_price:
            params['minPrice'] = str(filters.min_price)
        if filters.max_price:
            params['maxPrice'] = str(filters.max_price)
        
        # Currency
        if filters.currency:
            params['currency'] = filters.currency.value
        
        # Bedrooms
        if filters.bedrooms:
            params['bedrooms'] = str(filters.bedrooms)
        
        # Bathrooms
        if filters.bathrooms:
            params['bathrooms'] = str(filters.bathrooms)
        
        # Area
        if filters.min_area:
            params['minArea'] = str(filters.min_area)
        if filters.max_area:
            params['maxArea'] = str(filters.max_area)
        
        base_url = f"{self.base_url}/propiedades"
        if params:
            return f"{base_url}?{urlencode(params)}"
        return base_url
    
    def parse_listing_page(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Parse RE/MAX listing page and extract property links."""
        properties = []
        
        try:
            soup = self._get_soup(html)
            
            # Find property cards
            property_cards = soup.find_all('div', class_='property-card')
            if not property_cards:
                # Alternative selector
                property_cards = soup.find_all('article', class_='listing-item')
            
            for card in property_cards:
                try:
                    # Extract basic info
                    link_elem = card.find('a', href=True)
                    if not link_elem:
                        continue
                    
                    property_url = link_elem.get('href', '')
                    if not property_url.startswith('http'):
                        property_url = f"{self.base_url}{property_url}"
                    
                    # Title
                    title_elem = card.find(['h2', 'h3'], class_=['property-title', 'listing-title'])
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    # Price
                    price_elem = card.find(['span', 'div'], class_=['price', 'property-price'])
                    price_text = price_elem.get_text(strip=True) if price_elem else ""
                    
                    # Location
                    location_elem = card.find(['span', 'div'], class_=['location', 'property-location'])
                    location = location_elem.get_text(strip=True) if location_elem else ""
                    
                    # Image
                    img_elem = card.find('img')
                    image_url = img_elem.get('src', '') if img_elem else ""
                    
                    # Features
                    features_elem = card.find('div', class_='property-features')
                    features_text = features_elem.get_text(strip=True) if features_elem else ""
                    
                    properties.append({
                        'url': property_url,
                        'title': title,
                        'price_text': price_text,
                        'location': location,
                        'image_url': image_url,
                        'features_text': features_text,
                        'source': 'RE/MAX'
                    })
                    
                except Exception as e:
                    app_logger.warning(f"Error parsing RE/MAX property card: {e}")
                    continue
            
            app_logger.info(f"Found {len(properties)} properties on RE/MAX listing page")
            
        except Exception as e:
            app_logger.error(f"Error parsing RE/MAX listing page: {e}")
        
        return properties
    
    def parse_property_detail(self, html: str, url: str) -> Optional[Property]:
        """Parse individual RE/MAX property page."""
        try:
            soup = self._get_soup(html)
            
            # Extract property ID from URL
            property_id = self._extract_property_id(url)
            
            # Title
            title_elem = soup.find('h1', class_=['property-title', 'listing-title'])
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Price
            price_elem = soup.find(['span', 'div'], class_=['price', 'property-price'])
            price_text = price_elem.get_text(strip=True) if price_elem else ""
            price_amount, currency = self._parse_price_and_currency(price_text)
            
            # Description
            description_elem = soup.find('div', class_=['description', 'property-description'])
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            # Location
            location = self._parse_location_from_page(soup)
            
            # Features
            features = self._parse_features(soup)
            
            # Images
            images = self._parse_images(soup)
            
            # Contact info
            contact = self._parse_contact(soup)
            
            # Determine property type and operation type
            property_type = self._determine_property_type(title, description)
            operation_type = self._determine_operation_type(url, title)
            
            # Create Property object
            property_obj = Property(
                external_id=property_id,
                source_url=url,
                source_website="remax.com.ar",
                title=title,
                description=description,
                property_type=property_type,
                operation_type=operation_type,
                status=PropertyStatus.ACTIVE,
                
                # Location
                country="Argentina",
                province=location.province if location else None,
                city=location.city if location else None,
                neighborhood=location.neighborhood if location else None,
                address=location.address if location else None,
                latitude=location.latitude if location else None,
                longitude=location.longitude if location else None,
                
                # Features
                bedrooms=features.bedrooms if features else None,
                bathrooms=features.bathrooms if features else None,
                parking_spaces=features.parking_spaces if features else None,
                total_area=features.total_area if features else None,
                covered_area=features.covered_area if features else None,
                floor=features.floor if features else None,
                age=features.age if features else None,
                amenities=features.amenities if features else None,
                condition=features.condition if features else None,
                
                # Price
                price_amount=price_amount,
                price_currency=currency,
                
                # Contact
                agent_name=contact.agent_name if contact else None,
                agency_name=contact.agency_name if contact else None,
                phone=contact.phone if contact else None,
                email=contact.email if contact else None,
                website=contact.website if contact else None,
                
                # Images
                main_image=images.main_image if images else None,
                gallery=images.gallery if images else None,
                
                # Metadata
                first_seen=datetime.now(),
                last_updated=datetime.now(),
                last_checked=datetime.now()
            )
            
            return property_obj
            
        except Exception as e:
            app_logger.error(f"Error parsing RE/MAX property detail: {e}")
            return None
    
    def get_search_url(self, filters: PropertySearchFilters) -> str:
        """Build search URL based on filters"""
        base_url = "https://www.remax.com.ar/propiedades"
        params = []
        
        if filters.property_type:
            type_mapping = {
                'apartment': 'departamento',
                'house': 'casa',
                'commercial': 'comercial',
                'office': 'oficina',
                'land': 'terreno'
            }
            params.append(f"tipo={type_mapping.get(filters.property_type.value, 'departamento')}")
        
        if filters.operation_type:
            op = 'venta' if filters.operation_type.value == 'sale' else 'alquiler'
            params.append(f"operacion={op}")
        
        if filters.city:
            params.append(f"ubicacion={filters.city.replace(' ', '+')}")
        
        if filters.min_price:
            params.append(f"precio_min={filters.min_price}")
        if filters.max_price:
            params.append(f"precio_max={filters.max_price}")
        
        if params:
            return f"{base_url}?{'&'.join(params)}"
        return base_url
    
    def get_total_pages(self, search_url: str) -> int:
        """Get total number of pages from search results"""
        try:
            response = self.get_page(search_url)
            if not response:
                return 1
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for pagination
            pagination = soup.find('div', class_='pagination')
            if pagination:
                page_links = pagination.find_all('a')
                if page_links:
                    # Get the last page number
                    last_page = 1
                    for link in page_links:
                        try:
                            page_num = int(link.get_text(strip=True))
                            last_page = max(last_page, page_num)
                        except (ValueError, TypeError):
                            continue
                    return last_page
            
            # Alternative: look for page info text
            page_info = soup.find('span', class_='page-info')
            if page_info:
                text = page_info.get_text()
                # Extract from text like "Página 1 de 25"
                match = re.search(r'de\s+(\d+)', text)
                if match:
                    return int(match.group(1))
            
            return 1
            
        except Exception as e:
            app_logger.error(f"Error getting total pages: {e}")
            return 1
    
    def _extract_property_id(self, url: str) -> str:
        """Extract property ID from RE/MAX URL."""
        # RE/MAX URLs format: https://www.remax.com.ar/propiedades/123456
        match = re.search(r'/propiedades/(\d+)', url)
        return match.group(1) if match else url.split('/')[-1]
    
    def _parse_location_from_page(self, soup) -> Optional[Location]:
        """Parse location information from RE/MAX page."""
        try:
            location = Location()
            
            # Look for address
            address_elem = soup.find(['span', 'div'], class_=['address', 'property-address'])
            if address_elem:
                location.address = address_elem.get_text(strip=True)
            
            # Look for neighborhood/city
            location_elem = soup.find(['span', 'div'], class_=['location', 'property-location'])
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                parts = location_text.split(',')
                if len(parts) >= 2:
                    location.neighborhood = parts[0].strip()
                    location.city = parts[1].strip()
                elif len(parts) == 1:
                    location.city = parts[0].strip()
            
            # Look for coordinates in script tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'lat' in script.string and 'lng' in script.string:
                    try:
                        # Try to extract coordinates from JavaScript
                        lat_match = re.search(r'"lat":\s*(-?\d+\.?\d*)', script.string)
                        lng_match = re.search(r'"lng":\s*(-?\d+\.?\d*)', script.string)
                        
                        if lat_match and lng_match:
                            location.latitude = float(lat_match.group(1))
                            location.longitude = float(lng_match.group(1))
                            break
                    except:
                        continue
            
            return location
            
        except Exception as e:
            app_logger.warning(f"Error parsing RE/MAX location: {e}")
            return None
    
    def _parse_features(self, soup) -> Optional[PropertyFeatures]:
        """Parse property features from RE/MAX page."""
        try:
            features = PropertyFeatures()
            
            # Look for features section
            features_section = soup.find('div', class_=['features', 'property-features'])
            if features_section:
                feature_items = features_section.find_all(['li', 'span', 'div'])
                
                for item in feature_items:
                    text = item.get_text(strip=True).lower()
                    
                    if 'dormitorio' in text or 'habitacion' in text:
                        features.bedrooms = self._parse_number(text)
                    elif 'baño' in text:
                        features.bathrooms = self._parse_number(text)
                    elif 'cochera' in text or 'garage' in text:
                        features.parking_spaces = self._parse_number(text)
                    elif 'superficie' in text or 'm²' in text:
                        area = self._parse_area(text)
                        if 'total' in text:
                            features.total_area = area
                        elif 'cubierta' in text:
                            features.covered_area = area
                        else:
                            features.total_area = area
                    elif 'piso' in text:
                        features.floor = self._parse_number(text)
                    elif 'antigüedad' in text or 'años' in text:
                        features.age = self._parse_number(text)
            
            # Look for amenities
            amenities_section = soup.find('div', class_=['amenities', 'property-amenities'])
            if amenities_section:
                amenity_items = amenities_section.find_all(['li', 'span'])
                amenities = [item.get_text(strip=True) for item in amenity_items]
                features.amenities = amenities
            
            return features
            
        except Exception as e:
            app_logger.warning(f"Error parsing RE/MAX features: {e}")
            return None
    
    def _parse_images(self, soup) -> Optional[PropertyImages]:
        """Parse property images from RE/MAX page."""
        try:
            images = PropertyImages()
            gallery = []
            
            # Main image
            main_img = soup.find('img', class_=['main-image', 'hero-image'])
            if main_img:
                images.main_image = main_img.get('src', '')
            
            # Gallery images
            gallery_section = soup.find('div', class_=['gallery', 'image-gallery'])
            if gallery_section:
                img_elements = gallery_section.find_all('img')
                for img in img_elements:
                    img_url = img.get('src', '') or img.get('data-src', '')
                    if img_url and img_url not in gallery:
                        gallery.append(img_url)
            
            images.gallery = gallery
            return images
            
        except Exception as e:
            app_logger.warning(f"Error parsing RE/MAX images: {e}")
            return None
    
    def _parse_contact(self, soup) -> Optional[PropertyContact]:
        """Parse contact information from RE/MAX page."""
        try:
            contact = PropertyContact()
            
            # Look for agent information
            agent_section = soup.find('div', class_=['agent-info', 'contact-info'])
            if agent_section:
                # Agent name
                agent_name = agent_section.find(['h3', 'h4', 'span'], class_=['agent-name', 'contact-name'])
                if agent_name:
                    contact.agent_name = agent_name.get_text(strip=True)
                
                # Agency name (always RE/MAX)
                contact.agency_name = "RE/MAX"
                
                # Phone
                phone_elem = agent_section.find(['a', 'span'], href=re.compile(r'tel:'), class_=['phone', 'contact-phone'])
                if phone_elem:
                    contact.phone = phone_elem.get_text(strip=True)
                
                # Email
                email_elem = agent_section.find('a', href=re.compile(r'mailto:'))
                if email_elem:
                    contact.email = email_elem.get('href', '').replace('mailto:', '')
            
            return contact
            
        except Exception as e:
            app_logger.warning(f"Error parsing RE/MAX contact: {e}")
            return None
    
    def _determine_property_type(self, title: str, description: str) -> PropertyType:
        """Determine property type from title and description."""
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ['departamento', 'depto', 'apartment']):
            return PropertyType.APARTMENT
        elif any(word in text for word in ['casa', 'house', 'chalet', 'ph']):
            return PropertyType.HOUSE
        elif any(word in text for word in ['local', 'comercial', 'negocio']):
            return PropertyType.COMMERCIAL
        elif any(word in text for word in ['oficina', 'office']):
            return PropertyType.OFFICE
        elif any(word in text for word in ['terreno', 'lote', 'land']):
            return PropertyType.LAND
        else:
            return PropertyType.APARTMENT  # Default
    
    def _determine_operation_type(self, url: str, title: str) -> OperationType:
        """Determine operation type from URL and title."""
        text = f"{url} {title}".lower()
        
        if any(word in text for word in ['alquiler', 'rent', 'rental']):
            return OperationType.RENT
        else:
            return OperationType.SALE  # Default