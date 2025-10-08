# recommender_worker/recommender_core.py
import json
import pandas as pd
from models.preprocessor import Preprocessor
from models.recommender import Recommender

class RecommenderCore:
    """
    Lightweight wrapper for training and exporting property recommendations.
    """

    def __init__(self, input_path="data/listings.csv"):
        self.input_path = input_path
        self.prep = Preprocessor()
        self.rec = Recommender()

    def train(self, top_n=5, output_path="recommendations.json", fmt="json"):
        df = pd.read_csv(self.input_path)
        df_p = self.prep.transform(df)
        self.rec.fit(df_p)
        data = self.rec.build_json_recommendation_table(top_n=top_n)

        if fmt == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif fmt == "csv":
            pd.DataFrame(data).to_csv(output_path, index=False)
        print(f"[INFO] Exported {len(data)} recommendations to {output_path}")
