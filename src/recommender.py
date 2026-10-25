import numpy as np
from scipy.sparse import csr_matrix
from sklearn.preprocessing import normalize


class SteamRecommender:
    """
    Modern Steam Recommender Engine:
    - High-Dimensional Tag & Genre Vector Similarity across 124,000+ modern games
    - Multi-Criteria Re-ranking (Quality Score, Review Volume, Novelty Slider)
    - Explainability with Exact Tag Overlaps & Semantic Match Percentages
    - Steam Official Box Art & Price Metadata
    """

    def __init__(self, novelty_weight=0.25, random_state=42):
        self.novelty_weight = novelty_weight
        self.random_state = random_state

        self.content_matrix = None
        self.metadata_dict = {}
        self.game_to_idx = {}
        self.idx_to_game = {}
        self.is_fitted = False

    def fit(self, processed_data):
        self.content_matrix = processed_data["content_matrix"]
        self.metadata_dict = processed_data["metadata_dict"]
        self.game_to_idx = processed_data["game_to_idx"]
        self.idx_to_game = processed_data["idx_to_game"]
        self.is_fitted = True
        return self

    def recommend(
        self,
        custom_games_dict=None,
        selected_games=None,
        top_k=10,
        novelty_weight=0.2,
        min_review_score=0.0,
        exclude_known=True
    ):
        """
        Recommends games matching the input profile.
        
        Parameters:
        - selected_games: List of game names.
        - custom_games_dict: Dict of {game_name: weight_or_hours}.
        - top_k: Number of recommendations to return.
        - novelty_weight: [0.0, 1.0]. 0.0 surfaces blockbusters; 1.0 boosts hidden indie gems.
        - min_review_score: Filter by minimum positive review % (e.g., 80% positive).
        """
        if not self.is_fitted:
            raise ValueError("Recommender is not fitted.")

        # Resolve input games
        input_picks = {}
        if custom_games_dict:
            input_picks = custom_games_dict
        elif selected_games:
            input_picks = {g: 1.0 for g in selected_games}

        valid_inputs = {g: w for g, w in input_picks.items() if g in self.game_to_idx}
        known_indices = {self.game_to_idx[g] for g in valid_inputs}

        if not valid_inputs:
            return self._fallback_popular(top_k)

        # Build user profile vector by aggregating normalized content vectors of selected games
        profile_vec = np.zeros(self.content_matrix.shape[1], dtype=np.float32)
        for g_name, weight in valid_inputs.items():
            g_idx = self.game_to_idx[g_name]
            vec = self.content_matrix.getrow(g_idx).toarray().ravel()
            profile_vec += vec * float(weight)

        norm_p = np.linalg.norm(profile_vec)
        if norm_p > 0:
            profile_vec = profile_vec / norm_p

        # Compute cosine similarity across entire catalog: (n_games, n_features) @ (n_features, 1)
        sim_scores = self.content_matrix.dot(profile_vec).ravel()

        # Quality multiplier: boost games with higher positive review percentages
        final_scores = sim_scores.copy()

        for idx in range(len(final_scores)):
            name = self.idx_to_game[idx]
            meta = self.metadata_dict.get(name, {})
            score_pct = meta.get("review_score_pct", 70.0)
            norm_pop = meta.get("norm_popularity", 0.0)

            # Filter out games below minimum review quality threshold
            if score_pct < min_review_score and min_review_score > 0:
                final_scores[idx] = -1.0
                continue

            # 1. Quality factor with Bayesian smoothing to avoid 1-vote 100% bias
            total_revs = meta.get("total_reviews", 0)
            positives = meta.get("positive", 0)
            smoothed_quality = (positives + 25) / (total_revs + 30)
            final_scores[idx] *= (0.75 + 0.25 * smoothed_quality)

            # 2. Bayesian Credibility Regularizer:
            # Scales candidate score by log-volume of reviews to anchor recommendations to games
            # with confirmed player community engagement.
            log_vol = np.log10(1 + total_revs)
            credibility = log_vol / (log_vol + 1.2)
            # Smoothly blend credibility with the novelty slider:
            # When novelty = 0 (mainstream hits), credibility is strictly enforced.
            # When novelty = 1 (hidden indie gems), credibility damping is relaxed.
            effective_credibility = (1.0 - novelty_weight) * credibility + novelty_weight * 1.0
            final_scores[idx] *= max(0.20, effective_credibility)

            # 3. Novelty penalty: dampen high popularity score if slider > 0
            if novelty_weight > 0.0:
                penalty = 1.0 - (novelty_weight * (norm_pop ** 0.5))
                final_scores[idx] *= max(penalty, 0.05)

        # Exclude input games
        if exclude_known:
            for idx in known_indices:
                final_scores[idx] = -1.0

        # Retrieve Top-K
        top_indices = np.argsort(final_scores)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(top_indices, 1):
            if final_scores[idx] <= 0:
                continue

            g_name = self.idx_to_game[idx]
            meta = self.metadata_dict.get(g_name, {})

            # Find which input game shares the highest similarity & tag overlap
            best_source, best_sim, shared_tags = self._explain_match(idx, valid_inputs)

            results.append({
                "rank": rank,
                "game_title": g_name,
                "appID": meta.get("appID", 0),
                "header_image": meta.get("header_image", ""),
                "price": meta.get("price", 0.0),
                "release_date": meta.get("release_date", "N/A"),
                "review_score_pct": meta.get("review_score_pct", 0.0),
                "total_reviews": meta.get("total_reviews", 0),
                "genres": meta.get("genres", ""),
                "tags": meta.get("tags", ""),
                "popularity_tier": self._classify_tier(meta.get("norm_popularity", 0.0)),
                "affinity_score": round(float(final_scores[idx]) * 100, 1),
                "explained_by": best_source,
                "similarity_match": round(best_sim * 100, 1),
                "shared_tags": shared_tags
            })

        return results

    def _explain_match(self, target_idx, valid_inputs):
        """Finds closest input game and extracts overlapping tags."""
        target_name = self.idx_to_game[target_idx]
        target_meta = self.metadata_dict.get(target_name, {})
        target_tags = set([t.strip().lower() for t in target_meta.get("tags", "").split(",") if t.strip()])

        target_vec = self.content_matrix.getrow(target_idx).toarray().ravel()

        best_source = list(valid_inputs.keys())[0]
        best_sim = 0.0
        best_shared = []

        for src_name in valid_inputs:
            src_idx = self.game_to_idx[src_name]
            src_vec = self.content_matrix.getrow(src_idx).toarray().ravel()
            sim = float(np.dot(target_vec, src_vec))

            if sim > best_sim:
                best_sim = sim
                best_source = src_name

                src_meta = self.metadata_dict.get(src_name, {})
                src_tags = set([t.strip().lower() for t in src_meta.get("tags", "").split(",") if t.strip()])
                common = list(target_tags & src_tags)
                # Prioritize distinctive themes over generic noise words
                generic_noise = {"action", "adventure", "rpg", "indie", "casual", "singleplayer", "multiplayer"}
                meaningful = [t for t in common if t not in generic_noise]
                best_shared = [t.title() for t in (meaningful if meaningful else common)[:4]]

        return best_source, best_sim, best_shared

    def _classify_tier(self, norm_pop):
        if norm_pop >= 0.70:
            return "Blockbuster (Mainstream)"
        elif norm_pop >= 0.45:
            return "Popular Favorite"
        elif norm_pop >= 0.20:
            return "Cult Classic"
        else:
            return "Hidden Indie Gem"

    def _fallback_popular(self, top_k):
        """Fallback to top rated, popular titles."""
        sorted_games = sorted(
            self.metadata_dict.items(),
            key=lambda x: x[1].get("total_reviews", 0),
            reverse=True
        )[:top_k]

        return [
            {
                "rank": i + 1,
                "game_title": name,
                "appID": data.get("appID", 0),
                "header_image": data.get("header_image", ""),
                "price": data.get("price", 0.0),
                "release_date": data.get("release_date", "N/A"),
                "review_score_pct": data.get("review_score_pct", 0.0),
                "total_reviews": data.get("total_reviews", 0),
                "genres": data.get("genres", ""),
                "tags": data.get("tags", ""),
                "popularity_tier": "Blockbuster (Mainstream)",
                "affinity_score": 100.0 - i,
                "explained_by": "Top Steam Community Benchmark",
                "similarity_match": 100.0,
                "shared_tags": []
            }
            for i, (name, data) in enumerate(sorted_games)
        ]
