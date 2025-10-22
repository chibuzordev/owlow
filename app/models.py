# app/models.py
import re, json, numpy as np, pandas as pd
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class Property:
    id: str
    title: Optional[str]
    price: float
    priceCurrency: str
    pricePerM2: float
    city: str
    voivodeship: str
    district: Optional[str]
    bedrooms: Optional[int]
    areaM2: float
    features: Dict[str, Any]
    description: str
    media: List[str]
    # analysis is optional and may be set later
    analysis: Optional[Dict[str, Any]] = None

class PropertyNormalizer:
    FEATURE_SYNONYMS = {
        "balcony": ["balkon"],
        "basement": ["piwnica"],
        "garden": ["ogród", "ogródek"],
        "terrace": ["taras"],
        "parking": ["parking", "garaż", "miejsce postojowe"],
        "elevator": ["winda"],
        "bathtub": ["wanna"],
        "air_conditioning": ["klimatyzacja"],
        "intercom": ["domofon", "wideofon"],
        "separate_kitchen": ["oddzielna kuchnia"],
        "security": ["monitoring", "ochrona"],
    }

    def _text_blob(self, info_dict: dict, description: str) -> str:
        text_parts = []
        for k, v in info_dict.items():
            if isinstance(v, str):
                text_parts.append(v)
            else:
                try:
                    text_parts.append(str(v))
                except:
                    pass
        text_parts.append(description or "")
        return " ".join([t.lower() for t in text_parts if t])

    @staticmethod
    def _stringify(v):
        if isinstance(v, dict):
            # flatten dicts like {"value": 7863, "currency": "PLN"}
            return " ".join([f"{k}:{val}" for k, val in v.items()])
        if isinstance(v, list):
            return " ".join(map(str, v))
        return str(v)
    
    def normalize(self, record: Dict[str, Any]) -> Property:
        location = record.get("location", {}) or {}
        # add = {item.get("label", "").strip(): item.get("value", "") for item in record.get("additionalInfo", []) or []}

        add = {
            item.get("label", "").strip(): item.get("value", "")
            for item in record.get("additionalInfo", []) or []
            if isinstance(item, dict)
        }

        extras_blob = " ".join([self._stringify(v) for v in add.values()]) + " " + str(record.get("description") or "")
        # extras_blob = " ".join([v for v in add.values() if isinstance(v, str)]) + " " + (record.get("description") or "")
        extras_blob = extras_blob.lower()

        features = {}
        for feat, keywords in self.FEATURE_SYNONYMS.items():
            features[feat] = any(k in extras_blob for k in keywords)

        return Property(
            id=record.get("sourceId") or record.get("id") or "",
            title=record.get("title"),
            price=float(record.get("price") or 0),
            priceCurrency=(record.get("pricePerM2") or {}).get("currency", "PLN"),
            pricePerM2=float((record.get("pricePerM2") or {}).get("value") or 0),
            city=(location.get("city") or "").capitalize(),
            voivodeship=(location.get("voivodeship") or "").capitalize(),
            district=location.get("district"),
            bedrooms=int(record.get("bedrooms")) if record.get("bedrooms") not in (None, "", np.nan) else None,
            areaM2=float(record.get("areaM2") or 0),
            features=features,
            description=record.get("description") or "",
            media=[m.get("url") for m in record.get("media") or [] if m.get("kind") == "image"]
        )

class Preprocessor:
    """
    Lightweight flattening for a DataFrame (used if you want to ingest CSV/DF).
    Keep minimal — DB adapter should prefer raw JSON -> normalizer.
    """
    @staticmethod
    def transform(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # assume df has nested fields as in your notebook
        if "pricePerM2" in df.columns:
            df["pricePerM2_value"] = df["pricePerM2"].apply(lambda x: (x or {}).get("value") if isinstance(x, dict) else None)
            df["pricePerM2_currency"] = df["pricePerM2"].apply(lambda x: (x or {}).get("currency") if isinstance(x, dict) else None)
        # location flattening
        if "location" in df.columns:
            df["city"] = df["location"].apply(lambda x: (x or {}).get("city", "") if isinstance(x, dict) else "")
            df["voivodeship"] = df["location"].apply(lambda x: (x or {}).get("voivodeship", "") if isinstance(x, dict) else "")
        for col in ["price", "areaM2", "bedrooms"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df




