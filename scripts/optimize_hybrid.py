# scripts/optimize_hybrid.py
from pathlib import Path
import sys
import joblib
import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from recommender.preprocessing import load_processed
from recommender.collaborative import ItemCollaborativeFilter
from recommender.hybrid import minmax
from recommender.evaluation import precision_recall_map_ndcg

def main():
    data = load_processed(ROOT / 'data/processed/tracks.parquet')
    x = sparse.load_npz(ROOT / 'data/interactions/synthetic_interactions.npz').tolil()
    content = joblib.load(ROOT / 'models/content.joblib')
    col_to_id = {i: v for i, v in enumerate(data['track_id'].to_numpy())}
    rng = np.random.default_rng(42)
    held = []
    for u, row in enumerate(x.rows):
        if len(row) == 0:
            held.append(-1)
            continue
        h = int(rng.choice(row))
        held.append(h)
        pos = row.index(h)
        row.pop(pos)
        x.data[u].pop(pos)
    cf = ItemCollaborativeFilter(data.track_id.to_numpy(), x.tocsr())
    print("Extracting clean candidate profiles for validation seed tracks...")
    user_seeds = []
    content_scores_list = []
    collab_scores_list = []
    ground_truth = []
    for u in range(min(500, x.shape[0])):
        seeds = x.rows[u]
        if not seeds or held[u] == -1:
            continue
        seed_track_idx = seeds[0] 
        seed_track_id = data['track_id'].iloc[seed_track_idx]
        try:
            cs_initial = content.scores_for_track(seed_track_id)
            ks_initial = cf.scores_for_track(seed_track_id, top_k=200)
            candidates = cs_initial.index.union(ks_initial.index)
            candidate_matrix_indices = [content.id_to_index[tid] for tid in candidates if tid in content.id_to_index]
            cs_full = content.scores_for_track(seed_track_id, candidates=candidate_matrix_indices)
            ks_full = ks_initial.reindex(cs_full.index).fillna(0)
            user_seeds.append(u)
            content_scores_list.append(cs_full)
            collab_scores_list.append(ks_full)
            ground_truth.append([data['track_id'].iloc[held[u]]])
        except Exception as e:
            continue
            
    print(f"Starting parameter search across {len(user_seeds)} valid evaluation track sets...\n")
    print(f"{'Alpha Weight':<15}{'Precision@10':<15}{'Recall@10':<15}{'NDCG@10':<15}")
    best_alpha = 0.5
    best_ndcg = 0.0
    for alpha in np.linspace(0.0, 1.0, 11):
        recommendations = []
        for cs, ks in zip(content_scores_list, collab_scores_list):
            hy = alpha * minmax(cs) + (1 - alpha) * minmax(ks)
            top_recs = hy.sort_values(ascending=False).head(10).index.tolist()
            recommendations.append(top_recs) 
        metrics = precision_recall_map_ndcg(recommendations, ground_truth, k=10)
        p_10 = metrics.get('Precision@10', 0.0)
        r_10 = metrics.get('Recall@10', 0.0)
        n_10 = metrics.get('NDCG@10', 0.0)
        print(f"{alpha:<15.1f}{p_10:<15.4f}{r_10:<15.4f}{n_10:<15.4f}")
        if n_10 > best_ndcg:
            best_ndcg = n_10
            best_alpha = alpha
    print(f"🏆 Optimization Task Complete!")
    print(f"🎯 Optimal Performance Alpha found: {best_alpha:.1f}")
    print(f"📈 Peak Validation NDCG@10 Score:  {best_ndcg:.4f}")
if __name__ == '__main__':
    main()
