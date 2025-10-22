# app/recommender.py
import os, json
import pandas as pd
from typing import Dict, Any, Optional
import redis

class SessionCache:
    def __init__(self):
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                self.client = redis.from_url(redis_url)
            except Exception:
                self.client = None
        else:
            self.client = None
        self.mem = {}

    def save_filters(self, session_id: str, filters: Dict[str, Any]):
        if self.client:
            self.client.set(f"filters:{session_id}", json.dumps(filters))
        else:
            self.mem[session_id] = filters

    def get_filters(self, session_id: str) -> Optional[Dict[str, Any]]:
        if self.client:
            val = self.client.get(f"filters:{session_id}")
            return json.loads(val) if val else None
        return self.mem.get(session_id)

class PropertyRecommender:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def filter_properties(self, filters: Dict[str, Any]) -> pd.DataFrame:
        data = self.df.copy()
        if filters.get("city"):
            data = data[data["city"].str.lower() == str(filters["city"]).lower()]
        if filters.get("voivodeship"):
            data = data[data["voivodeship"].str.lower() == str(filters["voivodeship"]).lower()]
        if filters.get("bedrooms"):
            data = data[data["bedrooms"] == filters["bedrooms"]]
        if filters.get("price_max"):
            data = data[data["price"] <= filters["price_max"]]
        if filters.get("price_min"):
            data = data[data["price"] >= filters["price_min"]]
        if filters.get("area_max"):
            data = data[data["areaM2"] <= filters["area_max"]]
        if filters.get("area_min"):
            data = data[data["areaM2"] >= filters["area_min"]]
        features = filters.get("features", {})
        if isinstance(features, list):
            features = {f: True for f in features}
        if isinstance(features, dict):
            for feat, val in features.items():
                if feat in data.columns and val:
                    data = data[data[feat] == True]
        return data
