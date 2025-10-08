# api_service/routes/recommend.py
from fastapi import APIRouter, Query, Body
from typing import Optional, List, Dict, Any
import pandas as pd
import json
from api_service.models.recommender import Recommender
from api_service.models.advisor import Advisor
from api_service.models.preprocessor import Preprocessor

router = APIRouter()

# ---------- Initialize modules ----------
recommender = Recommender()
advisor: Optional[Advisor] = None
preprocessor = Preprocessor()

# ---------- Endpoint: Fit recommender ----------
@router.post("/fit")
async def fit_recommender(data: List[Dict[str, Any]] = Body(...)):
    """
    Fit the recommender model using uploaded property data.
    This should be run once after fetching from Prop-Intel API.
    """
    df = pd.DataFrame(data)
    df_p = preprocessor.transform(df)
    recommender.fit(df_p)
    global advisor
    advisor = Advisor(recommender)
    return {"status": "fitted", "records": len(df_p)}

# ---------- Endpoint: Get recommendations ----------
@router.get("/suggest")
async def suggest_properties(
    budget: Optional[float] = Query(None),
    city: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    reference_id: Optional[str] = Query(None),
    top_n: int = Query(5),
    include_condition: bool = Query(False)
):
    """
    Return top-N alternative listings within the user’s budget or by similarity.
    """
    if advisor is None:
        return {"error": "Model not fitted. Please call /api/recommend/fit first."}

    payload = advisor.advise(
        budget=budget,
        city=city,
        title=title,
        reference_id=reference_id,
        top_n=top_n,
        include_condition=include_condition
    )
    return {"status": "success", "advice": payload}

# ---------- Endpoint: Export precomputed recommendations ----------
@router.post("/export")
async def export_recommendations(
    style: str = Query("nested", enum=["nested", "normalized", "wide"]),
    top_n: int = Query(5)
):
    """
    Precompute and export recommendations in JSON for downstream API/DB.
    """
    if recommender.df is None:
        return {"error": "No data fitted yet. Use /api/recommend/fit first."}

    data = recommender.export_recommendations(fmt="json", style=style, top_n=top_n)
    return {"status": "exported", "style": style, "count": len(data)}
