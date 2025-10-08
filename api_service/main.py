# api_service/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api_service.routes import analyze, recommend

# ---------- Initialize app ----------
app = FastAPI(
    title="PropIntel AI Service",
    description="MVP backend for AI Property Analyzer and AI Advisor",
    version="1.0.0",
)

# ---------- CORS setup ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to frontend domain for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Register routes ----------
app.include_router(analyze.router, prefix="/api/analyze", tags=["AI Analyzer"])
app.include_router(recommend.router, prefix="/api/recommend", tags=["AI Advisor"])

# ---------- Root endpoint ----------
@app.get("/")
def root():
    return {
        "message": "🏠 PropIntel AI backend running successfully.",
        "endpoints": {
            "Analyzer": "/api/analyze/property",
            "Recommender fit": "/api/recommend/fit",
            "Advisor suggest": "/api/recommend/suggest",
            "Recommendation export": "/api/recommend/export"
        },
    }
