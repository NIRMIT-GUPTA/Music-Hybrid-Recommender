import numpy as np

def precision_recall_map_ndcg(recommendations, relevant, k=10):
    """Ranking metrics for a list of recommendation lists and held-out item sets."""
    p=[]; r=[]; ap=[]; ndcg=[]
    for rec, truth in zip(recommendations, relevant):
        rec=list(rec)[:k]; truth=set(truth); hits=[x in truth for x in rec]
        p.append(sum(hits)/k); r.append(sum(hits)/max(1,len(truth)))
        ap.append(sum(hit*(sum(hits[:i+1])/(i+1)) for i,hit in enumerate(hits))/max(1,min(k,len(truth))))
        ideal=sum(1/np.log2(i+2) for i in range(min(k,len(truth))))
        ndcg.append(sum(hit/np.log2(i+2) for i,hit in enumerate(hits))/max(1e-12,ideal))
    return {'Precision@'+str(k):np.mean(p), 'Recall@'+str(k):np.mean(r), 'MAP@'+str(k):np.mean(ap), 'NDCG@'+str(k):np.mean(ndcg)}

def catalog_coverage(recommendations, catalog_size):
    return len(set().union(*(set(x) for x in recommendations)))/max(1,catalog_size)

def diversity(recommendations, similarity):
    """Mean 1 - similarity across recommendation pairs."""
    values=[]
    for row in recommendations:
        for i,a in enumerate(row):
            for b in row[i+1:]: values.append(1-similarity(a,b))
    return float(np.mean(values)) if values else 0.0
