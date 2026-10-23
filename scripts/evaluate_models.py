"""Evaluate on held-out synthetic events; training never sees the held-out cell."""
from pathlib import Path
import sys, joblib
import numpy as np
import pandas as pd
from scipy import sparse
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).parents[1]))
from recommender.preprocessing import load_processed
from recommender.collaborative import ItemCollaborativeFilter
from recommender.hybrid import minmax
from recommender.evaluation import precision_recall_map_ndcg, catalog_coverage
ROOT = Path(__file__).parents[1]

def main():
    data=load_processed(ROOT/'data/processed/tracks.parquet'); x=sparse.load_npz(ROOT/'data/interactions/synthetic_interactions.npz').tolil(); rng=np.random.default_rng(42)
    held=[]
    for u, row in enumerate(x.rows):
        h=int(rng.choice(row)); held.append([h]); pos=row.index(h); row.pop(pos); x.data[u].pop(pos)
    cf=ItemCollaborativeFilter(data.track_id.to_numpy(), x.tocsr()); content=joblib.load(ROOT/'models/content.joblib')
    buckets={'Content':[],'Collaborative':[],'Hybrid':[],'Popularity baseline':[]}
    pop=np.argsort(-data.popularity.to_numpy())[:10].tolist()
    for u in range(min(200, x.shape[0])):
        seeds=x.rows[u]
        if not seeds: continue
        seed = data.track_id.iloc[seeds[0]]
        cs = content.scores_for_track(seed)
        ks = cf.scores_for_track(seed)
        candidates = cs.index.union(ks.index)
        cs_aligned = cs.reindex(candidates).fillna(0)
        ks_aligned = ks.reindex(candidates).fillna(0)
        hy = .5 * minmax(cs_aligned) + .5 * minmax(ks_aligned)
        buckets['Content'].append(cs.head(10).index.tolist()); buckets['Collaborative'].append(ks.head(10).index.tolist())
        buckets['Hybrid'].append(hy.sort_values(ascending=False).head(10).index.tolist()); buckets['Popularity baseline'].append(pop)
    rows=[]
    for name,recs in buckets.items():
        m=precision_recall_map_ndcg(recs, held[:len(recs)])
        m['Catalog coverage']=catalog_coverage(recs,len(data)); m['Model']=name; rows.append(m)
    result=pd.DataFrame(rows).set_index('Model'); result.to_csv(ROOT/'models/evaluation_metrics.csv')
    ax=result[['Precision@10','Recall@10','MAP@10','NDCG@10']].plot.bar(figsize=(9,4), ylim=(0,1), title='Held-out synthetic interaction metrics')
    ax.set_ylabel('score'); plt.tight_layout(); plt.savefig(ROOT/'models/evaluation_chart.png', dpi=150)
    print(result.round(4))
if __name__ == '__main__': main()

