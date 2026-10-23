from pathlib import Path
import sys, joblib
from scipy import sparse
import os
sys.path.insert(0, str(Path(__file__).parents[1]))


from recommender.preprocessing import load_processed
from recommender.content_based import ContentRecommender
from recommender.collaborative import ItemCollaborativeFilter
ROOT = Path(__file__).parents[1]

file_path = os.path.join(ROOT, 'models/content.joblib')
os.makedirs(os.path.dirname(file_path), exist_ok=True)
file_path = os.path.join(ROOT, 'models/collaborative.joblib')
os.makedirs(os.path.dirname(file_path), exist_ok=True)
if __name__ == '__main__':
    data = load_processed(ROOT/'data/processed/tracks.parquet')
    content = ContentRecommender(data)
    cf = ItemCollaborativeFilter(data.track_id.to_numpy(), sparse.load_npz(ROOT/'data/interactions/synthetic_interactions.npz'))
    joblib.dump(content, ROOT/'models/content.joblib', compress=3)
    joblib.dump(cf, ROOT/'models/collaborative.joblib', compress=3)
    print('Saved content and synthetic collaborative artifacts.')

