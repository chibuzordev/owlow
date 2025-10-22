# app/main.py
import os, json
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from .models import PropertyNormalizer
from .ai import AIFilterParser, PropertyAnalyzer, Advisor
from .recommender import PropertyRecommender, SessionCache
#from .db_adapter import DBAdapter
from .db_adapter import LocalDBAdapter as DBAdapter

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# instantiate classes
normalizer = PropertyNormalizer()
parser = AIFilterParser()
analyzer = PropertyAnalyzer()
advisor = Advisor()
cache = SessionCache()

# TODO: backend must replace this with real DB adapter instance
db = DBAdapter()

@app.post("/analyze")
def analyze_all(use_llm: bool = True):
    """
    Batch analyze step. Intended to be run periodically (cron, scheduler) or on-demand.
    It fetches all raw records, normalizes them, runs analyze_batch, and persists.
    """
    raw = db.fetch_all_raw()
    if not raw:
        return {"status": "no_data"}
    props = [normalizer.normalize(r) for r in raw]
    results = analyzer.analyze_batch(props, use_llm=use_llm)
    # build updates list
    updates = []
    for p, analysis in zip(props, results):
        updates.append({"id": p.id, "analysis": analysis})
    db.update_analysis_batch(updates)
    return {"status": "ok", "count": len(updates)}

@app.get("/recommend")
def recommend(q: str = Query(...), session_id: str = Query(None)):
    """
    Parse query, return filters, results, and advisor text.
    """
    # fetch raw + normalize into DataFrame
    raw = db.fetch_all_raw()
    props = [normalizer.normalize(r) for r in raw]
    df = pd.DataFrame([p.__dict__ for p in props])

    filters = parser.parse(q, df=df)
    if session_id:
        cache.save_filters(session_id, filters)

    recommender = PropertyRecommender(df)
    results = recommender.filter_properties(filters)
    top = results.sort_values("price").head(5).to_dict(orient="records")
    advice_text = advisor.advise(q, top)
    return {"filters": filters, "results": top, "advisor": advice_text}
