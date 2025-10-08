# api_service/routes/advice.py
from fastapi import APIRouter, Query
from api_service.models.advisor import Advisor
from api_service.models.recommender import Recommender
import pandas as pd

router = APIRouter()

# Example: load a small dataset or a pre-fitted recommender (in production, load from DB or JSON)
rec = Recommender()
# df = pd.read_json("shared/recommendations_full.json")
# rec.fit(df)
advisor = Advisor(rec)

@router.get("/")
def get_advice(
    budget: float = Query(None, description="User's available budget in PLN"),
    city: str = Query(None, description="City name to filter results"),
    top_n: int = Query(5, description="Number of suggestions to return"),
):
    """
    Returns AI Advisor recommendations based on budget, location, and available listings.
    """
    payload = advisor.advise(
        budget=budget,
        city=city,
        top_n=top_n,
        include_condition=True
    )
    return payload
