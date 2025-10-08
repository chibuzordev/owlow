# recommender_worker/train_recommender.py
from recommender_worker.recommender_core import RecommenderCore

if __name__ == "__main__":
    model = RecommenderCore(input_path="data/listings.csv")
    model.train(top_n=5, output_path="data/recommendations.json", fmt="json")
