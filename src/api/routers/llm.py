from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ...database.connection import get_db
from ...services.property_service import PropertyService
from ...llm import DeepSeekClient, PropertyAnalyzer, TextEnhancer
from ...utils import app_logger, settings

router = APIRouter(prefix="/llm", tags=["LLM"])


class AnalyzePropertyRequest(BaseModel):
    property_id: int


class AnalyzeTextRequest(BaseModel):
    text: str


class EnhanceDescriptionRequest(BaseModel):
    title: str
    description: str
    features: Optional[Dict[str, Any]] = None


class GenerateSummaryRequest(BaseModel):
    property_data: Dict[str, Any]


class LLMHealthResponse(BaseModel):
    status: str
    model: str
    base_url: str
    enabled: bool


@router.get("/health", response_model=LLMHealthResponse)
async def check_llm_health():
    """Check LLM service health"""
    if not settings.llm_enabled:
        return LLMHealthResponse(
            status="disabled",
            model=settings.deepseek_model,
            base_url=settings.deepseek_base_url,
            enabled=False
        )
    
    try:
        client = DeepSeekClient()
        is_healthy = client.check_health()
        
        return LLMHealthResponse(
            status="healthy" if is_healthy else "unhealthy",
            model=settings.deepseek_model,
            base_url=settings.deepseek_base_url,
            enabled=settings.llm_enabled
        )
    except Exception as e:
        app_logger.error(f"LLM health check failed: {e}")
        return LLMHealthResponse(
            status="error",
            model=settings.deepseek_model,
            base_url=settings.deepseek_base_url,
            enabled=settings.llm_enabled
        )


