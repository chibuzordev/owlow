# analyzer_worker/analyze_batch.py
from analyzer_worker.analyzer_core import AnalyzerCore

if __name__ == "__main__":
    job = AnalyzerCore(model_name="gpt-4o-mini", input_path="data/listings.csv")
    job.run_analysis(limit=20)