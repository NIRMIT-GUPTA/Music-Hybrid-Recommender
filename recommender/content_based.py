import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from .preprocessing import NUMERIC

class ContentRecommender:
    def __init__(self, data):
        self.data = data.reset_index(drop=True).copy()
        self.id_to_index = pd.Series(self.data.index, index=self.data.track_id).to_dict()
        self.features = [x for x in NUMERIC if x in self.data]
        self.transformer = ColumnTransformer([
            ("numbers", StandardScaler(), self.features),
            ("genre", OneHotEncoder(handle_unknown="ignore"), ["track_genre"]),
            ("artist", TfidfVectorizer(token_pattern=r"[^,]+"), "artists"),
        ])
        self.matrix = sparse.csr_matrix(self.transformer.fit_transform(self.data))
        self.knn = NearestNeighbors(metric="cosine", algorithm="brute", n_jobs=-1).fit(self.matrix)

    def scores_for_track(self, track_id, candidates=None):
        if track_id not in self.id_to_index: raise KeyError(f"Unknown track_id: {track_id}")
        idx = self.id_to_index[track_id]
        if candidates is None:
            
            distances, inds = self.knn.kneighbors(self.matrix[idx], n_neighbors=min(len(self.data), 301))
            mapped_track_ids = self.data["track_id"].iloc[inds.ravel()].values
            return pd.Series(1 - distances.ravel(), index=mapped_track_ids).drop(track_id, errors="ignore")
        inds = np.asarray(candidates, dtype=int)
        sims = self.matrix[inds].dot(self.matrix[idx].T).toarray().ravel()
        norms = np.sqrt(self.matrix[inds].multiply(self.matrix[inds]).sum(axis=1)).A1 * np.sqrt(self.matrix[idx].multiply(self.matrix[idx]).sum())
        mapped_candidates = self.data["track_id"].iloc[inds].values
        return pd.Series(np.divide(sims, norms, out=np.zeros_like(sims), where=norms != 0), index=mapped_candidates)

    def recommend_similar_tracks(self, track_id, top_n=10):
        s = self.scores_for_track(track_id).sort_values(ascending=False).head(top_n)
        out = self.data.iloc[s.index][["track_id", "track_name", "artists", "track_genre", "popularity"]].copy()
        out["similarity_score"] = s.values
        return out.reset_index(drop=True)
