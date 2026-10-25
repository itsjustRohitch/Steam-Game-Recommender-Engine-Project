# 🎮 Steam Game Discovery Engine (124,000+ Modern Games)

A production-grade, AI-powered recommender system built with **Python, Scikit-Learn, and Streamlit**. It indexes over **124,000 Steam titles** (including releases like *God of War, Elden Ring, Baldur's Gate 3, Cyberpunk 2077, Black Myth: Wukong*, and cross-platform benchmarks like *Bloodborne* and *Zelda: Breath of the Wild*).

Featuring a **Cyber-Glow & Glassmorphism** web interface, high-dimensional semantic vector search, **Bayesian credibility regularization**, an interactive **Novelty / Serendipity dial**, and full **JSON export capabilities**.

---

## 🌟 Key Features

1. **Massive Modern Catalog (124,146 Games):**
   - Ingested directly from the **FronkonGames Steam Dataset** via Hugging Face.
   - Includes official Steam banner covers (`header_image`), pricing, release dates, and review scores.

2. **Algorithmic Vector Search (TF-IDF + Sublinear Scaling):**
   - Uses `max_df=0.25` domain stop-word filtering to prevent generic categories (`action`, `adventure`, `rpg`) from causing false-positive collisions.
   - Sublinear term-frequency scaling ($1 + \log(\text{tf})$) to prevent short, sparse entries from dominating cosine dot products.

3. **Bayesian Credibility Regularization:**
   - Anchors recommendations to community consensus using a logarithmic credibility prior:
     $$\text{Credibility}(v) = \frac{\log_{10}(1 + v)}{\log_{10}(1 + v) + 1.2}$$
   - Prevents 30-review shovelware from outranking verified, acclaimed blockbusters when seeking mainstream quality.

4. **Novelty & Serendipity Dial (Popularity Bias Mitigation):**
   - Allows users to smoothly transition between **Mainstream Blockbusters** ($\lambda = 0.0$) and **Hidden Indie Gems** ($\lambda \to 1.0$) by penalizing global popularity.

5. **Explainability ("Why This Was Recommended"):**
   - Each card displays the input title that drove the match, mathematical correlation percentage, and exact overlapping sub-genre tags (*Souls-like*, *Dark Fantasy*, *Difficult*, *Action RPG*).

6. **One-Click JSON Export:**
   - Dedicated export button downloading your complete session profile (selected inputs, tuning parameters, recommendations, and similarity scores) as `steam_recommendations_export.json`.

---

## 📁 Repository Structure

```text
├── data/
│   ├── preprocessed_catalog.parquet      # Cleaned catalog (122k titles, 41MB)
│   └── preprocessed_interactions.parquet # Cleaned playtime interactions
│
├── notebooks/
│   └── eda_steam_games.ipynb             # Comprehensive EDA with Seaborn/Matplotlib
│
├── reports/figures/                      # Exported high-resolution charts
│   ├── 01_sentiment_and_reviews.png
│   ├── 02_pricing_landscape.png
│   ├── 03_genre_and_subgenre_intelligence.png
│   ├── 04_long_tail_popularity_curve.png
│   └── 05_playtime_and_confidence.png
│
├── src/
│   ├── data_loader.py                    # Catalog ingestion & TF-IDF indexing
│   ├── recommender.py                   # Vector engine + Bayesian regularizer + Explainability
│   └── evaluate.py                       # Precision@K, Recall@K & Coverage benchmarks
│
├── app.py                                # Cyber-Glow Streamlit web dashboard
├── preprocess.py                         # Standalone data preprocessing pipeline
├── run_eda.py                            # Headless EDA script to generate figures
├── requirements.txt                      # Dependencies (pure Python & Scipy/Sklearn)
├── .gitignore                            # Excludes raw >100MB archives
└── README.md
```

---

## 🚀 Quickstart & Local Setup

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/<YOUR_USERNAME>/<YOUR_REPO_NAME>.git
cd <YOUR_REPO_NAME>
pip install -r requirements.txt
```

### 2. Launch the Streamlit App
```bash
python -m streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## 🧪 Exploratory Data Analysis (EDA)

Run the automated EDA visualization script to generate figures:
```bash
python run_eda.py
```
Or open the interactive Jupyter Notebook at [`notebooks/eda_steam_games.ipynb`](notebooks/eda_steam_games.ipynb).

---

## 🌐 Free Deployment (Streamlit Community Cloud)

1. Push this repository to your GitHub account:
   ```bash
   git add .
   git commit -m "Production release of Steam Game Recommender"
   git push origin main
   ```
2. Navigate to **[share.streamlit.io](https://share.streamlit.io)** and log in with GitHub.
3. Click **"New app"**, select your repository, set the main file to **`app.py`**, and click **Deploy**.
4. Your live app will be accessible at:
   `https://<your-repo-name>.streamlit.app`
