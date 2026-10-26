"""A small lazy singleton around the already-trained recommendation models."""
import sys
from pathlib import Path

import joblib

# Adding this directory lets joblib find recommender classes while unpickling.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from recommender.hybrid import HybridRecommender
from recommender.preprocessing import load_processed

_data = None
_engine = None


def get_data():
    """Load processed tracks once, on the first request that needs them."""
    global _data
    if _data is None:
        _data = load_processed(ROOT / "data" / "processed" / "tracks.parquet")
    return _data


def get_engine():
    """Load models once and return the shared hybrid recommender."""
    global _engine
    if _engine is None:
        _engine = HybridRecommender(
            get_data(),
            joblib.load(ROOT / "models" / "content.joblib"),
            joblib.load(ROOT / "models" / "collaborative.joblib"),
        )
    return _engine
