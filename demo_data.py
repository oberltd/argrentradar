#!/usr/bin/env python3
"""
Demo data generator for Argentina Real Estate Parser
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from datetime import datetime, timedelta
import random

from src.database import db_manager
from src.services import PropertyService
from src.models import (
    Property, PropertyType, OperationType, Currency, PropertyStatus,
    Location, PropertyFeatures, PropertyPrice, PropertyContact, PropertyImages
)
from src.utils import app_logger


def create_demo_properties():
    """Create demo properties for testing."""
    
    demo_properties = [
        {
            "external_id": "demo_001",
            "source_url": "https://www.zonaprop.com.ar/propiedades/demo-001",
            "source_website": "zonaprop.com.ar",
            "title": "Departamento 2 ambientes en Palermo",
            "description": "Hermoso departamento de 2 ambientes en el corazón de Palermo. Totalmente renovado, con cocina integrada y balcón. Excelente ubicación cerca del transporte público.",
            "property_type": PropertyType.APARTMENT,
            "operation_type": OperationType.SALE,
            "location": Location(
                province="Buenos Aires",
                city="Buenos Aires",
                neighborhood="Palermo",
                address="Av. Santa Fe 3456"
            ),
            "features": PropertyFeatures(
                bedrooms=2,
                bathrooms=1,
                total_area=65.0,
                covered_area=60.0,
                parking_spaces=1,
                amenities=["balcón", "cocina integrada", "luminoso"]
            ),
            "price": PropertyPrice(
                amount=180000,
                currency=Currency.USD
            ),
            "contact": PropertyContact(
                agency_name="Inmobiliaria Palermo",
                phone="+54 11 4567-8901"
            ),
            "images": PropertyImages(
                main_image="https://example.com/images/demo_001_main.jpg",
                gallery=["https://example.com/images/demo_001_1.jpg", "https://example.com/images/demo_001_2.jpg"]
            )
        },
        {
            "external_id": "demo_002", 
            "source_url": "https://www.argenprop.com/propiedades/demo-002",
            "source_website": "argenprop.com",
            "title": "Casa 3 dormitorios en San Isidro",
            "description": "Amplia casa familiar en zona residencial de San Isidro. 3 dormitorios, 2 baños, jardín y quincho. Ideal para familias.",
            "property_type": PropertyType.HOUSE,
            "operation_type": OperationType.SALE,
            "location": Location(
                province="Buenos Aires",
                city="San Isidro",
                neighborhood="Centro",
                address="Belgrano 1234"
            ),
            "features": PropertyFeatures(
                bedrooms=3,
                bathrooms=2,
                total_area=180.0,
                covered_area=120.0,
                parking_spaces=2,
                amenities=["jardín", "quincho", "parrilla", "garage"]
            ),
            "price": PropertyPrice(
                amount=320000,
                currency=Currency.USD
            ),
            "contact": PropertyContact(
                agency_name="RE/MAX San Isidro",
                phone="+54 11 4747-1234"
            ),
            "images": PropertyImages(
                main_image="https://example.com/images/demo_002_main.jpg",
                gallery=["https://example.com/images/demo_002_1.jpg", "https://example.com/images/demo_002_2.jpg"]
            )
        },
        {
            "external_id": "demo_003",
            "source_url": "https://www.zonaprop.com.ar/propiedades/demo-003", 
            "source_website": "zonaprop.com.ar",
            "title": "Departamento 1 ambiente en Recoleta - Alquiler",
            "description": "Moderno monoambiente en Recoleta, totalmente amoblado. Ideal para profesionales. Incluye todos los servicios.",
            "property_type": PropertyType.APARTMENT,
            "operation_type": OperationType.RENT,
            "location": Location(
                province="Buenos Aires",
                city="Buenos Aires", 
                neighborhood="Recoleta",
                address="Av. Callao 987"
            ),
            "features": PropertyFeatures(
                bedrooms=1,
                bathrooms=1,
                total_area=35.0,
                covered_area=35.0,
                amenities=["amoblado", "servicios incluidos", "portero 24hs"]
            ),
            "price": PropertyPrice(
                amount=85000,
                currency=Currency.ARS,
                expenses=25000,
                expenses_currency=Currency.ARS
            ),
            "contact": PropertyContact(
                agency_name="Recoleta Properties",
                phone="+54 11 4812-3456"
            ),
            "images": PropertyImages(
                main_image="https://example.com/images/demo_003_main.jpg",
                gallery=["https://example.com/images/demo_003_1.jpg"]
            )
        },
        {
            "external_id": "demo_004",
            "source_url": "https://www.argenprop.com/propiedades/demo-004",
            "source_website": "argenprop.com", 
            "title": "Local comercial en Microcentro",
            "description": "Excelente local comercial en pleno microcentro porteño. Gran vidriera y excelente ubicación para cualquier tipo de negocio.",
            "property_type": PropertyType.COMMERCIAL,
            "operation_type": OperationType.RENT,
            "location": Location(
                province="Buenos Aires",
                city="Buenos Aires",
                neighborhood="Microcentro",
                address="Florida 456"
            ),
            "features": PropertyFeatures(
                total_area=80.0,
                covered_area=80.0,
                amenities=["vidriera", "aire acondicionado", "baño"]
            ),
            "price": PropertyPrice(
                amount=150000,
                currency=Currency.ARS,
                expenses=35000,
                expenses_currency=Currency.ARS
            ),
            "contact": PropertyContact(
                agency_name="Comercial Center",
                phone="+54 11 4325-6789"
            ),
            "images": PropertyImages(
                main_image="https://example.com/images/demo_004_main.jpg",
                gallery=["https://example.com/images/demo_004_1.jpg", "https://example.com/images/demo_004_2.jpg"]
            )
        },
        {
            "external_id": "demo_005",
            "source_url": "https://www.zonaprop.com.ar/propiedades/demo-005",
            "source_website": "zonaprop.com.ar",
            "title": "Casa quinta en Tigre",
            "description": "Hermosa casa quinta en Tigre con acceso al río. Ideal para descanso y recreación. Amplio parque y muelle privado.",
            "property_type": PropertyType.HOUSE,
            "operation_type": OperationType.SALE,
            "location": Location(
                province="Buenos Aires",
                city="Tigre",
                neighborhood="Delta",
                address="Canal San Antonio 123"
            ),
            "features": PropertyFeatures(
                bedrooms=4,
                bathrooms=3,
                total_area=500.0,
                covered_area=200.0,
                parking_spaces=3,
                amenities=["muelle privado", "parque", "quincho", "piscina"]
            ),
            "price": PropertyPrice(
                amount=450000,
                currency=Currency.USD
            ),
            "contact": PropertyContact(
                agency_name="Delta Properties",
                phone="+54 11 4749-8888"
            ),
            "images": PropertyImages(
                main_image="https://example.com/images/demo_005_main.jpg",
                gallery=["https://example.com/images/demo_005_1.jpg", "https://example.com/images/demo_005_2.jpg", "https://example.com/images/demo_005_3.jpg"]
            )
        }
    ]
    
    with db_manager.get_session() as db:
        property_service = PropertyService(db)
        
        for prop_data in demo_properties:
            # Add some randomness to timestamps
            days_ago = random.randint(1, 30)
            hours_ago = random.randint(1, 23)
            
            first_seen = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)
            last_updated = first_seen + timedelta(hours=random.randint(1, 48))
            
            property_obj = Property(
                first_seen=first_seen,
                last_updated=last_updated,
                last_checked=datetime.utcnow(),
                **prop_data
            )
            
            try:
                created_property = property_service.create_property(property_obj)
                app_logger.info(f"Created demo property: {created_property.title}")
            except Exception as e:
                app_logger.error(f"Error creating demo property: {e}")


if __name__ == "__main__":
    app_logger.info("Creating demo properties...")
    create_demo_properties()
    app_logger.info("Demo properties created successfully!")