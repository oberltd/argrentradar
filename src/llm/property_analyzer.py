from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import re

from .deepseek_client import DeepSeekClient
from ..models import Property, PropertyType, OperationType
from ..utils import app_logger


@dataclass
class PropertyAnalysis:
    """Result of property analysis"""
    confidence_score: float
    extracted_features: Dict[str, Any]
    enhanced_description: str
    classification: Dict[str, str]
    location_details: Dict[str, str]
    summary: str
    recommendations: List[str]


class PropertyAnalyzer:
    """Advanced property analysis using LLM"""
    
    def __init__(self, llm_client: DeepSeekClient = None):
        self.llm = llm_client or DeepSeekClient()
    
    def analyze_property(self, property_obj: Property) -> PropertyAnalysis:
        """Perform comprehensive property analysis"""
        try:
            # Combine all text for analysis
            full_text = f"{property_obj.title}\n{property_obj.description}"
            
            # Extract features using LLM
            extracted_features = self.llm.analyze_property_text(full_text)
            
            # Enhance description
            features_dict = {
                'bedrooms': property_obj.bedrooms,
                'bathrooms': property_obj.bathrooms,
                'total_area': property_obj.total_area,
                'covered_area': property_obj.covered_area,
                'parking_spaces': property_obj.parking_spaces,
                'floor': property_obj.floor,
                'amenities': property_obj.amenities
            }
            
            enhanced_description = self.llm.enhance_property_description(
                property_obj.title,
                property_obj.description,
                features_dict
            )
            
            # Classify property
            property_type = self.llm.classify_property_type(
                property_obj.title,
                property_obj.description
            )
            
            operation_type = self._determine_operation_type(property_obj.source_url, full_text)
            
            classification = {
                'property_type': property_type,
                'operation_type': operation_type
            }
            
            # Extract location details
            location_text = f"{property_obj.city} {property_obj.neighborhood} {property_obj.address}"
            location_details = self.llm.extract_location_details(location_text.strip())
            
            # Generate summary
            property_data = {
                'title': property_obj.title,
                'description': property_obj.description,
                'price': property_obj.price_amount,
                'currency': property_obj.price_currency.value if property_obj.price_currency else None,
                'location': location_text.strip(),
                'features': features_dict
            }
            
            summary = self.llm.generate_property_summary(property_data)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(property_obj, extracted_features)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                property_obj, extracted_features, classification
            )
            
            return PropertyAnalysis(
                confidence_score=confidence_score,
                extracted_features=extracted_features,
                enhanced_description=enhanced_description,
                classification=classification,
                location_details=location_details,
                summary=summary,
                recommendations=recommendations
            )
            
        except Exception as e:
            app_logger.error(f"Error analyzing property: {e}")
            return self._create_fallback_analysis(property_obj)
    
    def _determine_operation_type(self, url: str, text: str) -> str:
        """Determine operation type from URL and text"""
        combined_text = f"{url} {text}".lower()
        
        if any(word in combined_text for word in ['alquiler', 'rent', 'rental']):
            return 'rent'
        else:
            return 'sale'
    
    def _generate_recommendations(self, property_obj: Property, features: Dict[str, Any]) -> List[str]:
        """Generate recommendations for property improvement"""
        recommendations = []
        
        # Check for missing information
        if not property_obj.bedrooms:
            recommendations.append("Agregar información sobre cantidad de dormitorios")
        
        if not property_obj.bathrooms:
            recommendations.append("Especificar cantidad de baños")
        
        if not property_obj.total_area and not property_obj.covered_area:
            recommendations.append("Incluir información de superficie")
        
        if not property_obj.main_image:
            recommendations.append("Agregar fotografías de la propiedad")
        
        if not property_obj.amenities:
            recommendations.append("Detallar amenities y características especiales")
        
        # Check description quality
        if property_obj.description and len(property_obj.description) < 100:
            recommendations.append("Ampliar la descripción de la propiedad")
        
        # Location recommendations
        if not property_obj.neighborhood:
            recommendations.append("Especificar barrio o zona")
        
        if not property_obj.latitude or not property_obj.longitude:
            recommendations.append("Agregar coordenadas geográficas")
        
        return recommendations
    
    def _calculate_confidence_score(self, property_obj: Property, features: Dict[str, Any], classification: Dict[str, str]) -> float:
        """Calculate confidence score for property data quality"""
        score = 0.0
        max_score = 10.0
        
        # Basic information (3 points)
        if property_obj.title:
            score += 0.5
        if property_obj.description and len(property_obj.description) > 50:
            score += 1.0
        if property_obj.price_amount:
            score += 1.0
        if property_obj.source_url:
            score += 0.5
        
        # Location information (2 points)
        if property_obj.city:
            score += 0.5
        if property_obj.neighborhood:
            score += 0.5
        if property_obj.address:
            score += 0.5
        if property_obj.latitude and property_obj.longitude:
            score += 0.5
        
        # Property features (3 points)
        if property_obj.bedrooms:
            score += 0.5
        if property_obj.bathrooms:
            score += 0.5
        if property_obj.total_area or property_obj.covered_area:
            score += 1.0
        if property_obj.amenities:
            score += 0.5
        if property_obj.parking_spaces:
            score += 0.5
        
        # Contact information (1 point)
        if property_obj.agent_name or property_obj.agency_name:
            score += 0.5
        if property_obj.phone or property_obj.email:
            score += 0.5
        
        # Images (1 point)
        if property_obj.main_image:
            score += 0.5
        if property_obj.gallery and len(property_obj.gallery) > 1:
            score += 0.5
        
        return min(score / max_score, 1.0)
    
    def _create_fallback_analysis(self, property_obj: Property) -> PropertyAnalysis:
        """Create fallback analysis when LLM fails"""
        return PropertyAnalysis(
            confidence_score=0.5,
            extracted_features={},
            enhanced_description=property_obj.description or "",
            classification={
                'property_type': 'apartment',
                'operation_type': 'sale'
            },
            location_details={
                'city': property_obj.city,
                'neighborhood': property_obj.neighborhood
            },
            summary=property_obj.title or "Propiedad disponible",
            recommendations=["Verificar información de la propiedad"]
        )
    
    def batch_analyze_properties(self, properties: List[Property]) -> List[PropertyAnalysis]:
        """Analyze multiple properties in batch"""
        results = []
        
        for property_obj in properties:
            try:
                analysis = self.analyze_property(property_obj)
                results.append(analysis)
                app_logger.info(f"Analyzed property {property_obj.external_id}")
            except Exception as e:
                app_logger.error(f"Failed to analyze property {property_obj.external_id}: {e}")
                results.append(self._create_fallback_analysis(property_obj))
        
        return results
    
    def get_market_insights(self, properties: List[Property]) -> Dict[str, Any]:
        """Generate market insights from property data"""
        if not properties:
            return {}
        
        # Prepare data for LLM analysis
        property_summaries = []
        for prop in properties[:10]:  # Limit to 10 properties for analysis
            summary = {
                'type': prop.property_type.value if prop.property_type else 'unknown',
                'operation': prop.operation_type.value if prop.operation_type else 'unknown',
                'price': prop.price_amount,
                'currency': prop.price_currency.value if prop.price_currency else 'unknown',
                'location': f"{prop.city} {prop.neighborhood}".strip(),
                'area': prop.total_area or prop.covered_area,
                'bedrooms': prop.bedrooms,
                'bathrooms': prop.bathrooms
            }
            property_summaries.append(summary)
        
        # Generate insights using LLM
        system_prompt = """
        Eres un analista de mercado inmobiliario en Argentina.
        Analiza los datos de propiedades y genera insights de mercado.
        
        Incluye:
        - Tendencias de precios por tipo de propiedad
        - Zonas más demandadas
        - Características más valoradas
        - Recomendaciones para compradores/vendedores
        
        Responde en formato JSON con las claves: price_trends, popular_areas, valued_features, recommendations
        """
        
        import json
        data_text = json.dumps(property_summaries, ensure_ascii=False, indent=2)
        prompt = f"Analiza estos datos de propiedades:\n\n{data_text}"
        
        response = self.llm.generate(prompt, system_prompt)
        
        if response.success:
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                return {"raw_insights": response.content}
        else:
            return {"error": "No se pudieron generar insights de mercado"}