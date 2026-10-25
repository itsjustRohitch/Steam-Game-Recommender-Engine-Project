import os
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PARQUET_FILE = os.path.join(DATA_DIR, "fronkon_games.parquet")
STEAM_200K_FILE = os.path.join(DATA_DIR, "steam-200k.csv")


PREPROCESSED_CATALOG = os.path.join(DATA_DIR, "preprocessed_catalog.parquet")


def load_modern_steam_catalog():
    """
    Loads modern Steam games catalog.
    Prefers preprocessed_catalog.parquet if generated, otherwise falls back to raw parquet.
    """
    if os.path.exists(PREPROCESSED_CATALOG):
        print(f"Loading from preprocessed catalog: {PREPROCESSED_CATALOG}")
        df = pd.read_parquet(PREPROCESSED_CATALOG)
        return df

    if not os.path.exists(PARQUET_FILE):
        raise FileNotFoundError(f"Missing {PARQUET_FILE}. Run download_latest.py first.")

    cols = [
        "appID", "name", "release_date", "price", "header_image",
        "positive", "negative", "estimated_owners", "average_playtime_forever",
        "genres", "tags", "short_description"
    ]

    df = pd.read_parquet(PARQUET_FILE, columns=cols)
    df = df.dropna(subset=["name"]).copy()
    df["name"] = df["name"].astype(str).str.strip()

    # Drop duplicate names keeping the one with higher positive reviews
    df = df.sort_values(by="positive", ascending=False).drop_duplicates(subset=["name"]).reset_index(drop=True)

    # Clean text columns
    df["genres"] = df["genres"].fillna("").astype(str)
    df["tags"] = df["tags"].fillna("").astype(str)
    df["short_description"] = df["short_description"].fillna("").astype(str)

    # Compute review percentage and total review volume
    df["total_reviews"] = df["positive"] + df["negative"]
    df["review_score_pct"] = np.where(
        df["total_reviews"] > 0,
        np.round((df["positive"] / df["total_reviews"]) * 100, 1),
        0.0
    )

    # Combined content soup for TF-IDF / Tag similarity
    df["content_soup"] = (
        (df["tags"] + " ") * 3 +
        (df["genres"] + " ") * 2 +
        df["short_description"]
    ).str.lower().str.replace(r"[^\w\s-]", " ", regex=True)

    return df


def load_and_preprocess_data(min_catalog_reviews=10):
    """
    Combines the latest 124,146 Steam catalog with interaction data,
    building an integrated modern metadata index + content vectorizer.
    """
    catalog_df = load_modern_steam_catalog()

    # We index games that have at least some community presence or notable titles
    # To keep the vector matrix responsive and high-signal (<100ms response)
    popular_mask = (catalog_df["total_reviews"] >= min_catalog_reviews) | (catalog_df["positive"] >= 5)
    active_catalog = catalog_df[popular_mask].copy().reset_index(drop=True)

    # Also make sure cross-platform legends are accessible
    legends = [
        {
            "appID": 999901, "name": "Bloodborne", "release_date": "Mar 24, 2015", "price": 19.99,
            "header_image": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/374320/header.jpg",
            "positive": 150000, "negative": 5000, "total_reviews": 155000, "review_score_pct": 96.8,
            "genres": "Action, RPG", "tags": "Souls-like, Dark Fantasy, Difficult, Action RPG, Lovecraftian, Atmospheric",
            "short_description": "Face your fears as you search for answers in the ancient city of Yharnam, now cursed with a strange endemic illness.",
            "content_soup": "souls-like dark fantasy difficult action rpg lovecraftian atmospheric action rpg bloodborne yharnam hunters"
        },
        {
            "appID": 999902, "name": "The Legend of Zelda: Breath of the Wild", "release_date": "Mar 3, 2017", "price": 59.99,
            "header_image": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/292030/header.jpg",
            "positive": 200000, "negative": 4000, "total_reviews": 204000, "review_score_pct": 98.0,
            "genres": "Action, Adventure, RPG", "tags": "Open World, Exploration, Adventure, Action RPG, Beautiful, Masterpiece",
            "short_description": "Step into a world of discovery, exploration, and adventure in The Legend of Zelda: Breath of the Wild.",
            "content_soup": "open world exploration adventure action rpg beautiful masterpiece fantasy climbing shrines puzzle physics"
        }
    ]

    for leg in legends:
        if leg["name"] not in active_catalog["name"].values:
            active_catalog = pd.concat([active_catalog, pd.DataFrame([leg])], ignore_index=True)

    # Build metadata lookup dict by game name
    metadata_dict = active_catalog.set_index("name").to_dict(orient="index")

    # Build Content TF-IDF matrix with domain noise filtering and sublinear scaling
    print("Vectorizing gameplay descriptions & semantics with max_df=0.25 and sublinear_tf...")
    # Add gaming-specific white noise stop words that convey zero subgenre discrimination
    domain_stopwords = [
        "game", "games", "play", "player", "players", "world", "new", "experience",
        "action", "adventure", "rpg", "indie", "casual", "features", "steam",
        "singleplayer", "multiplayer"
    ]
    all_stopwords = list(TfidfVectorizer(stop_words="english").get_stop_words().union(domain_stopwords))

    tfidf = TfidfVectorizer(
        max_features=40000,
        stop_words=all_stopwords,
        ngram_range=(1, 2),
        max_df=0.25,
        min_df=3,
        sublinear_tf=True
    )
    content_matrix = tfidf.fit_transform(active_catalog["content_soup"])
    content_matrix = normalize(content_matrix, norm="l2", axis=1)

    game_to_idx = {name: i for i, name in enumerate(active_catalog["name"])}
    idx_to_game = {i: name for i, name in enumerate(active_catalog["name"])}

    # Popularity metric: log1p of total reviews normalized 0 to 1
    max_rev = np.log1p(active_catalog["total_reviews"].max())
    norm_pops = np.log1p(active_catalog["total_reviews"].values) / (max_rev if max_rev > 0 else 1.0)
    for i, name in enumerate(active_catalog["name"]):
        if name in metadata_dict:
            metadata_dict[name]["norm_popularity"] = float(norm_pops[i])

    print(f"Catalog indexed: {len(active_catalog):,} modern games ready.")

    return {
        "catalog_df": active_catalog,
        "metadata_dict": metadata_dict,
        "content_matrix": content_matrix,
        "game_to_idx": game_to_idx,
        "idx_to_game": idx_to_game,
        "total_catalog_count": len(catalog_df)
    }


if __name__ == "__main__":
    data = load_and_preprocess_data()
    print("Sample indexed games:", list(data["game_to_idx"].keys())[:10])
