# app/db_adapter.py
from typing import List, Dict
from .models import Property

DATA_PATH = os.getenv("DATA_PATH", "data.json")
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
        """
        Load listings from local file (data.json). 
        You can put your processed data in this file to simulate DB data.
        """
        if not os.path.exists(DATA_PATH):
            raise FileNotFoundError(f"Missing {DATA_PATH}. Please place your processed listings JSON here.")
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else [data]

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
