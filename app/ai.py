# app/ai.py
import os, re, json, time
from typing import Dict, Any, Optional, List
import pandas as pd
from openai import OpenAI
from .models import Property
from dataclasses import asdict

# init OpenAI client from env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AIFilterParser:
    def __init__(self, model: str = os.getenv("AI_FILTER_MODEL", "gpt-4o-mini")):
        self.model = model

    def parse(self, query: str, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        schema_hint = ""
        if df is not None:
            cols = list(df.columns)
            schema_hint = f"Available fields: {', '.join(cols)}."

        system_prompt = f"""
You are an expert real estate AI filter builder.
Output strict JSON with:
{{"city": null|"string","voivodeship":null|"string","district":null|"string",
 "bedrooms":null|"int","price_min":null|"int","price_max":null|"int",
 "area_min":null|"int","area_max":null|"int","features":{{}},"keywords":[]}}
{schema_hint}
Return JSON only, no explanation.
"""
        user_prompt = f"User query: {query}\nReturn JSON."

        try:
            resp = client.responses.create(
                model=self.model,
                input=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],
                max_output_tokens=400
            )
            raw = getattr(resp, "output_text", "") or ""
            m = re.search(r"\{.*\}", raw, re.S)
            filters = json.loads(m.group(0)) if m else {"error":"no_json"}
        except Exception as e:
            filters = {"error": str(e)}

        # normalize
        defaults = {"city": None,"voivodeship":None,"district":None,"bedrooms":None,
                    "price_min":0,"price_max":None,"area_min":0,"area_max":None,"features":{},"keywords":[]}
        for k,v in defaults.items():
            filters.setdefault(k, v)
        # coerce feature list -> dict
        if isinstance(filters.get("features"), list):
            filters["features"] = {f: True for f in filters["features"]}
        if not isinstance(filters.get("features"), dict):
            filters["features"] = {}
        # numeric coercion
        for key in ["price_min","price_max","area_min","area_max"]:
            try:
                if filters.get(key) is not None:
                    filters[key] = float(filters[key])
            except:
                filters[key] = None
        return filters

class PropertyAnalyzer:
    """
    Batch analyze properties: one-time processing for dataset refresh.
    Use analyze_batch to return a list of analyses aligned with input order.
    """

    def __init__(self, model: str = os.getenv("ANALYZER_MODEL", "gpt-4o-mini")):
        self.model = model

    def analyze_property(self, prop: Property) -> Dict[str, Any]:
        sys = ("ROLE: Polish speaking property analyst. Output strict JSON with keys: "
               '{"summary","condition","recommendation"} - concise.')
        brief = prop.description[:800] if prop.description else ""
        images = "\n".join((prop.media or [])[:3])
        user = f"Property summary:\n{json.dumps(asdict(prop), ensure_ascii=False)}\n\nImages:\n{images}\n\nDescription excerpt:\n{brief}"
        try:
            resp = client.responses.create(
                model=self.model,
                input=[{"role":"system","content":sys},{"role":"user","content":user}],
                max_output_tokens=500
            )
            raw = getattr(resp, "output_text", "") or ""
            m = re.search(r"\{.*\}", raw, re.S)
            return json.loads(m.group(0)) if m else {"raw": raw}
        except Exception as e:
            return {"error": str(e)}

    def analyze_batch(self, props: List[Property], use_llm: bool = True) -> List[Dict[str, Any]]:
        # Return list aligned to props order
        results = []
        if not use_llm:
            for _ in props:
                results.append({"analysis": "[Analysis pending]"})
            return results

        for p in props:
            res = self.analyze_property(p)
            results.append(res)
            time.sleep(0.2)  # small throttle
        return results

class Advisor:
    def __init__(self, model: str = os.getenv("ADVISOR_MODEL", "gpt-5"), max_retries: int = 1):
        self.model = model
        self.max_retries = max_retries

    def _sanitize(self, text: Optional[str]) -> str:
        if not text:
            return ""
        t = text.strip()
        t = re.sub(r"^```.*?```$", "", t, flags=re.S)
        t = re.sub(r'^[\s\n\'"`“”]+|[\s\n\'"`“”]+$', "", t)
        if t in {"", "''", '""', "“”", "``", "none", "null"}:
            return ""
        return t

    def _looks_valid(self, t: str) -> bool:
        if not t or len(t.split()) < 6:
            return False
        if re.fullmatch(r'[^A-Za-z0-9ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+', t):
            return False
        return True

    def advise(self, user_query: str, top_properties: List[Dict[str, Any]]) -> str:
        # stateless call
        context = json.dumps(top_properties[:5], ensure_ascii=False)
        system = ("ROLE: Professional property advisor. Output plain text only, one short paragraph, no quotes, no markdown.")
        user = f"Query: {user_query}\nTop properties (JSON):\n{context}\n Provide concise advice."

        for _ in range(self.max_retries + 1):
            try:
                resp = client.responses.create(
                    model=self.model,
                    input=[{"role":"system","content":system},{"role":"user","content":user}],
                    max_output_tokens=300
                )
                raw = getattr(resp, "output_text", "") or ""
            except Exception as e:
                raw = ""
            txt = self._sanitize(raw)
            if self._looks_valid(txt):
                return txt
            time.sleep(0.5)
        # fallback deterministic advice:
        return "No strong AI advice available; consider widening your search area or increasing budget slightly."

