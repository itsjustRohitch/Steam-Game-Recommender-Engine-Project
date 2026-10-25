import os
from collections import Counter
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports", "figures")
os.makedirs(REPORTS_DIR, exist_ok=True)

CATALOG_PATH = os.path.join(DATA_DIR, "preprocessed_catalog.parquet")
INTERACTIONS_PATH = os.path.join(DATA_DIR, "preprocessed_interactions.parquet")

plt.style.use("dark_background")
plt.rcParams["font.size"] = 11
plt.rcParams["figure.titlesize"] = 14
plt.rcParams["figure.titleweight"] = "bold"

print("Loading preprocessed datasets...")
catalog_df = pd.read_parquet(CATALOG_PATH)
interactions_df = pd.read_parquet(INTERACTIONS_PATH)

print(f"Catalog: {len(catalog_df):,} titles")
print(f"Interactions: {len(interactions_df):,} interactions")

# -------------------------------------------------------------
# 1. Sentiment & Review Distribution
# -------------------------------------------------------------
print("Generating Chart 1: Sentiment & Review Distribution...")
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
reviewed_games = catalog_df[catalog_df["total_reviews"] >= 20]

sns.histplot(reviewed_games["review_score_pct"], bins=40, kde=True, ax=axes[0], color="#66c0f4")
axes[0].set_title("Distribution of Positive Review % (Min 20 Reviews)", pad=12)
axes[0].set_xlabel("Positive Reviews Percentage (%)")
axes[0].set_ylabel("Number of Games")
axes[0].axvline(reviewed_games["review_score_pct"].median(), color="#e1b12c", linestyle="--", label=f"Median: {reviewed_games['review_score_pct'].median():.1f}%")
axes[0].legend()

top_reviewed = catalog_df.nlargest(15, "total_reviews")
sns.barplot(data=top_reviewed, y="name", x="total_reviews", ax=axes[1], hue="name", legend=False, palette="crest_r")
axes[1].set_title("Top 15 Most Reviewed Games on Steam", pad=12)
axes[1].set_xlabel("Total Reviews (Positive + Negative)")
axes[1].set_ylabel("")

plt.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, "01_sentiment_and_reviews.png"), dpi=200)
plt.close(fig)

# -------------------------------------------------------------
# 2. Pricing Landscape
# -------------------------------------------------------------
print("Generating Chart 2: Pricing Landscape...")
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
free_counts = catalog_df["is_free"].value_counts()
labels = ["Paid Games", "Free-to-Play"]
colors = ["#2a475e", "#66c0f4"]
axes[0].pie(free_counts, labels=labels, autopct="%1.1f%%", startangle=140, colors=colors, explode=(0, 0.08))
axes[0].set_title("Share of Free vs. Paid Games in Catalog", pad=12)

paid_games = catalog_df[catalog_df["price"] > 0]
order = ["Under $10", "$10 - $30", "$30 - $60", "AAA Premium ($60+)"]
sns.countplot(data=paid_games, x="price_category", order=order, ax=axes[1], hue="price_category", legend=False, palette="viridis")
axes[1].set_title("Price Category Breakdown (Paid Games)", pad=12)
axes[1].set_xlabel("Price Bracket")
axes[1].set_ylabel("Number of Titles")

plt.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, "02_pricing_landscape.png"), dpi=200)
plt.close(fig)

# -------------------------------------------------------------
# 3. GENRE & SUBGENRE INTELLIGENCE (Replaces generic tag list)
# -------------------------------------------------------------
print("Generating Chart 3: Genre & Sub-Genre Intelligence...")
# Focus on core distinct sub-genres and gameplay mechanics
KEY_SUBGENRES = [
    "Souls-like", "Roguelike", "Deckbuilder", "Metroidvania", "Open World",
    "Survival Horror", "Psychological Horror", "Cyberpunk", "Dark Fantasy",
    "Sci-Fi", "Turn-Based", "Hack and Slash", "Co-op", "Story Rich",
    "City Builder", "FPS", "Stealth", "Crafting"
]

# A: Build Co-Occurrence Matrix
subgenre_matrix = pd.DataFrame(0, index=KEY_SUBGENRES, columns=KEY_SUBGENRES)

# Pre-extract tags list for fast co-occurrence
tags_series = catalog_df["tags"].dropna().apply(lambda x: [t.strip() for t in str(x).split(",") if t.strip()])

# Filter for games having at least 1 key subgenre
for tags in tags_series:
    present = [g for g in KEY_SUBGENRES if g in tags]
    for g1 in present:
        for g2 in present:
            subgenre_matrix.loc[g1, g2] += 1

# Normalize co-occurrence to Jaccard-like or conditional probability: P(g2 | g1)
diag = np.diag(subgenre_matrix)
corr_matrix = subgenre_matrix.div(diag, axis=0).fillna(0.0)

