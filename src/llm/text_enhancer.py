from typing import Dict, Any, Optional, List
import re

from .deepseek_client import DeepSeekClient
from ..utils import app_logger


class TextEnhancer:
    """Text enhancement and processing using LLM"""
    
    def __init__(self, llm_client: DeepSeekClient = None):
        self.llm = llm_client or DeepSeekClient()
    
    def clean_and_enhance_description(self, description: str) -> str:
        """Clean and enhance property description"""
        if not description:
            return ""
        
        # Basic cleaning
        cleaned = self._basic_text_cleaning(description)
        
        # Enhance with LLM
        system_prompt = """
        Mejora y limpia esta descripción de propiedad inmobiliaria.
        
        Tareas:
        - Corregir errores ortográficos y gramaticales
        - Mejorar la estructura y fluidez
        - Mantener toda la información factual
        - Usar español argentino profesional
        - Eliminar texto repetitivo o irrelevante
        - Máximo 400 palabras
        """
        
        response = self.llm.generate(cleaned, system_prompt)
        return response.content if response.success else cleaned
    
    def extract_key_features(self, text: str) -> List[str]:
        """Extract key features from property text"""
        system_prompt = """
        Extrae las características más importantes de esta descripción de propiedad.
        
        Busca:
        - Características estructurales (dormitorios, baños, superficie)
        - Amenities (piscina, gimnasio, seguridad, etc.)
        - Ubicación destacada
        - Estado de la propiedad
        - Características únicas
        
        Responde con una lista de características separadas por comas.
        Máximo 10 características.
        """
        
        response = self.llm.generate(text, system_prompt)
        
        if response.success:
            features = [f.strip() for f in response.content.split(',')]
            return [f for f in features if f and len(f) > 3][:10]
        else:
            return self._extract_features_fallback(text)
    
    def generate_seo_title(self, title: str, location: str, property_type: str) -> str:
        """Generate SEO-optimized title"""
        system_prompt = """
        Genera un título optimizado para SEO de una propiedad inmobiliaria.
        
        Requisitos:
        - Incluir tipo de propiedad y ubicación
        - Máximo 60 caracteres
        - Atractivo para búsquedas
        - Español argentino
        - Incluir palabras clave relevantes
        """
        
        prompt = f"Título original: {title}\nUbicación: {location}\nTipo: {property_type}"
        
        response = self.llm.generate(prompt, system_prompt)
        
        if response.success and len(response.content) <= 60:
            return response.content
        else:
            return self._generate_seo_title_fallback(title, location, property_type)
    
    def generate_meta_description(self, description: str, features: List[str]) -> str:
        """Generate meta description for SEO"""
        system_prompt = """
        Genera una meta descripción para SEO de una propiedad inmobiliaria.
        
        Requisitos:
        - Máximo 160 caracteres
        - Incluir características principales
        - Call to action atractivo
        - Español argentino
        """
        
        features_text = ", ".join(features[:5])
        prompt = f"Descripción: {description[:200]}\nCaracterísticas: {features_text}"
        
        response = self.llm.generate(prompt, system_prompt)
        
        if response.success and len(response.content) <= 160:
            return response.content
        else:
            return self._generate_meta_description_fallback(description, features)
    
    def translate_to_english(self, text: str) -> str:
        """Translate property description to English"""
        system_prompt = """
        Traduce esta descripción de propiedad inmobiliaria al inglés.
        
        Requisitos:
        - Traducción natural y profesional
        - Mantener términos inmobiliarios apropiados
        - Adaptar medidas y monedas si es necesario
        - Conservar toda la información factual
        """
        
        response = self.llm.generate(text, system_prompt)
        return response.content if response.success else text
    
    def generate_social_media_post(self, property_data: Dict[str, Any], platform: str = "instagram") -> str:
        """Generate social media post for property"""
        system_prompt = f"""
        Genera un post para {platform} promocionando esta propiedad inmobiliaria.
        
        Requisitos para {platform}:
        - Tono atractivo y moderno
        - Incluir hashtags relevantes
        - Call to action claro
        - Español argentino
        - Máximo 280 caracteres para Twitter, 500 para Instagram
        """
        
        import json
        property_text = json.dumps(property_data, ensure_ascii=False, indent=2)
        
        response = self.llm.generate(property_text, system_prompt)
        return response.content if response.success else self._generate_social_post_fallback(property_data)
    
    def extract_price_from_text(self, text: str) -> Dict[str, Any]:
        """Extract price information from text"""
        system_prompt = """
        Extrae información de precio de este texto inmobiliario.
        
        Busca:
        - Precio principal
        - Moneda (USD, ARS, EUR)
        - Expensas si se mencionan
        - Precio por m² si está disponible
        
        Responde en formato JSON con las claves: price, currency, expenses, price_per_sqm
        """
        
        response = self.llm.generate(text, system_prompt)
        
        if response.success:
            try:
                import json
                return json.loads(response.content)
            except json.JSONDecodeError:
                return self._extract_price_fallback(text)
        else:
            return self._extract_price_fallback(text)
    
    def _basic_text_cleaning(self, text: str) -> str:
        """Basic text cleaning operations"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove special characters but keep Spanish accents
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)ñáéíóúüÑÁÉÍÓÚÜ]', '', text)
        
        # Fix common issues
        text = text.replace('  ', ' ')
        text = text.strip()
        
        return text
    
    def _extract_features_fallback(self, text: str) -> List[str]:
        """Fallback feature extraction using regex"""
        features = []
        
        # Common patterns
        patterns = {
            'dormitorios': r'(\d+)\s*dormitorios?',
            'baños': r'(\d+)\s*baños?',
            'cocheras': r'(\d+)\s*cocheras?',
            'piscina': r'piscina',
            'gimnasio': r'gimnasio',
            'seguridad': r'seguridad',
            'balcón': r'balcón',
            'terraza': r'terraza'
        }
        
        text_lower = text.lower()
        
        for feature, pattern in patterns.items():
            if re.search(pattern, text_lower):
                match = re.search(pattern, text_lower)
                if match and match.groups():
                    features.append(f"{match.group(1)} {feature}")
                else:
                    features.append(feature)
        
        return features[:10]
    
    def _generate_seo_title_fallback(self, title: str, location: str, property_type: str) -> str:
        """Fallback SEO title generation"""
        # Simple template-based generation
        clean_title = title[:30] if title else property_type
        clean_location = location[:20] if location else ""
        
        if clean_location:
            return f"{clean_title} en {clean_location}"[:60]
        else:
            return clean_title[:60]
    
    def _generate_meta_description_fallback(self, description: str, features: List[str]) -> str:
        """Fallback meta description generation"""
        desc_part = description[:100] if description else "Propiedad disponible"
        features_part = ", ".join(features[:3]) if features else ""
        
        if features_part:
            meta = f"{desc_part}. {features_part}. ¡Consultá ya!"
        else:
            meta = f"{desc_part}. ¡Consultá ya!"
        
        return meta[:160]
    
    def _generate_social_post_fallback(self, property_data: Dict[str, Any]) -> str:
        """Fallback social media post generation"""
        title = property_data.get('title', 'Propiedad disponible')
        location = property_data.get('location', '')
        price = property_data.get('price', '')
        
        post = f"🏠 {title[:50]}"
        if location:
            post += f" en {location[:30]}"
        if price:
            post += f"\n💰 ${price}"
        post += "\n¡Consultá ya! #inmuebles #argentina #propiedad"
        
        return post[:280]
    
    def _extract_price_fallback(self, text: str) -> Dict[str, Any]:
        """Fallback price extraction using regex"""
        result = {
            'price': None,
            'currency': None,
            'expenses': None,
            'price_per_sqm': None
        }
        
        # Price patterns
        price_patterns = [
            r'USD?\s*(\d{1,3}(?:\.\d{3})*)',
            r'\$\s*(\d{1,3}(?:\.\d{3})*)',
            r'(\d{1,3}(?:\.\d{3})*)\s*dólares',
            r'(\d{1,3}(?:\.\d{3})*)\s*pesos'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['price'] = match.group(1).replace('.', '')
                if 'USD' in pattern or '$' in pattern or 'dólares' in pattern:
                    result['currency'] = 'USD'
                else:
                    result['currency'] = 'ARS'
                break
        
        return result