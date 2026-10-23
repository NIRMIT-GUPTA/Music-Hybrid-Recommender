import numpy as np
import pandas as pd

def minmax(values):
    values = pd.Series(values, dtype=float).fillna(0)
    span = values.max() - values.min()
    return (values-values.min())/span if span > 0 else pd.Series(0.0, index=values.index)

class HybridRecommender:
    def __init__(self, data, content, collaborative): self.data, self.content, self.collaborative = data.reset_index(drop=True), content, collaborative
    def _rank(self, content_scores, collab_scores, candidates, top_n, alpha=.5, genre=None, seed=None):
        candidates = pd.Index(candidates).unique()
        if genre is not None: candidates = candidates[self.data.iloc[candidates].track_genre.to_numpy() == genre]
        if seed is not None: candidates = candidates[candidates != self.content.id_to_index[seed]]
        c=content_scores.reindex(candidates).fillna(0)
        k=collab_scores.reindex(candidates).fillna(0)
        out = self.data[self.data["track_id"].isin(candidates)][["track_id", "track_name", "artists", "track_genre", "popularity"]].copy()
        out["content_score"] = minmax(c).to_numpy(); out["collaborative_score"] = minmax(k).to_numpy()
        out["hybrid_score"] = alpha*out.content_score + (1-alpha)*out.collaborative_score
        return out.sort_values(["hybrid_score","popularity"], ascending=False).drop_duplicates("track_id").head(top_n).reset_index(drop=True)
    def recommend_by_song(self, track_id, top_n=10, alpha=.6):
        if track_id not in self.content.id_to_index: raise KeyError(f"Unknown track_id: {track_id}")
        cs_initial = self.content.scores_for_track(track_id)
        ks_initial = self.collaborative.scores_for_track(track_id, top_k=200)
        if ks_initial.empty or ks_initial.sum() == 0:
            return self._rank(cs_initial, pd.Series(0.0, index=cs_initial.index), cs_initial.index, top_n, alpha=1.0, seed=track_id)
        candidates = cs_initial.index.union(ks_initial.index)
        candidate_matrix_indices = [self.content.id_to_index[tid] for tid in candidates if tid in self.content.id_to_index]
        cs_full = self.content.scores_for_track(track_id, candidates=candidate_matrix_indices)
        ks_full = ks_initial.reindex(cs_full.index).fillna(0)
        return self._rank(cs_full, ks_full, cs_full.index, top_n, alpha, seed=track_id)        
    def recommend_by_genre(self, genre, top_n=10, alpha=.5):
        if genre not in set(self.data.track_genre): raise KeyError(f"Unknown genre: {genre}")
        candidates = self.data.index[self.data.track_genre == genre]
        # Transparent content score: genre constraint plus scaled popularity.
        cs = pd.Series(self.data.iloc[candidates].popularity.to_numpy(), index=candidates)
        ks = self.collaborative.genre_scores(candidates)
        return self._rank(cs, ks, candidates, top_n, alpha, genre=genre)

