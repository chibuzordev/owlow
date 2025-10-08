# analyzer_worker/analyzer_core.py
import json
import pandas as pd
from models.analyzer import PropertyAnalyzer

class AnalyzerCore:
    """
    Runs batch-level photo + description AI analysis on property listings.
    """

    def __init__(self, model_name="gpt-4o-mini", input_path="data/listings.csv"):
        self.model_name = model_name
        self.input_path = input_path
        self.analyzer = PropertyAnalyzer(llm_model=model_name)

    def run_analysis(self, output_path="data/analysis_results.json", limit=None):
        df = pd.read_csv(self.input_path)
        results = []
        for i, row in df.head(limit).iterrows():
            urls = [row.get("url")] if isinstance(row.get("url"), str) else []
            desc = row.get("description", "")
            analysis = self.analyzer.analyze(urls, desc, use_llm=True)
            results.append({
                "id": row.get("_id", i),
                "analysis": analysis
            })

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Saved {len(results)} analyses to {output_path}")
