import numpy as np
from sklearn.model_selection import train_test_split
from scipy.sparse import csr_matrix


def train_test_split_implicit(user_item_matrix, test_ratio=0.2, random_state=42):
    """
    Masks a fraction of interactions for each user as a holdout test set for evaluation.
    """
    np.random.seed(random_state)
    train_matrix = user_item_matrix.copy().tolil()
    test_interactions = {}

    rows, cols = user_item_matrix.nonzero()
    user_interactions = {}
    for r, c in zip(rows, cols):
        user_interactions.setdefault(r, []).append(c)

    for u_idx, items in user_interactions.items():
        if len(items) >= 4:
            n_test = max(1, int(len(items) * test_ratio))
            test_items = np.random.choice(items, size=n_test, replace=False)
            test_interactions[u_idx] = set(test_items)
            for item in test_items:
                train_matrix[u_idx, item] = 0

    return train_matrix.tocsr(), test_interactions


def evaluate_recommender(recommender, test_interactions, top_k=10, max_eval_users=200, algorithm="Hybrid Ensemble"):
    """
    Evaluates recommender on test users:
    - Precision@K
    - Recall@K
    - Catalog Coverage
    """
    precision_scores = []
    recall_scores = []
    recommended_items = set()

    eval_users = list(test_interactions.keys())[:max_eval_users]

    for u_idx in eval_users:
        ground_truth = test_interactions[u_idx]
        if not ground_truth:
            continue

        uid = recommender.idx_to_user[u_idx]
        recs = recommender.recommend(user_id=uid, algorithm=algorithm, top_k=top_k, exclude_known=True)

        rec_indices = [
            recommender.game_to_idx[r["game_title"]]
            for r in recs
            if r["game_title"] in recommender.game_to_idx
        ]

        hits = len(set(rec_indices) & ground_truth)
        precision = hits / top_k
        recall = hits / len(ground_truth)

        precision_scores.append(precision)
        recall_scores.append(recall)
        recommended_items.update(rec_indices)

    total_catalog = len(recommender.idx_to_game)
    coverage = (len(recommended_items) / total_catalog) * 100 if total_catalog > 0 else 0.0

    return {
        "precision_at_k": float(np.mean(precision_scores)) if precision_scores else 0.0,
        "recall_at_k": float(np.mean(recall_scores)) if recall_scores else 0.0,
        "catalog_coverage_pct": round(coverage, 2),
        "total_evaluated_users": len(eval_users),
        "top_k": top_k
    }
