# app/db_adapter.py
import json, os
from typing import List, Dict
from .models import Property

DATA_PATH = "./data.json"
ANALYSIS_CACHE = os.getenv("ANALYSIS_CACHE", "analysis_cache.json")

class LocalDBAdapter:
    """
    Temporary offline adapter — uses local JSON files instead of a real database.
    Keeps full compatibility with the main DBAdapter interface.
    """

    def __init__(self):
        os.makedirs(os.path.dirname(ANALYSIS_CACHE) or ".", exist_ok=True)
        # Load or initialize cache file
        if not os.path.exists(ANALYSIS_CACHE):
            with open(ANALYSIS_CACHE, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def fetch_all_raw(self) -> List[Dict]:
        """Load listings from local file (data.json). Supports both JSON arrays and NDJSON."""
        if not os.path.exists(DATA_PATH):
            raise FileNotFoundError(f"Missing {DATA_PATH}. Please place your processed listings JSON here.")
    
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
    
        # Case 1: proper JSON array
        if content.startswith("["):
            return json.loads(content)
    
        # Case 2: NDJSON (multiple lines)
        lines = [json.loads(line) for line in content.splitlines() if line.strip()]
        return lines

    
    # def fetch_all_raw(self) -> List[Dict]:
    #     """
    #     Load listings from local file (data.json).
    #     Automatically fixes common JSON format issues (concatenated arrays, newline JSON, etc.).
    #     """
    #     if not os.path.exists(DATA_PATH):
    #         os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    #         with open(DATA_PATH, "w", encoding="utf-8") as f:
    #             json.dump([], f)
    #         print(f"[INFO] Created empty dataset at {DATA_PATH}")
    #         return []
    
    #     with open(DATA_PATH, "r", encoding="utf-8") as f:
    #         content = f.read().strip()
    
    #     # Fix accidental concatenated arrays (e.g. "][")
    #     if "][" in content:
    #         content = content.replace("][", ",")
    
    #     # Try parsing as a single JSON value
    #     try:
    #         data = json.loads(content)
    #         return data if isinstance(data, list) else [data]
    #     except json.JSONDecodeError:
    #         # fallback: newline-delimited JSON
    #         print("[WARN] Malformed JSON detected — attempting line-by-line parse.")
    #         lines = [json.loads(line) for line in content.splitlines() if line.strip()]
    #         return lines


    def update_analysis_batch(self, updates: List[Dict[str, any]]):
        """
        Saves analysis results locally to analysis_cache.json
        Keeps a mapping of id -> analysis.
        """
        try:
            with open(ANALYSIS_CACHE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

        for upd in updates:
            cache[upd["id"]] = upd.get("analysis", {})

        with open(ANALYSIS_CACHE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

        return {"saved": len(updates)}

class DBAdapter:
    """
    Minimal interface the backend team should implement.
    Replace methods with real DB calls (Postgres, DynamoDB, etc).
    """

    def fetch_all_raw(self) -> List[Dict]:
        """
        Return raw listing records (list of dicts) exactly as in your processed data.
        """
        raise NotImplementedError("Implement fetch_all_raw to return list of raw records")

    def update_analysis_batch(self, updates: List[Dict[str, any]]):
        """
        Accepts list of records: [{"id": "<sourceId>", "analysis": {...}}, ...]
        and update DB accordingly (JSONB column).
        """
        raise NotImplementedError("Implement update_analysis_batch to persist analysis into DB")








