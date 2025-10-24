# app/main.py
import os, json, asyncio
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import numpy as np, pandas as pd
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
    print("🧩 [ANALYZE] Starting analysis...")

    raw = db.fetch_all_raw()
    if not raw:
        print("⚠️ No raw data found.")
        return {"status": "no_data"}

    print(f"✅ Loaded {len(raw)} records")
    props = [normalizer.normalize(r) for r in raw]
    print("🔧 Normalization done")

    # Run analyzer — optionally using LLM if enabled
    try:
        results = analyzer.analyze_batch(props, use_llm=use_llm)
    except Exception as e:
        print("❌ Error during analysis:", e)
        raise HTTPException(status_code=500, detail=f"Analyzer failed: {e}")

    print(f"🧠 Analysis produced {len(results)} results")

    # Build updates and persist locally
    updates = [{"id": p.id, "analysis": analysis} for p, analysis in zip(props, results)]
    db.update_analysis_batch(updates)

    print(f"💾 Saved {len(updates)} analyses cached")
    return {"status": "ok", "count": len(updates)}

# @app.post("/analyze")
# async def analyze_all(use_llm: bool = True):
#     raw = db.fetch_all_raw()
#     props = [normalizer.normalize(r) for r in raw]

#     loop = asyncio.get_running_loop()
#     results = await loop.run_in_executor(None, analyzer.analyze_batch, props, use_llm)

#     updates = [{"id": p.id, "analysis": analysis} for p, analysis in zip(props, results)]
#     db.update_analysis_batch(updates)
#     return {"status": "ok", "count": len(updates)}

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

    # Replace NaN, inf, -inf before serializing
    results = results.replace([np.inf, -np.inf], np.nan)
    results = results.fillna(0)
    print("Incoming:", q)
    print("Filters:", filters)
    print("Results:", len(results), "Top sample:", top[:1])

    top = results.sort_values("price").head(5).to_dict(orient="records")
    advice_text = advisor.advise(q, top)
    return {"filters": filters, "results": top, "advisor": advice_text}