@router.post("/analyze/property")
async def analyze_property(
    request: AnalyzePropertyRequest,
    db: Session = Depends(get_db)
):
    """Analyze a property using LLM"""
    if not settings.llm_enabled:
        raise HTTPException(status_code=503, detail="LLM service is disabled")
    
    try:
        property_service = PropertyService(db)
        property_obj = property_service.get_property(request.property_id)
        
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")
        
        analyzer = PropertyAnalyzer()
        analysis = analyzer.analyze_property(property_obj)
        
        return {
            "property_id": request.property_id,
            "analysis": {
                "confidence_score": analysis.confidence_score,
                "extracted_features": analysis.extracted_features,
                "enhanced_description": analysis.enhanced_description,
                "classification": analysis.classification,
                "location_details": analysis.location_details,
                "summary": analysis.summary,
                "recommendations": analysis.recommendations
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error analyzing property: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analyze/text")
async def analyze_text(request: AnalyzeTextRequest):
    """Analyze property text using LLM"""
    if not settings.llm_enabled:
        raise HTTPException(status_code=503, detail="LLM service is disabled")
    
    try:
        client = DeepSeekClient()
        result = client.analyze_property_text(request.text)
        
        return {
            "text": request.text[:100] + "..." if len(request.text) > 100 else request.text,
            "analysis": result
        }
        
    except Exception as e:
        app_logger.error(f"Error analyzing text: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/enhance/description")
async def enhance_description(request: EnhanceDescriptionRequest):
    """Enhance property description using LLM"""
    if not settings.llm_enabled:
        raise HTTPException(status_code=503, detail="LLM service is disabled")
    
    try:
        enhancer = TextEnhancer()
        
        # Clean and enhance description
        enhanced = enhancer.clean_and_enhance_description(request.description)
        
        # Extract key features
        features = enhancer.extract_key_features(f"{request.title} {request.description}")
        
        # Generate SEO title
        location = request.features.get('location', '') if request.features else ''
        property_type = request.features.get('property_type', 'propiedad') if request.features else 'propiedad'
        seo_title = enhancer.generate_seo_title(request.title, location, property_type)
        
        # Generate meta description
        meta_description = enhancer.generate_meta_description(enhanced, features)
        
        return {
            "original": {
                "title": request.title,
                "description": request.description
            },
            "enhanced": {
                "description": enhanced,
                "seo_title": seo_title,
                "meta_description": meta_description,
                "key_features": features
            }
        }
        
    except Exception as e:
        app_logger.error(f"Error enhancing description: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/generate/summary")
async def generate_summary(request: GenerateSummaryRequest):
    """Generate property summary using LLM"""
    if not settings.llm_enabled:
        raise HTTPException(status_code=503, detail="LLM service is disabled")
    
    try:
        client = DeepSeekClient()
        summary = client.generate_property_summary(request.property_data)
        
        return {
            "property_data": request.property_data,
            "summary": summary
        }
        
    except Exception as e:
        app_logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/translate/english")
async def translate_to_english(request: AnalyzeTextRequest):
    """Translate property description to English"""
    if not settings.llm_enabled:
        raise HTTPException(status_code=503, detail="LLM service is disabled")
    
    try:
        enhancer = TextEnhancer()
        translation = enhancer.translate_to_english(request.text)
        
        return {
            "original": request.text,
            "translation": translation
        }
        
    except Exception as e:
        app_logger.error(f"Error translating text: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/social/post")
async def generate_social_post(
    property_data: Dict[str, Any],
    platform: str = "instagram"
):
    """Generate social media post for property"""
    if not settings.llm_enabled:
        raise HTTPException(status_code=503, detail="LLM service is disabled")
    
    if platform not in ["instagram", "twitter", "facebook"]:
        raise HTTPException(status_code=400, detail="Unsupported platform")
    
    try:
        enhancer = TextEnhancer()
        post = enhancer.generate_social_media_post(property_data, platform)
        
        return {
            "platform": platform,
            "property_data": property_data,
            "post": post
        }
        
    except Exception as e:
        app_logger.error(f"Error generating social post: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/market/insights")
async def get_market_insights(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get market insights using LLM analysis"""
    if not settings.llm_enabled:
        raise HTTPException(status_code=503, detail="LLM service is disabled")
    
    try:
        property_service = PropertyService(db)
        properties = property_service.get_properties(limit=limit)
        
        if not properties:
            raise HTTPException(status_code=404, detail="No properties found")
        
        analyzer = PropertyAnalyzer()
        insights = analyzer.get_market_insights(properties)
        
        return {
            "total_properties_analyzed": len(properties),
            "insights": insights
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error generating market insights: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/batch/analyze")
async def batch_analyze_properties(
    property_ids: List[int],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Analyze multiple properties in background"""
    if not settings.llm_enabled:
        raise HTTPException(status_code=503, detail="LLM service is disabled")
    
    try:
        property_service = PropertyService(db)
        properties = []
        
        for prop_id in property_ids:
            prop = property_service.get_property(prop_id)
            if prop:
                properties.append(prop)
        
        if not properties:
            raise HTTPException(status_code=404, detail="No valid properties found")
        
        # Add background task
        background_tasks.add_task(
            _batch_analyze_task,
            properties,
            db
        )
        
        return {
            "message": f"Started batch analysis for {len(properties)} properties",
            "property_ids": [p.id for p in properties]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error starting batch analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def _batch_analyze_task(properties: List, db: Session):
    """Background task for batch property analysis"""
    try:
        analyzer = PropertyAnalyzer()
        results = analyzer.batch_analyze_properties(properties)
        
        app_logger.info(f"Completed batch analysis for {len(properties)} properties")
        
        # Here you could save results to database or send notifications
        
    except Exception as e:
        app_logger.error(f"Error in batch analysis task: {e}")


@router.get("/models")
async def list_available_models():
    """List available LLM models"""
    if not settings.llm_enabled:
        raise HTTPException(status_code=503, detail="LLM service is disabled")
    
    try:
        import requests
        response = requests.get(f"{settings.deepseek_base_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json()
            return {
                "current_model": settings.deepseek_model,
                "available_models": models.get("models", [])
            }
        else:
            return {
                "current_model": settings.deepseek_model,
                "available_models": [],
                "error": "Could not fetch available models"
            }
            
    except Exception as e:
        app_logger.error(f"Error listing models: {e}")
        return {
            "current_model": settings.deepseek_model,
            "available_models": [],
            "error": str(e)
        }