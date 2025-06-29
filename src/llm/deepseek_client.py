import json
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..utils import app_logger
from ..utils import settings


@dataclass
class LLMResponse:
    """Response from LLM API"""
    content: str
    usage: Dict[str, int]
    model: str
    success: bool = True
    error: Optional[str] = None


class DeepSeekClient:
    """Client for DeepSeek R1 local LLM"""
    
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or getattr(settings, 'DEEPSEEK_BASE_URL', 'http://localhost:11434')
        self.api_key = api_key or getattr(settings, 'DEEPSEEK_API_KEY', None)
        self.model = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-r1:latest')
        self.timeout = getattr(settings, 'DEEPSEEK_TIMEOUT', 30)
        
        # Headers for API requests
        self.headers = {
            'Content-Type': 'application/json',
        }
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
    
    def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> LLMResponse:
        """Generate text using DeepSeek R1 model"""
        try:
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Prepare request data
            data = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                **kwargs
            }
            
            # Make API request
            response = requests.post(
                f"{self.base_url}/api/chat",
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return LLMResponse(
                    content=result.get('message', {}).get('content', ''),
                    usage=result.get('usage', {}),
                    model=result.get('model', self.model),
                    success=True
                )
            else:
                app_logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                return LLMResponse(
                    content="",
                    usage={},
                    model=self.model,
                    success=False,
                    error=f"API error: {response.status_code}"
                )
                
        except requests.exceptions.RequestException as e:
            app_logger.error(f"DeepSeek connection error: {e}")
            return LLMResponse(
                content="",
                usage={},
                model=self.model,
                success=False,
                error=f"Connection error: {str(e)}"
            )
        except Exception as e:
            app_logger.error(f"DeepSeek unexpected error: {e}")
            return LLMResponse(
                content="",
                usage={},
                model=self.model,
                success=False,
                error=f"Unexpected error: {str(e)}"
            )
    
    def analyze_property_text(self, text: str) -> Dict[str, Any]:
        """Analyze property description and extract structured data"""
        system_prompt = """
        Eres un experto en análisis de propiedades inmobiliarias en Argentina. 
        Tu tarea es analizar descripciones de propiedades y extraer información estructurada.
        
        Extrae la siguiente información del texto:
        - Tipo de propiedad (departamento, casa, oficina, local, terreno)
        - Número de dormitorios
        - Número de baños
        - Superficie total y cubierta (en m²)
        - Piso (si aplica)
        - Amenities y características especiales
        - Estado de la propiedad (nuevo, usado, a estrenar, etc.)
        - Ubicación específica (barrio, zona)
        - Precio estimado si se menciona
        - Puntos destacados de la propiedad
        
        Responde en formato JSON válido.
        """
        
        prompt = f"Analiza esta descripción de propiedad:\n\n{text}"
        
        response = self.generate(prompt, system_prompt)
        
        if response.success:
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                app_logger.warning("Failed to parse LLM response as JSON")
                return {"raw_response": response.content}
        else:
            return {"error": response.error}
    
    def enhance_property_description(self, title: str, description: str, features: Dict[str, Any]) -> str:
        """Enhance property description using LLM"""
        system_prompt = """
        Eres un experto en marketing inmobiliario en Argentina. 
        Tu tarea es mejorar descripciones de propiedades para hacerlas más atractivas y completas.
        
        Reglas:
        - Mantén la información factual exacta
        - Usa un tono profesional pero atractivo
        - Incluye características destacadas
        - Menciona la ubicación de manera atractiva
        - Agrega valor percibido sin exagerar
        - Usa español argentino
        - Máximo 300 palabras
        """
        
        features_text = json.dumps(features, ensure_ascii=False, indent=2)
        prompt = f"""
        Mejora esta descripción de propiedad:
        
        Título: {title}
        Descripción actual: {description}
        Características: {features_text}
        
        Genera una descripción mejorada y atractiva.
        """
        
        response = self.generate(prompt, system_prompt)
        return response.content if response.success else description
    
    def classify_property_type(self, title: str, description: str) -> str:
        """Classify property type using LLM"""
        system_prompt = """
        Clasifica el tipo de propiedad basándote en el título y descripción.
        
        Tipos válidos:
        - apartment (departamento)
        - house (casa, chalet, PH)
        - commercial (local comercial, negocio)
        - office (oficina)
        - land (terreno, lote)
        
        Responde solo con una palabra: apartment, house, commercial, office, o land
        """
        
        prompt = f"Título: {title}\nDescripción: {description}"
        
        response = self.generate(prompt, system_prompt)
        
        if response.success:
            classification = response.content.strip().lower()
            valid_types = ['apartment', 'house', 'commercial', 'office', 'land']
            return classification if classification in valid_types else 'apartment'
        else:
            return 'apartment'  # Default fallback
    
    def extract_location_details(self, location_text: str) -> Dict[str, str]:
        """Extract detailed location information using LLM"""
        system_prompt = """
        Extrae información detallada de ubicación de propiedades en Argentina.
        
        Del texto de ubicación, identifica:
        - provincia (province)
        - ciudad (city) 
        - barrio (neighborhood)
        - zona específica (area)
        
        Responde en formato JSON con las claves: province, city, neighborhood, area
        Si algún dato no está disponible, usa null.
        """
        
        prompt = f"Ubicación: {location_text}"
        
        response = self.generate(prompt, system_prompt)
        
        if response.success:
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                return {"raw_location": location_text}
        else:
            return {"raw_location": location_text}
    
    def generate_property_summary(self, property_data: Dict[str, Any]) -> str:
        """Generate a concise property summary"""
        system_prompt = """
        Genera un resumen conciso y atractivo de una propiedad inmobiliaria.
        El resumen debe ser de máximo 100 palabras y destacar los puntos más importantes.
        Usa español argentino y un tono profesional.
        """
        
        property_text = json.dumps(property_data, ensure_ascii=False, indent=2)
        prompt = f"Genera un resumen para esta propiedad:\n\n{property_text}"
        
        response = self.generate(prompt, system_prompt)
        return response.content if response.success else "Propiedad disponible para consulta."
    
    def check_health(self) -> bool:
        """Check if DeepSeek service is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False