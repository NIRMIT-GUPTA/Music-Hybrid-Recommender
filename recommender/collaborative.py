import numpy as np
import pandas as pd
from scipy import sparse

class ItemCollaborativeFilter:
    """Sparse item-item CF trained only on labelled synthetic demonstration events."""
    def __init__(self, track_ids, matrix, popularity=None):
        self.track_ids = np.asarray(track_ids)
        self.id_to_col = {v:i for i,v in enumerate(self.track_ids)}
        self.col_to_id = {i: v for i, v in enumerate(self.track_ids)}
        self.matrix = matrix.tocsr()
        self.item_popularity = np.asarray(popularity if popularity is not None else self.matrix.sum(axis=0)).ravel()
        norms = np.sqrt(np.asarray(self.matrix.multiply(self.matrix).sum(axis=0)).ravel())
        self.norms = norms

    def scores_for_track(self, track_id, top_k=500):
        if track_id not in self.id_to_col: raise KeyError(f"Unknown track_id: {track_id}")
        col = self.id_to_col[track_id]
        raw = (self.matrix.T @ self.matrix[:, col]).toarray().ravel()
        denom = self.norms * self.norms[col]
        scores = np.divide(raw, denom, out=np.zeros_like(raw, dtype=float), where=denom > 0)
        scores[col] = 0
        inds = np.argpartition(scores, -min(top_k, len(scores)))[-min(top_k, len(scores)):]
        col_to_id = {v: k for k, v in self.id_to_col.items()}
        mapped_track_ids = [col_to_id[i] for i in inds]
        return pd.Series(scores[inds], index=mapped_track_ids)[lambda s: s > 0].sort_values(ascending=False)

    def genre_scores(self, columns):
        # No individual user is fabricated: global synthetic interaction support is used.
        return pd.Series(self.item_popularity[np.asarray(columns)], index=np.asarray(columns))

def simulate_interactions(data, users=600, per_user=45, seed=42):
    rng = np.random.default_rng(seed); n = len(data)
    genres = data.groupby("track_genre").indices
    rows=[]; cols=[]
    for user in range(users):
        fav = rng.choice(list(genres), size=min(3, len(genres)), replace=False)
        pool = np.unique(np.concatenate([genres[g] for g in fav]))
        pop = data.iloc[pool].popularity.to_numpy(float) + 5
        take = min(per_user, len(pool)); chosen = rng.choice(pool, size=take, replace=False, p=pop/pop.sum())
        rows.extend([user]*take); cols.extend(chosen.tolist())
    matrix = sparse.csr_matrix((np.ones(len(rows), dtype=np.float32), (rows, cols)), shape=(users, n))
    return matrix