# B: Compute Community Satisfaction (% Positive Reviews) per Subgenre
satisfaction_data = []
for sg in KEY_SUBGENRES:
    matches = catalog_df[catalog_df["tags"].str.contains(sg, na=False, case=False)]
    matches_reviewed = matches[matches["total_reviews"] >= 15]
    if len(matches_reviewed) > 0:
        satisfaction_data.append({
            "Subgenre": sg,
            "Median_Rating_Pct": matches_reviewed["review_score_pct"].median(),
            "Game_Count": len(matches)
        })

sat_df = pd.DataFrame(satisfaction_data).sort_values(by="Median_Rating_Pct", ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(18, 8))

# Panel 1: Co-Occurrence Heatmap
sns.heatmap(
    corr_matrix,
    cmap="mako",
    ax=axes[0],
    cbar_kws={"label": "Co-Occurrence Affinity P(Column | Row)"},
    linewidths=0.5,
    linecolor="#11161d"
)
axes[0].set_title("Sub-Genre Co-Occurrence Heatmap (Recommender Feature Clusters)", pad=14)
axes[0].set_xticklabels(axes[0].get_xticklabels(), rotation=45, ha="right", fontsize=10)
axes[0].set_yticklabels(axes[0].get_yticklabels(), rotation=0, fontsize=10)

# Panel 2: Community Satisfaction Ranking
sns.barplot(
    data=sat_df,
    y="Subgenre",
    x="Median_Rating_Pct",
    ax=axes[1],
    hue="Subgenre",
    legend=False,
    palette="flare"
)
axes[1].set_title("Player Satisfaction by Sub-Genre (Median % Positive Reviews)", pad=14)
axes[1].set_xlabel("Median Positive Review Score (%)")
axes[1].set_ylabel("")
axes[1].set_xlim(60, 100)
for p in axes[1].patches:
    val = p.get_width()
    axes[1].annotate(f"{val:.1f}%", (val + 0.5, p.get_y() + p.get_height() / 2),
                     ha="left", va="center", fontsize=9, color="#ffffff")

plt.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, "03_genre_and_subgenre_intelligence.png"), dpi=200)
# Also overwrite the old top tags file so any references resolve cleanly
fig.savefig(os.path.join(REPORTS_DIR, "03_top_steam_tags.png"), dpi=200)
plt.close(fig)

# -------------------------------------------------------------
# 4. Long-Tail Concentration Curve
# -------------------------------------------------------------
print("Generating Chart 4: Long-Tail Concentration Curve...")
sorted_reviews = catalog_df["total_reviews"].sort_values(ascending=False).reset_index(drop=True)
cum_reviews = sorted_reviews.cumsum() / sorted_reviews.sum() * 100
percent_catalog = (np.arange(1, len(sorted_reviews) + 1) / len(sorted_reviews)) * 100

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(percent_catalog, cum_reviews, color="#66c0f4", linewidth=2.5, label="Cumulative Review Concentration")
ax.plot([0, 100], [0, 100], color="#8ba2b5", linestyle="--", label="Uniform Equality Baseline")

top_1_pct_index = int(len(sorted_reviews) * 0.01)
top_1_pct_share = cum_reviews.iloc[top_1_pct_index]
ax.scatter([1.0], [top_1_pct_share], color="#c23616", s=80, zorder=5)
ax.annotate(f"Top 1% of games capture {top_1_pct_share:.1f}% of all reviews!",
            xy=(1.0, top_1_pct_share), xytext=(12, top_1_pct_share - 10),
            arrowprops=dict(facecolor="#c23616", shrink=0.08), fontsize=11, color="#ffffff")

ax.set_title("The Long-Tail Curve: Cumulative Attention Concentration on Steam", pad=15)
ax.set_xlabel("% of Catalog Games (Ranked from Most to Least Popular)")
ax.set_ylabel("Cumulative % of Total Steam Reviews")
ax.legend(loc="lower right")
ax.grid(True, alpha=0.2)

plt.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, "04_long_tail_popularity_curve.png"), dpi=200)
plt.close(fig)

# -------------------------------------------------------------
# 5. Playtime & Implicit Confidence
# -------------------------------------------------------------
print("Generating Chart 5: Playtime & Implicit Confidence...")
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

sns.histplot(interactions_df["hours"], bins=50, log_scale=True, ax=axes[0], color="#9c88ff")
axes[0].set_title("Playtime Hours Distribution (Log Scale)", pad=12)
axes[0].set_xlabel("Playtime (Hours, log-scaled)")
axes[0].set_ylabel("Number of Interactions")
axes[0].axvline(interactions_df["hours"].median(), color="#e1b12c", linestyle="--", label=f"Median: {interactions_df['hours'].median():.1f} hrs")
axes[0].legend()

sns.histplot(interactions_df["confidence"], bins=50, ax=axes[1], color="#44bd32")
axes[1].set_title("Engine Confidence Transformation: c_ui = 1 + alpha * log(1 + hours)", pad=12)
axes[1].set_xlabel("Implicit Feedback Confidence Score")
axes[1].set_ylabel("Interaction Frequency")

plt.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, "05_playtime_and_confidence.png"), dpi=200)
plt.close(fig)

print("All charts updated successfully in reports/figures/!")
