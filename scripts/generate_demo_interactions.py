from pathlib import Path
import sys
from scipy import sparse
import os


sys.path.insert(0, str(Path(__file__).parents[1]))
from recommender.preprocessing import load_processed
from recommender.collaborative import simulate_interactions
ROOT = Path(__file__).parents[1]
if __name__ == '__main__':
    data = load_processed(ROOT/'data/processed/tracks.parquet')
    x = simulate_interactions(data)
    file_path = os.path.join(ROOT, 'data/interactions/synthetic_interactions.npz')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    sparse.save_npz(file_path, x)
    print(f'Saved {x.nnz:,} synthetic events; these are not real listener data.')
