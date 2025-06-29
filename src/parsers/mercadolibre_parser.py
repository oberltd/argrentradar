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


class MercadoLibreParser(BaseParser):
    """Parser for MercadoLibre.com.ar real estate section"""
    
    def __init__(self):
        super().__init__("https://inmuebles.mercadolibre.com.ar", "MercadoLibre")
        
    def get_search_url(self, filters: PropertySearchFilters) -> str:
        """Build MercadoLibre search URL based on filters."""
        params = {}
        
        # Operation type mapping
        if filters.operation_type:
            if filters.operation_type == OperationType.SALE:
                params['category'] = 'MLA1459'  # Venta
            elif filters.operation_type == OperationType.RENT:
                params['category'] = 'MLA1472'  # Alquiler
        
        # Property type mapping
        if filters.property_type:
            type_mapping = {
                PropertyType.APARTMENT: 'MLA50547',  # Departamentos
                PropertyType.HOUSE: 'MLA50546',      # Casas
                PropertyType.COMMERCIAL: 'MLA50548', # Locales comerciales
                PropertyType.OFFICE: 'MLA50549',     # Oficinas
                PropertyType.LAND: 'MLA50550'        # Terrenos y lotes
            }
            if filters.property_type in type_mapping:
                params['category'] = type_mapping[filters.property_type]
        
        # Location
        if filters.city:
            params['state'] = 'TUxBUENBUGw3M2E1'  # Capital Federal
            params['city'] = filters.city
        
        # Price range
        if filters.min_price:
            params['price'] = f"{filters.min_price}-*"
        if filters.max_price:
            if filters.min_price:
                params['price'] = f"{filters.min_price}-{filters.max_price}"
            else:
                params['price'] = f"*-{filters.max_price}"
        
        # Currency
        if filters.currency:
            if filters.currency == Currency.USD:
                params['currency'] = 'USD'
            elif filters.currency == Currency.ARS:
                params['currency'] = 'ARS'
        
        # Bedrooms
        if filters.bedrooms:
            params['bedrooms'] = str(filters.bedrooms)
        
        # Bathrooms
        if filters.bathrooms:
            params['bathrooms'] = str(filters.bathrooms)
        
        # Area
        if filters.min_area:
            params['covered_area'] = f"{filters.min_area}-*"
        if filters.max_area:
            if filters.min_area:
                params['covered_area'] = f"{filters.min_area}-{filters.max_area}"
            else:
                params['covered_area'] = f"*-{filters.max_area}"
        
        base_url = f"{self.base_url}/listado"
        if params:
            return f"{base_url}?{urlencode(params)}"
        return base_url
    
    def parse_listing_page(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Parse MercadoLibre listing page and extract property links."""
        properties = []
        
        try:
            soup = self._get_soup(html)
            
            # Find property cards
            property_cards = soup.find_all('div', class_='ui-search-result__wrapper')
            
            for card in property_cards:
                try:
                    # Extract basic info
                    link_elem = card.find('a', class_='ui-search-link')
                    if not link_elem:
                        continue
                    
                    property_url = link_elem.get('href', '')
                    if not property_url.startswith('http'):
                        property_url = f"https://inmuebles.mercadolibre.com.ar{property_url}"
                    
                    # Title
                    title_elem = card.find('h2', class_='ui-search-item__title')
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    # Price
                    price_elem = card.find('span', class_='andes-money-amount__fraction')
                    price_text = price_elem.get_text(strip=True) if price_elem else ""
                    
                    # Currency
                    currency_elem = card.find('span', class_='andes-money-amount__currency-symbol')
                    currency_text = currency_elem.get_text(strip=True) if currency_elem else ""
                    
                    # Location
                    location_elem = card.find('span', class_='ui-search-item__group__element')
                    location = location_elem.get_text(strip=True) if location_elem else ""
                    
                    # Image
                    img_elem = card.find('img', class_='ui-search-result-image__element')
                    image_url = img_elem.get('src', '') if img_elem else ""
                    
                    properties.append({
                        'url': property_url,
                        'title': title,
                        'price_text': price_text,
                        'currency_text': currency_text,
                        'location': location,
                        'image_url': image_url,
                        'source': 'MercadoLibre'
                    })
                    
                except Exception as e:
                    app_logger.warning(f"Error parsing property card: {e}")
                    continue
            
            app_logger.info(f"Found {len(properties)} properties on MercadoLibre listing page")
            
        except Exception as e:
            app_logger.error(f"Error parsing MercadoLibre listing page: {e}")
        
        return properties
    
    def parse_property_detail(self, html: str, url: str) -> Optional[Property]:
        """Parse individual MercadoLibre property page."""
        try:
            soup = self._get_soup(html)
            
            # Extract property ID from URL
            property_id = self._extract_property_id(url)
            
            # Title
            title_elem = soup.find('h1', class_='ui-pdp-title')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Price
            price_elem = soup.find('span', class_='andes-money-amount__fraction')
            price_text = price_elem.get_text(strip=True) if price_elem else ""
            price_amount = self._parse_price(price_text)
            
            # Currency
            currency_elem = soup.find('span', class_='andes-money-amount__currency-symbol')
            currency_text = currency_elem.get_text(strip=True) if currency_elem else ""
            currency = self._parse_currency(currency_text)
            
            # Description
            description_elem = soup.find('div', class_='ui-pdp-description__content')
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            # Location
            location_elem = soup.find('p', class_='ui-pdp-color--BLACK')
            location_text = location_elem.get_text(strip=True) if location_elem else ""
            location = self._parse_location(location_text)
            
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
                source_website="mercadolibre.com.ar",
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
            app_logger.error(f"Error parsing MercadoLibre property detail: {e}")
            return None
    
    def get_search_url(self, filters: PropertySearchFilters) -> str:
        """Build search URL based on filters"""
        base_url = "https://inmuebles.mercadolibre.com.ar"
        
        # Build search parameters
        params = {}
        
        # Property type mapping
        if filters.property_type:
            type_mapping = {
                'apartment': 'departamento',
                'house': 'casa',
                'commercial': 'local',
                'office': 'oficina',
                'land': 'terreno'
            }
            params['ITEM_CONDITION'] = type_mapping.get(filters.property_type.value, 'departamento')
        
        # Operation type
        if filters.operation_type:
            if filters.operation_type.value == 'sale':
                params['operation'] = 'sale'
            else:
                params['operation'] = 'rent'
        
        # Location
        if filters.city:
            params['state'] = 'TUxBUENBUGw3M2E1'  # Buenos Aires state ID
            if 'buenos aires' in filters.city.lower():
                params['city'] = 'TUxBQ0NBUGZlZG1sYQ'  # Buenos Aires city ID
        
        # Price range
        if filters.min_price:
            params['price'] = f"{filters.min_price}-*"
        if filters.max_price:
            if filters.min_price:
                params['price'] = f"{filters.min_price}-{filters.max_price}"
            else:
                params['price'] = f"*-{filters.max_price}"
        
        # Currency
        if filters.currency:
            params['currency'] = filters.currency.value
        
        # Build URL
        if params:
            from urllib.parse import urlencode
            return f"{base_url}/_NoIndex_True?{urlencode(params)}"
        else:
            return f"{base_url}/_NoIndex_True"
    
    def get_total_pages(self, search_url: str) -> int:
        """Get total number of pages for a search"""
        try:
            response = self.get_page(search_url)
            if not response:
                return 1
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for pagination
            pagination = soup.find('nav', class_='andes-pagination')
            if pagination:
                page_links = pagination.find_all('a', class_='andes-pagination__link')
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
            
            # Alternative: look for "Siguiente" button and estimate
            next_button = soup.find('a', string=re.compile(r'Siguiente|Next'))
            if next_button:
                return 10  # Default estimate
            
            return 1
            
        except Exception as e:
            app_logger.error(f"Error getting total pages: {e}")
            return 1
    
    def _extract_property_id(self, url: str) -> str:
        """Extract property ID from MercadoLibre URL."""
        # MercadoLibre URLs format: https://inmuebles.mercadolibre.com.ar/MLA-123456789-title
        match = re.search(r'MLA-(\d+)', url)
        return match.group(1) if match else url.split('/')[-1]
    
    def _parse_features(self, soup) -> Optional[PropertyFeatures]:
        """Parse property features from MercadoLibre page."""
        try:
            features = PropertyFeatures()
            
            # Look for attributes section
            attrs_section = soup.find('section', class_='ui-vpp-highlighted-specs')
            if attrs_section:
                specs = attrs_section.find_all('div', class_='ui-vpp-highlighted-specs__attribute')
                
                for spec in specs:
                    label_elem = spec.find('strong')
                    value_elem = spec.find('span')
                    
                    if not label_elem or not value_elem:
                        continue
                    
                    label = label_elem.get_text(strip=True).lower()
                    value = value_elem.get_text(strip=True)
                    
                    if 'dormitorio' in label or 'ambiente' in label:
                        features.bedrooms = self._parse_number(value)
                    elif 'baño' in label:
                        features.bathrooms = self._parse_number(value)
                    elif 'cochera' in label or 'garage' in label:
                        features.parking_spaces = self._parse_number(value)
                    elif 'superficie total' in label:
                        features.total_area = self._parse_area(value)
                    elif 'superficie cubierta' in label:
                        features.covered_area = self._parse_area(value)
                    elif 'piso' in label:
                        features.floor = self._parse_number(value)
                    elif 'antigüedad' in label:
                        features.age = self._parse_number(value)
            
            return features
            
        except Exception as e:
            app_logger.warning(f"Error parsing MercadoLibre features: {e}")
            return None
    
    def _parse_images(self, soup) -> Optional[PropertyImages]:
        """Parse property images from MercadoLibre page."""
        try:
            images = PropertyImages()
            gallery = []
            
            # Main image
            main_img = soup.find('img', class_='ui-pdp-image')
            if main_img:
                images.main_image = main_img.get('src', '')
            
            # Gallery images
            gallery_section = soup.find('div', class_='ui-pdp-gallery')
            if gallery_section:
                img_elements = gallery_section.find_all('img')
                for img in img_elements:
                    img_url = img.get('src', '')
                    if img_url and img_url not in gallery:
                        gallery.append(img_url)
            
            images.gallery = gallery
            return images
            
        except Exception as e:
            app_logger.warning(f"Error parsing MercadoLibre images: {e}")
            return None
    
    def _parse_contact(self, soup) -> Optional[PropertyContact]:
        """Parse contact information from MercadoLibre page."""
        try:
            contact = PropertyContact()
            
            # Look for seller information
            seller_section = soup.find('div', class_='ui-box-component-pdp')
            if seller_section:
                seller_name = seller_section.find('span', class_='ui-pdp-seller__header__title')
                if seller_name:
                    contact.agent_name = seller_name.get_text(strip=True)
            
            return contact
            
        except Exception as e:
            app_logger.warning(f"Error parsing MercadoLibre contact: {e}")
            return None
    
    def _determine_property_type(self, title: str, description: str) -> PropertyType:
        """Determine property type from title and description."""
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ['departamento', 'depto', 'apartment']):
            return PropertyType.APARTMENT
        elif any(word in text for word in ['casa', 'house', 'chalet']):
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