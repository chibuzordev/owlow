# api_service/routes/analyze_property.py
from fastapi import APIRouter, Body
from typing import List, Optional
from api_service.models.analyzer import PropertyAnalyzer

router = APIRouter()

# Initialize the analyzer (use_llm=False unless you have OpenAI API key)
analyzer = PropertyAnalyzer(llm_model="gpt-4o-mini")

@router.post("/")
async def analyze_property(
    image_urls: Optional[List[str]] = Body(default=[]),
    description: Optional[str] = Body(default=""),
    use_llm: bool = Body(default=False)
):
    """
    Analyze a property based on description and optional images.
    Returns structured JSON with condition and component-level analysis.
    """
    result = analyzer.analyze(image_urls=image_urls, description=description, use_llm=use_llm)
    return {
        "status": "success",
        "analysis": result
    }
