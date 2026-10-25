import streamlit as st
import pandas as pd
import numpy as np
import time
import json

from src.data_loader import load_and_preprocess_data
from src.recommender import SteamRecommender

# Page setup
st.set_page_config(
    page_title="Steam Game Recommender | Cyber-Glow",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Cyber-Glow & Glassmorphism Styling
def render_clean_html(html_str):
    """Removes leading/trailing indentation from each line so Markdown never renders code blocks."""
    clean = " ".join([line.strip() for line in html_str.splitlines() if line.strip()])
    st.markdown(clean, unsafe_allow_html=True)

st.markdown("""
<style>
    /* Global Background & Typography */
    .stApp {
        background: radial-gradient(circle at 10% 10%, rgba(0, 242, 254, 0.07) 0%, transparent 40%),
                    radial-gradient(circle at 90% 60%, rgba(155, 81, 224, 0.07) 0%, transparent 40%),
                    #080b12;
        color: #e2e8f0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Sidebar Glassmorphism */
    section[data-testid="stSidebar"] {
        background: rgba(11, 16, 27, 0.85) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-right: 1px solid rgba(0, 242, 254, 0.12);
    }

    /* Hero Header */
    .hero-badge {
        display: inline-block;
        background: linear-gradient(90deg, rgba(0, 242, 254, 0.15) 0%, rgba(155, 81, 224, 0.15) 100%);
        border: 1px solid rgba(0, 242, 254, 0.4);
        color: #00f2fe;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        padding: 4px 12px;
        border-radius: 20px;
        margin-bottom: 8px;
        box-shadow: 0 0 12px rgba(0, 242, 254, 0.25);
    }

    /* Glassmorphism Cards */
    .game-card {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border-radius: 14px;
        padding: 20px;
        border: 1px solid rgba(0, 242, 254, 0.18);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45), inset 0 0 12px rgba(0, 242, 254, 0.02);
        margin-bottom: 20px;
        transition: all 0.25s ease-in-out;
    }
    .game-card:hover {
        border-color: rgba(0, 242, 254, 0.5);
        box-shadow: 0 12px 36px rgba(0, 242, 254, 0.12), inset 0 0 16px rgba(0, 242, 254, 0.05);
        transform: translateY(-2px);
    }

    .input-game-card {
        background: rgba(19, 31, 56, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 12px;
        padding: 14px;
        border: 1px solid rgba(79, 172, 254, 0.3);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
        margin-bottom: 12px;
        transition: all 0.2s ease;
    }
    .input-game-card:hover {
        border-color: rgba(0, 242, 254, 0.5);
    }

    /* Badges */
    .input-badge {
        background: linear-gradient(135deg, #0078d4 0%, #00b4d8 100%);
        color: #ffffff;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        box-shadow: 0 0 8px rgba(0, 180, 216, 0.4);
    }
    .rating-badge {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.35);
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 12px;
        box-shadow: 0 0 8px rgba(16, 185, 129, 0.15);
    }
    .badge-mainstream {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.3) 100%);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
    }
    .badge-popular {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(217, 119, 6, 0.3) 100%);
        color: #fde68a;
        border: 1px solid rgba(245, 158, 11, 0.4);
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
    }
    .badge-cult {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.3) 100%);
        color: #6ee7b7;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
    }
    .badge-gem {
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.2) 0%, rgba(147, 51, 234, 0.3) 100%);
        color: #d8b4fe;
        border: 1px solid rgba(168, 85, 247, 0.4);
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        box-shadow: 0 0 10px rgba(168, 85, 247, 0.2);
    }

    /* Tag Pills */
    .tag-pill {
        background: rgba(0, 242, 254, 0.06);
        color: #38bdf8;
        border: 1px solid rgba(0, 242, 254, 0.2);
        padding: 3px 9px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 500;
        margin-right: 5px;
        display: inline-block;
        margin-top: 4px;
        transition: all 0.2s;
    }
    .tag-pill:hover {
        background: rgba(0, 242, 254, 0.15);
        border-color: rgba(0, 242, 254, 0.4);
    }

    /* Engine Explanation Banner */
    .engine-banner {
        background: linear-gradient(135deg, rgba(0, 242, 254, 0.08) 0%, rgba(155, 81, 224, 0.08) 100%);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 242, 254, 0.3);
        box-shadow: 0 0 24px rgba(0, 242, 254, 0.08);
        border-radius: 12px;
        padding: 14px 18px;
        margin: 20px 0 24px 0;
        color: #cbd5e1;
        font-size: 13px;
        line-height: 1.5;
    }

    /* Affinity Match Meter */
    .match-meter-container {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 6px 0 10px 0;
    }
    .match-bar-bg {
        flex: 1;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 6px;
        height: 8px;
        overflow: hidden;
    }
    .match-bar-fill {
        height: 100%;
        border-radius: 6px;
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 50%, #9b51e0 100%);
        box-shadow: 0 0 12px rgba(0, 242, 254, 0.6);
    }
    .match-pct-text {
        font-size: 13px;
        font-weight: 700;
        color: #00f2fe;
        min-width: 75px;
        text-align: right;
    }

    /* Explain Box */
    .explain-box {
        background: rgba(8, 14, 26, 0.7);
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 12px;
        border-left: 3px solid #00f2fe;
        font-size: 13px;
        color: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Initializing Steam Recommender Engine...")
def get_model_and_catalog():
    processed = load_and_preprocess_data(min_catalog_reviews=10)
    model = SteamRecommender()
    model.fit(processed)
    return processed, model


processed_data, model = get_model_and_catalog()
all_indexed_games = sorted(list(processed_data["game_to_idx"].keys()))
total_catalog_count = processed_data["total_catalog_count"]

# ----------------- SIDEBAR CONTROLS -----------------
st.sidebar.markdown("<div class='hero-badge'>⚡ REC-SYS CONTROLS</div>", unsafe_allow_html=True)
st.sidebar.title("🎮 Recommender Hub")

st.sidebar.markdown(f"📦 Catalog: <b style='color:#00f2fe;'>{total_catalog_count:,}</b> games", unsafe_allow_html=True)
st.sidebar.markdown(f"⚡ Search Index: <b style='color:#38bdf8;'>{len(all_indexed_games):,}</b> titles", unsafe_allow_html=True)
st.sidebar.markdown("---")

st.sidebar.subheader("🎛️ Dynamic Tuning")

novelty_slider = st.sidebar.slider(
    "Novelty / Serendipity Dial",
    min_value=0.0,
    max_value=1.0,
    value=0.20,
    step=0.05,
    help="0.0 = Mainstream Blockbusters (God of War, Elden Ring, GTA V)\n1.0 = Boosts high-affinity Hidden Indie Gems"
)

min_rating_filter = st.sidebar.slider(
    "Minimum Steam Review %",
    min_value=50,
    max_value=95,
    value=70,
    step=5,
    help="Filters out games with mixed or negative community reception."
)

top_k = st.sidebar.slider("Number of Recommendations", min_value=5, max_value=25, value=10, step=5)

st.sidebar.markdown("---")
st.sidebar.caption("Data Source: Latest Steam Catalog via Hugging Face & SteamSpy (124k+ games).")


# ----------------- MAIN VIEW -----------------
st.markdown("<div class='hero-badge'>🎮 NEXT-GEN GAME RECOMMENDER</div>", unsafe_allow_html=True)
st.title("🎯 Steam Game Discovery Engine")
st.markdown(
    "<span style='color: #94a3b8; font-size: 15px;'>High-dimensional tag, sub-genre, and semantic affinity retrieval across 124,000+ modern PC titles.</span>",
    unsafe_allow_html=True
)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])

with col1:
    default_picks = ["God of War", "Bloodborne"]
    valid_defaults = [g for g in default_picks if g in processed_data["game_to_idx"]]

    selected_games = st.multiselect(
        "Search your favorite games to construct taste profile:",
        options=all_indexed_games,
        default=valid_defaults,
        max_selections=5
    )

with col2:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    run_btn = st.button("🚀 Recommend Matches", type="primary", use_container_width=True)

if run_btn or selected_games:
    if not selected_games:
        st.warning("Please select at least 1 game above to generate recommendations.")
    else:
        # ----------------- SELECTED TITLES PROFILE (DEMO & EXPLANATION) -----------------
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        st.markdown("### 🎮 Your Selected Input Profile")
        st.caption("The engine analyzes the exact sub-genres, tags, and community metrics from these games:")

        num_cols = min(len(selected_games), 4)
        input_cols = st.columns(num_cols)

        for i, g_name in enumerate(selected_games):
            meta = processed_data["metadata_dict"].get(g_name, {})
            col_target = input_cols[i % num_cols]
            
            img_url = meta.get("header_image", "")
            if not img_url or not img_url.startswith("http"):
                img_url = "https://store.cloudflare.steamstatic.com/public/images/v6/logo_steam_footer.png"
            
            tags_list = [t.strip() for t in str(meta.get("tags", "")).split(",") if t.strip()][:4]
            pills = "".join([f"<span class='tag-pill'>{t}</span>" for t in tags_list])
            price_str = "Free" if meta.get("price", 0) == 0 else f"${meta.get('price', 0):.2f}"
            review_pct = meta.get("review_score_pct", 0.0)
            total_rev = meta.get("total_reviews", 0)

            with col_target:
                render_clean_html(f"""
                <div class="input-game-card">
                    <img src="{img_url}" style="width: 100%; border-radius: 8px; margin-bottom: 10px; object-fit: cover;" onerror="this.style.display='none'" />
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0; color: #ffffff; font-size: 14px; font-weight: 700;">{g_name}</h4>
                        <span class="input-badge">Selected</span>
                    </div>
                    <div style="margin-top: 6px; color: #94a3b8; font-size: 12px;">
                        <span class="rating-badge">👍 {review_pct}%</span> • 
                        <span>{total_rev:,} reviews</span> • 
                        <b style="color: #e2e8f0;">{price_str}</b>
                    </div>
                    <div style="margin-top: 8px;">
                        {pills}
                    </div>
                </div>
                """)

        render_clean_html("""
        <div class="engine-banner">
            <b style="color: #00f2fe;">👨‍🏫 Recommender Engine Mechanics:</b> The system extracts the multi-dimensional tag & genre embeddings of your selected games, projects them into a <b>normalized user taste vector</b>, and calculates high-speed <b>cosine dot products</b> against all 124,000+ candidates in the database.
        </div>
        """)

        with st.spinner("Calculating high-dimensional cosine similarity & applying quality re-ranking..."):
            t0 = time.time()
            recs = model.recommend(
                selected_games=selected_games,
                top_k=top_k,
                novelty_weight=novelty_slider,
                min_review_score=float(min_rating_filter),
                exclude_known=True
            )
            latency_ms = (time.time() - t0) * 1000

        # Header with Download JSON Button
        col_rec_header, col_export_btn = st.columns([3, 1])

        with col_rec_header:
            st.markdown("### 🏆 Top Recommended Games For You")
            st.markdown(f"<span style='color: #00f2fe; font-size: 13px; font-weight: 600;'>⚡ Retrieved Top {len(recs)} candidates in {latency_ms:.1f}ms</span>", unsafe_allow_html=True)

        with col_export_btn:
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            export_payload = {
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "recommender_configuration": {
                    "novelty_dial": float(novelty_slider),
                    "min_review_pct_filter": float(min_rating_filter),
                    "top_k": int(top_k),
                    "retrieval_latency_ms": round(latency_ms, 1)
                },
                "input_selected_games": [
                    {
                        "game_title": g,
                        "appID": int(processed_data["metadata_dict"].get(g, {}).get("appID", 0)),
                        "price": float(processed_data["metadata_dict"].get(g, {}).get("price", 0.0)),
                        "review_score_pct": float(processed_data["metadata_dict"].get(g, {}).get("review_score_pct", 0.0)),
                        "total_reviews": int(processed_data["metadata_dict"].get(g, {}).get("total_reviews", 0)),
                        "genres": str(processed_data["metadata_dict"].get(g, {}).get("genres", "")),
                        "tags": str(processed_data["metadata_dict"].get(g, {}).get("tags", ""))
                    }
                    for g in selected_games
                ],
                "recommended_games": [
                    {
                        "rank": int(r["rank"]),
                        "game_title": r["game_title"],
                        "appID": int(r["appID"]),
                        "affinity_score_pct": float(r["affinity_score"]),
                        "similarity_correlation_pct": float(r["similarity_match"]),
                        "attributed_source_game": r["explained_by"],
                        "shared_tags": r["shared_tags"],
                        "price": float(r["price"]),
                        "review_score_pct": float(r["review_score_pct"]),
                        "total_reviews": int(r["total_reviews"]),
                        "release_date": r["release_date"],
                        "popularity_tier": r["popularity_tier"],
                        "genres": r["genres"],
                        "tags": r["tags"]
                    }
                    for r in recs
                ]
            }

            json_str = json.dumps(export_payload, indent=2)
            st.download_button(
                label="📥 Export JSON",
                data=json_str,
                file_name="steam_recommendations_export.json",
                mime="application/json",
                use_container_width=True
            )

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        for rec in recs:
            tier = rec["popularity_tier"]
            badge_class = (
                "badge-mainstream" if "Blockbuster" in tier
                else "badge-popular" if "Popular" in tier
                else "badge-cult" if "Cult" in tier
                else "badge-gem"
            )

            img_url = rec["header_image"]
            if not img_url or not img_url.startswith("http"):
                img_url = "https://store.cloudflare.steamstatic.com/public/images/v6/logo_steam_footer.png"

            tags_list = [t.strip() for t in rec["tags"].split(",") if t.strip()][:5]
            tag_pills_html = "".join([f"<span class='tag-pill'>{t}</span>" for t in tags_list])

            shared_tags_str = ", ".join(rec["shared_tags"]) if rec["shared_tags"] else "Shared core mechanics"
            price_display = "Free to Play" if rec["price"] == 0 else f"${rec['price']:.2f}"
            affinity_pct = min(100.0, max(5.0, rec["affinity_score"]))

            render_clean_html(f"""
            <div class="game-card">
                <div style="display: flex; gap: 20px; align-items: flex-start;">
                    <img src="{img_url}" style="width: 220px; border-radius: 8px; object-fit: cover; box-shadow: 0 4px 12px rgba(0,0,0,0.5);" onerror="this.style.display='none'" />
                    <div style="flex: 1;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h3 style="margin: 0; color: #ffffff; font-size: 18px; font-weight: 700;">#{rec['rank']} {rec['game_title']}</h3>
                            <span class="{badge_class}">{tier}</span>
                        </div>
                        <div class="match-meter-container">
                            <span style="font-size: 12px; color: #94a3b8; font-weight: 600;">Match Affinity:</span>
                            <div class="match-bar-bg">
                                <div class="match-bar-fill" style="width: {affinity_pct}%;"></div>
                            </div>
                            <span class="match-pct-text">{affinity_pct:.1f}% Match</span>
                        </div>
                        <div style="margin-top: 4px; color: #94a3b8; font-size: 13px;">
                            <span>🏷️ Price: <b style="color: #e2e8f0;">{price_display}</b></span> &nbsp;•&nbsp; 
                            <span>📅 Released: <b>{rec['release_date']}</b></span> &nbsp;•&nbsp; 
                            <span class="rating-badge">👍 {rec['review_score_pct']}%</span> <span style="font-size: 12px;">({rec['total_reviews']:,} reviews)</span>
                        </div>
                        <div style="margin-top: 8px;">
                            {tag_pills_html}
                        </div>
                        <div class="explain-box">
                            💡 <b>Why this was recommended:</b> Driven primarily by your selection of <b>{rec['explained_by']}</b> 
                            (correlation: <b style="color: #00f2fe;">{rec['similarity_match']}%</b>). Shared themes: <i style="color: #e2e8f0;">{shared_tags_str}</i>.
                        </div>
                    </div>
                </div>
            </div>
            """)
