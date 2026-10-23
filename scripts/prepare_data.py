from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
from recommender.preprocessing import clean_dataset
ROOT = Path(__file__).parents[1]
if __name__ == '__main__':
    df = clean_dataset(ROOT/'data/raw/dataset.csv', ROOT/'data/processed/tracks.parquet')
    print(f'Cleaned {len(df):,} unique tracks.')
