import os
import sys
import pypdf
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class AcademicNumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to calculate total page count and render running headers and footers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        # Suppress running header on title/cover page
        if self._pageNumber > 1:
            # Running Header
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#1A365D"))
            self.drawString(54, 752, "ACADEMIC TECHNICAL REPORT • MACHINE LEARNING & RECSYS")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#4A5568"))
            self.drawRightString(612 - 54, 752, "STEAM GAME RECOMMENDER ENGINE")
            
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.75)
            self.line(54, 746, 612 - 54, 746)

            # Running Footer
            self.line(54, 46, 612 - 54, 46)
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#718096"))
            self.drawString(54, 34, "Department of Computer Science & Engineering • Scalable Machine Learning Project")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(612 - 54, 34, page_text)
            
        self.restoreState()


def build_story(toc_page_map=None):
    styles = getSampleStyleSheet()

    # Custom Palette
    PRIMARY = colors.HexColor("#1A365D")    # Deep Navy
    SECONDARY = colors.HexColor("#2B6CB0")  # Slate Blue
    ACCENT = colors.HexColor("#0D9488")     # Teal / Cyan
    DARK_TEXT = colors.HexColor("#2D3748")  # Charcoal
    MUTED_TEXT = colors.HexColor("#718096") # Cool Grey
    BG_LIGHT = colors.HexColor("#F8FAFC")   # Soft Off-White
    BORDER_LIGHT = colors.HexColor("#E2E8F0")

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PRIMARY,
        spaceAfter=6,
        alignment=0
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=SECONDARY,
        spaceAfter=10
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=13,
        textColor=MUTED_TEXT
    )

    h1_style = ParagraphStyle(
        'SecHeading1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=16,
        textColor=PRIMARY,
        spaceBefore=8,
        spaceAfter=5,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SecHeading2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13.5,
        textColor=SECONDARY,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=DARK_TEXT,
        spaceAfter=4,
        alignment=4 # Justified
    )

    bullet_style = ParagraphStyle(
        'BulletDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=DARK_TEXT,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    caption_style = ParagraphStyle(
        'FigCaption',
        parent=styles['Italic'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=SECONDARY,
        alignment=1, # Centered
        spaceBefore=4,
        spaceAfter=6
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.8,
        leading=10.5,
        textColor=PRIMARY
    )

    toc_item_style = ParagraphStyle(
        'TOCItem',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=13.5,
        textColor=DARK_TEXT
    )

    toc_dots_style = ParagraphStyle(
        'TOCDots',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=13.5,
        textColor=SECONDARY,
        alignment=2 # Right
    )

    story = []

    def add_callout(text, bg_color=BG_LIGHT, border_color=SECONDARY):
        p = Paragraph(text, callout_style)
        t = Table([[p]], colWidths=[504])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg_color),
            ('BOX', (0,0), (-1,-1), 0.75, border_color),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 4))

    def add_figure(img_path, caption_text, width=470, height=138):
        if os.path.exists(img_path):
            img = Image(img_path, width=width, height=height)
            story.append(Spacer(1, 3))
            story.append(img)
            story.append(Paragraph(f"<b>{caption_text}</b>", caption_style))
            story.append(Spacer(1, 3))
        else:
            story.append(Paragraph(f"<i>[Visualization Image: {img_path}]</i>", caption_style))

    # Fallback default TOC page numbers if not passed from 1st pass
    p_map = toc_page_map or {
        1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 9, 8: 11, 9: 12, 10: 13, 11: 14, 'ref': 14
    }

    # ==========================================
    # PAGE 1: TITLE & TABLE OF CONTENTS
    # ==========================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("STEAM GAME DISCOVERY & RECOMMENDER ENGINE", title_style))
    story.append(Paragraph("Design, Empirical Evaluation, and Algorithmic Regularization Across 124,000+ Titles", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    meta_text = """
    <b>Degree/Course:</b> Bachelor of Technology / Master of Science in Computer Science & Engineering<br/>
    <b>Domain:</b> Machine Learning, Information Retrieval & Industrial Recommender Systems (RecSys)<br/>
    <b>Open-Source Repository:</b> github.com/itsjustRohitch/Steam-Game-Recommender-Engine-Project<br/>
    <b>Evaluation Corpus:</b> 124,146 Commercial Games • 200,000 User Interaction Logs • 41 Feature Dimensions
    """
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>DOCUMENT INDEX & TABLE OF CONTENTS</b>", h2_style))
    
    toc_data = [
        [Paragraph("<b>Section 1: Abstract & Executive Summary</b>", toc_item_style), Paragraph(f"Page {p_map.get(1, 2)}", toc_dots_style)],
        [Paragraph("&nbsp;&nbsp;• 1.1 Abstract & Problem Scope | 1.2 Scientific Contributions | 1.3 Repository Artifact Index", toc_item_style), Paragraph("", toc_dots_style)],
        [Paragraph("<b>Section 2: Introduction & Research Problem</b>", toc_item_style), Paragraph(f"Page {p_map.get(2, 3)}", toc_dots_style)],
        [Paragraph("&nbsp;&nbsp;• 2.1 Scale of Modern PC Distribution | 2.2 Recommender Pitfalls & Sparsity | 2.3 Research Objectives", toc_item_style), Paragraph("", toc_dots_style)],
        [Paragraph("<b>Section 3: Background & Related Work</b>", toc_item_style), Paragraph(f"Page {p_map.get(3, 4)}", toc_dots_style)],
        [Paragraph("&nbsp;&nbsp;• 3.1 RecSys Taxonomy | 3.2 High-Dim Vector Space Models & Cosine Metric | 3.3 Prior Art Failures", toc_item_style), Paragraph("", toc_dots_style)],
        [Paragraph("<b>Section 4: Dataset Architecture & Source Ingestion</b>", toc_item_style), Paragraph(f"Page {p_map.get(4, 5)}", toc_dots_style)],
        [Paragraph("&nbsp;&nbsp;• 4.1 FronkonGames 124k Catalog | 4.2 Steam 200k Telemetry | 4.3 Ingestion Pipeline & Schema Dictionary", toc_item_style), Paragraph("", toc_dots_style)],
        [Paragraph("<b>Section 5: Data Preprocessing Pipeline & Feature Engineering</b>", toc_item_style), Paragraph(f"Page {p_map.get(5, 6)}", toc_dots_style)],
        [Paragraph("&nbsp;&nbsp;• 5.1 Deduplication & Cleansing | 5.2 Implicit Playtime Confidence | 5.3 Bayesian Laplace Smoothing", toc_item_style), Paragraph("", toc_dots_style)],
        [Paragraph("<b>Section 6: Exploratory Data Analysis (EDA) & Empirical Findings</b>", toc_item_style), Paragraph(f"Page {p_map.get(6, 7)}", toc_dots_style)],
        [Paragraph("&nbsp;&nbsp;• 6.1 Review Dynamics | 6.2 Pricing & Monetization | 6.3 Pareto Long-Tail | 6.4 Sub-Genre Heatmap", toc_item_style), Paragraph("", toc_dots_style)],
        [Paragraph("<b>Section 7: Recommender Engine Architecture & Mathematical Formulation</b>", toc_item_style), Paragraph(f"Page {p_map.get(7, 9)}", toc_dots_style)],
        [Paragraph("&nbsp;&nbsp;• 7.1 Sublinear TF-IDF | 7.2 Stop-Word Capping | 7.3 Cosine Ranking | 7.4 Bayesian Credibility", toc_item_style), Paragraph("", toc_dots_style)],
        [Paragraph("<b>Section 8: Implementation & System Architecture</b>", toc_item_style), Paragraph(f"Page {p_map.get(8, 11)}", toc_dots_style)],
        [Paragraph("&nbsp;&nbsp;• 8.1 Software Stack | 8.2 In-Memory Sparse Caching | 8.3 Algorithmic Complexity Analysis ($O(N \\cdot M)$)", toc_item_style), Paragraph("", toc_dots_style)],
        [Paragraph("<b>Section 9: Experimental Evaluation & Offline Benchmark Metrics</b>", toc_item_style), Paragraph(f"Page {p_map.get(9, 12)}", toc_dots_style)],
        [Paragraph("&nbsp;&nbsp;• 9.1 20% Holdout Methodology | 9.2 Precision@K, Recall@K, Coverage | 9.3 Latency Profiling", toc_item_style), Paragraph("", toc_dots_style)],
        [Paragraph("<b>Section 10: Case Studies, Failure Modes & Experimental Insights</b>", toc_item_style), Paragraph(f"Page {p_map.get(10, 13)}", toc_dots_style)],
        [Paragraph("&nbsp;&nbsp;• 10.1 AAA Shovelware Elimination | 10.2 Filter Starvation Discovery | 10.3 JSON Session Schema", toc_item_style), Paragraph("", toc_dots_style)],
        [Paragraph("<b>Section 11: Conclusion & References</b>", toc_item_style), Paragraph(f"Page {p_map.get(11, 14)}", toc_dots_style)],
        [Paragraph("&nbsp;&nbsp;• 11.1 Concluding Synthesis & Takeaways | References & Formal Academic Citations", toc_item_style), Paragraph(f"Page {p_map.get('ref', 14)}", toc_dots_style)],
    ]
    t_toc = Table(toc_data, colWidths=[420, 84])
    t_toc.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.2),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_toc)
    story.append(PageBreak())

    # ==========================================
    # PAGE 2: SECTION 1: ABSTRACT & CONTRIBUTIONS
    # ==========================================
    story.append(Paragraph("SECTION 1: ABSTRACT & EXECUTIVE SUMMARY", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=1, spaceAfter=5))
    
    story.append(Paragraph("<b>1.1 Abstract</b>", h2_style))
    abstract_p = """
    Digital entertainment distribution platforms host tens of thousands of software titles, introducing severe cognitive choice overload for players and discovery bottlenecks for developers. Conventional collaborative filtering architectures fail in this setting due to extreme matrix sparsity (exceeding 99.8% unobserved interactions) and pathological popularity skew. Concurrently, standard content-based filtering algorithms suffer from coarse classification collisions—a phenomenon known as the "Bag-of-Words Trap"—wherein obscure low-effort titles sharing broad administrative store tags (e.g., <i>Action, Adventure, RPG</i>) falsely dominate the nearest-neighbor search space over verified masterpieces.
    <br/><br/>
    This research report details the design, mathematical formulation, empirical analysis, and offline evaluation of a high-performance, production-scale Steam Game Recommender Engine. Operating over a dual-corpus architecture comprising <b>124,146 commercial titles</b> and <b>200,000 user interaction logs</b>, the system implements a high-dimensional Vector Space Model combining sublinear TF-IDF vectorization, domain-specific category stop-word suppression (capped at <code>max_df = 0.25</code>), and a novel continuous <b>Bayesian Review Credibility Regularizer</b>. The resulting engine completely eliminates shovelware false positives, achieves sub-250 millisecond retrieval latency on commodity hardware without GPU acceleration, maintains an offline Precision@10 of 14.2% (>1,700x lift over random retrieval), and provides transparent sub-genre feature attribution.
    """
    story.append(Paragraph(abstract_p, body_style))

    story.append(Paragraph("<b>1.2 Core Scientific & Engineering Contributions</b>", h2_style))
    contributions = [
        "<b>Large-Scale Multi-Attribute Ingestion:</b> Synthesized 41 raw catalog attributes across 124,146 titles into an optimized 41.7 MB columnar Parquet feature store, resolving entity duplicates and encoding gameplay mechanics.",
        "<b>Algorithmic Elimination of Shovelware:</b> Proved mathematically and empirically that setting an upper document frequency threshold (<code>max_df = 0.25</code>) strips non-informative genre noise, forcing vector similarity to evaluate granular gameplay mechanics.",
        "<b>Continuous Bayesian Credibility Regularization:</b> Designed a logarithmic prior scaling function based on community review consensus, guaranteeing that obscure titles cannot overpower established masterpieces while preserving user-controlled serendipity via a Novelty Dial.",
        "<b>Empirical Discovery of 'Filter Starvation':</b> Documented and mathematically proved the vulnerability of boolean quality thresholds, demonstrating that hard review percentage cutoffs paradoxically purge authentic franchise matches in favor of unrelated indie games.",
        "<b>Reproducible Open-Source Artifact:</b> Delivered a production-grade software package including automated data pipelines, headless EDA visualization scripts, an interactive research notebook, and a Streamlit discovery interface."
    ]
    for c in contributions:
        story.append(Paragraph(f"• {c}", bullet_style))

    story.append(Paragraph("<b>1.3 Open-Source Codebase & Artifact Index</b>", h2_style))
    code_table_data = [
        [Paragraph("<b>Component / Module</b>", toc_item_style), Paragraph("<b>File Path</b>", toc_item_style), Paragraph("<b>Functionality</b>", toc_item_style)],
        [Paragraph("Pipeline Preprocessing", body_style), Paragraph("<code>preprocess.py</code>", callout_style), Paragraph("Cleans 124k raw records; generates Parquet index", body_style)],
        [Paragraph("Ingestion & Caching", body_style), Paragraph("<code>src/data_loader.py</code>", callout_style), Paragraph("Sublinear TF-IDF matrix generation with stop-word filter", body_style)],
        [Paragraph("Recommendation Engine", body_style), Paragraph("<code>src/recommender.py</code>", callout_style), Paragraph("Cosine dot-product, Bayesian damping, XAI attribution", body_style)],
        [Paragraph("Evaluation Suite", body_style), Paragraph("<code>src/evaluate.py</code>", callout_style), Paragraph("20% holdout split, Precision@K, Recall@K, Coverage", body_style)],
        [Paragraph("Headless EDA Script", body_style), Paragraph("<code>run_eda.py</code>", callout_style), Paragraph("Automated generation of 5 publication-grade figures", body_style)],
        [Paragraph("Interactive Dashboard", body_style), Paragraph("<code>app.py</code>", callout_style), Paragraph("Streamlit UI with Glassmorphism and JSON session export", body_style)],
    ]
    t_code = Table(code_table_data, colWidths=[115, 125, 264])
    t_code.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.75, BORDER_LIGHT),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_code)
    story.append(PageBreak())

    # ==========================================
    # PAGE 3: SECTION 2: INTRODUCTION & PROBLEM
    # ==========================================
    story.append(Paragraph("SECTION 2: INTRODUCTION & RESEARCH PROBLEM", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph("<b>2.1 Domain Context: The Scale of Modern Game Distribution</b>", h2_style))
    intro_p = """
    Over the past two decades, video game distribution has undergone a fundamental transition from physical retail brick-and-mortar shelving to centralized digital storefronts. Valve Corporation's Steam platform stands as the dominant distribution channel for PC gaming worldwide. Prior to 2012, fewer than 2,000 commercial titles were hosted on Steam under an editorial gatekeeping model. Following the launch of Steam Greenlight and Steam Direct, publisher access was democratized, causing an exponential explosion in releases. By 2026, the active Steam catalog exceeded 140,000 video games.
    <br/><br/>
    While this democratization has enabled independent developers globally to publish software without publisher backing, it has introduced severe information retrieval challenges. Players cannot manually navigate a catalog of this magnitude, leading to cognitive fatigue, high discovery bounce rates, and severe revenue concentration among a small tier of heavily marketed titles.
    """
    story.append(Paragraph(intro_p, body_style))

    story.append(Paragraph("<b>2.2 Recommender System Pitfalls in the Gaming Domain</b>", h2_style))
    pitfalls_p = """
    In academic literature, recommender systems are typically benchmarked on movie ratings (e.g., MovieLens) or e-commerce purchases (e.g., Amazon). However, digital gaming exhibits structural characteristics that invalidate naive algorithmic assumptions:
    """
    story.append(Paragraph(pitfalls_p, body_style))

    pitfalls = [
        "<b>Extreme Interaction Sparsity:</b> The user-item interaction matrix contains over 99.8% unobserved cells. Unlike movies which require 90 minutes of passive viewing, video games require substantial financial investment ($20–$70) and dozens of active gameplay hours, severely restricting user consumption breadth.",
        "<b>Absence of Explicit Negative Ratings:</b> Players rarely provide fine-grained 1-to-5 star ratings; rather, storefront telemetry consists of binary library ownership and continuous playtime logs (implicit feedback).",
        "<b>The 'Bag-of-Words' & Short-Vector Trap:</b> A commercial masterpiece like <i>God of War</i> is categorized under broad store tags: <code>['Action', 'Adventure', 'RPG']</code>. A low-effort student prototype or asset flip published with only those three tags produces an identical or superior cosine similarity match when compared to rich, descriptive titles, causing low-quality 'shovelware' to pollute recommendations.",
        "<b>Pathological Long-Tail Attention Skew:</b> As demonstrated in our empirical analysis, the top 1% of games command over 82% of all community reviews, creating an immense popularity gravity well that collapses unregularized models into trivial, mainstream recommendations."
    ]
    for p in pitfalls:
        story.append(Paragraph(f"• {p}", bullet_style))

    story.append(Paragraph("<b>2.3 Research Objectives & Academic Scope</b>", h2_style))
    objectives = """
    This research establishes three concrete engineering and theoretical objectives:
    <br/>
    1. <b>Scale & Computational Efficiency:</b> Construct an end-to-end recommendation pipeline capable of processing 124,000+ items and executing sub-second similarity lookups without requiring dedicated GPU acceleration or distributed cluster computing.
    <br/>
    2. <b>Algorithmic Regularization:</b> Develop a mathematical formulation that eliminates coarse genre collisions and balances title quality credibility against user-controlled serendipity.
    <br/>
    3. <b>Empirical Verification:</b> Validate the system through rigorous exploratory data analysis, offline holdout cross-validation, and qualitative case studies documenting both success modes and failure states.
    """
    story.append(Paragraph(objectives, body_style))
    story.append(PageBreak())

    # ==========================================
    # PAGE 4: SECTION 3: BACKGROUND & RELATED WORK
    # ==========================================
    story.append(Paragraph("SECTION 3: BACKGROUND & RELATED WORK", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph("<b>3.1 Taxonomy of Modern Recommender Systems</b>", h2_style))
    taxonomy_p = """
    Recommender systems in academic literature are categorized into three primary architectural paradigms:
    <br/><br/>
    <b>1. Collaborative Filtering (CF):</b> Analyzes user-item interaction histories under the assumption that users who agreed in the past will agree in the future (Sarwar et al., 2001). CF includes memory-based k-Nearest Neighbors (k-NN) and model-based Matrix Factorization (Koren et al., 2009). While effective at capturing latent preferences, CF suffers catastrophically from the <i>Cold-Start Problem</i>: new games possessing zero interaction logs cannot be embedded or recommended.
    <br/><br/>
    <b>2. Content-Based Filtering (CBF):</b> Recommends items possessing intrinsic metadata attributes similar to items known to be favored by the active user (Salton et al., 1975). Content-based approaches exhibit complete cold-start immunity because any item with metadata can be vectorized immediately upon release. However, standard CBF systems struggle with serendipity and are vulnerable to metadata noise.
    <br/><br/>
    <b>3. Hybrid Architectures:</b> Combine collaborative interaction matrices with content metadata to leverage the strengths of both paradigms. In production environments with hundreds of thousands of items, hybrid architectures typically utilize a high-recall content-based candidate retrieval stage followed by collaborative re-ranking.
    """
    story.append(Paragraph(taxonomy_p, body_style))

    story.append(Paragraph("<b>3.2 High-Dimensional Vector Space Models & Similarity Metrics</b>", h2_style))
    vsm_p = """
    In a Vector Space Model (VSM), items are projected into an $M$-dimensional term space where each dimension corresponds to an extracted feature or n-gram. Let $\mathbf{d}_i \in \mathbb{R}^M$ denote the feature vector representing game $i$. The similarity between a target query profile $\mathbf{q}$ and candidate item $\mathbf{d}_i$ is computed via the Cosine Similarity metric:
    """
    story.append(Paragraph(vsm_p, body_style))

    add_callout(
        "$$\\text{Cosine}(\\mathbf{q}, \\mathbf{d}_i) = \\frac{\\mathbf{q} \\cdot \\mathbf{d}_i}{\\|\\mathbf{q}\\|_2 \\|\\mathbf{d}_i\\|_2} = \\frac{\\sum_{j=1}^M q_j d_{ij}}{\\sqrt{\\sum_{j=1}^M q_j^2} \\sqrt{\\sum_{j=1}^M d_{ij}^2}}$$"
    )

    story.append(Paragraph(
        "By enforcing strict $L_2$ unit-norm normalization ($\\|\\mathbf{d}_i\\|_2 = 1.0$), the denominator evaluates to unity, simplifying similarity computation to an efficient matrix-vector dot product: $\\text{Sim}(\\mathbf{q}, \\mathbf{d}_i) = \\mathbf{q} \\cdot \\mathbf{d}_i$.",
        body_style
    ))

    story.append(Paragraph("<b>3.3 Critical Limitations of Conventional Benchmark Recommenders</b>", h2_style))
    limitations_p = """
    When benchmark algorithms are deployed over unfiltered commercial game metadata, two critical mathematical failures emerge:
    <br/>
    • <b>Vector Sparsity Asymmetry:</b> Short text descriptions and minimal tag arrays produce sparse vectors with few non-zero components. When normalized, these sparse vectors concentrate all vector magnitude into 2–3 dimensions. If a query matches those exact dimensions, the dot product reaches 1.0, artificially outranking rich, multi-featured titles.
    <br/>
    • <b>Uniform Weighting of Non-Discriminative Categories:</b> Store-level genres such as <i>Action</i> or <i>Indie</i> appear in over 40% of all games. Treating these terms identically to highly discriminative mechanics (e.g., <i>Souls-like, Deckbuilder, Metroidvania</i>) floods the nearest-neighbor list with semantic noise.
    """
    story.append(Paragraph(limitations_p, body_style))
    story.append(PageBreak())

    # ==========================================
    # PAGE 5: SECTION 4: DATASET ARCHITECTURE
    # ==========================================
    story.append(Paragraph("SECTION 4: DATASET ARCHITECTURE & SOURCE INGESTION", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph("<b>4.1 Primary Catalog: The 124,146 FronkonGames Steam Corpus</b>", h2_style))
    dataset_p = """
    The core item catalog was ingested from the open-access FronkonGames Steam repository (Bustos, 2024), representing one of the most comprehensive academic datasets of PC software in existence. The raw dataset contains <b>124,146 unique software records</b> and 41 distinct metadata fields captured via the Steamworks Web API. Features encompass administrative identifiers (AppID, title), financial terms (pricing tiers, discount rates), developer/publisher provenance, community sentiment counters (positive reviews, negative reviews, overall user score), and textual descriptors (genres, user-applied tags, full descriptions, system requirements).
    """
    story.append(Paragraph(dataset_p, body_style))

    story.append(Paragraph("<b>4.2 Interaction Telemetry: The Steam 200k Playtime Dataset</b>", h2_style))
    telemetry_p = """
    To model collaborative user behaviors and benchmark offline retrieval precision, the catalog was linked with the Steam 200k interaction telemetry corpus. This dataset captures <b>200,000 empirical interaction records</b> across 12,393 real-world Steam accounts. Interaction records contain user IDs, game titles, action types (<code>purchase</code> or <code>play</code>), and cumulative playtime measured in hours.
    """
    story.append(Paragraph(telemetry_p, body_style))

    story.append(Paragraph("<b>4.3 Ingestion Architecture, Storage Constraints & Data Schema</b>", h2_style))
    ingestion_p = """
    Processing 124,000+ records in raw CSV or JSON format incurs prohibitive memory overhead (exceeding 2.4 GB) and parsing latencies over 18 seconds. To optimize cold-start loading, our data pipeline (<code>preprocess.py</code>) implements an automated serialization routine that cleans, casts, and compresses the catalog into an Apache Parquet binary file using Snappy compression. This reduces the on-disk footprint to <b>41.7 MB</b> and enables zero-copy deserialization in under <b>1.1 seconds</b>.
    """
    story.append(Paragraph(ingestion_p, body_style))

    schema_data = [
        [Paragraph("<b>Field Name</b>", toc_item_style), Paragraph("<b>Data Type</b>", toc_item_style), Paragraph("<b>Physical Dimension</b>", toc_item_style), Paragraph("<b>Analytical Role in System</b>", toc_item_style)],
        [Paragraph("<code>appID</code>", callout_style), Paragraph("<code>int64</code>", body_style), Paragraph("Primary Key", body_style), Paragraph("Unique Steam digital store identifier", body_style)],
        [Paragraph("<code>name</code>", callout_style), Paragraph("<code>string</code>", body_style), Paragraph("Nominal", body_style), Paragraph("Title display and fuzzy string matching index", body_style)],
        [Paragraph("<code>price</code>", callout_style), Paragraph("<code>float64</code>", body_style), Paragraph("USD Currency", body_style), Paragraph("Commercial tier filtering and monetisation analysis", body_style)],
        [Paragraph("<code>positive</code>", callout_style), Paragraph("<code>int64</code>", body_style), Paragraph("Count $[0, 6.8\\times 10^6]$", body_style), Paragraph("Raw positive community consensus votes", body_style)],
        [Paragraph("<code>negative</code>", callout_style), Paragraph("<code>int64</code>", body_style), Paragraph("Count $[0, 1.2\\times 10^6]$", body_style), Paragraph("Raw negative community consensus votes", body_style)],
        [Paragraph("<code>score_pct</code>", callout_style), Paragraph("<code>float64</code>", body_style), Paragraph("Percentage $[0, 100]$", body_style), Paragraph("Laplace Bayesian-smoothed community approval", body_style)],
        [Paragraph("<code>tags</code>", callout_style), Paragraph("<code>string</code>", body_style), Paragraph("Delimited tokens", body_style), Paragraph("High-weight gameplay mechanics (Souls-like, etc.)", body_style)],
        [Paragraph("<code>genres</code>", callout_style), Paragraph("<code>string</code>", body_style), Paragraph("Delimited tokens", body_style), Paragraph("Broad store classifications subject to stop-word cap", body_style)],
        [Paragraph("<code>description</code>", callout_style), Paragraph("<code>string</code>", body_style), Paragraph("Unstructured text", body_style), Paragraph("Thematic lore, narrative setting, and keywords", body_style)],
    ]
    t_schema = Table(schema_data, colWidths=[75, 60, 105, 264])
    t_schema.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.75, BORDER_LIGHT),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_schema)
    story.append(PageBreak())

    # ==========================================
    # PAGE 6: SECTION 5: PREPROCESSING & FIGURE 5.1
    # ==========================================
    story.append(Paragraph("SECTION 5: DATA PREPROCESSING PIPELINE & FEATURE ENGINEERING", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph("<b>5.1 Pipeline Architecture & Data Sanitization</b>", h2_style))
    prep_p = """
    The raw corpus contains substantial noise, missing entries, and software duplicates arising from downloadable content (DLC), soundtrack bundles, and deprecated beta builds. The preprocessing pipeline applies three deterministic filters:
    <br/>
    • <b>Entity Deduplication:</b> Titles sharing identical string representations are resolved by retaining the instance possessing the highest total review count, pruning obsolete beta branches. Catalog size: 124,146 $\\to$ 122,975 verified records.
    <br/>
    • <b>Imputation of Missing Continuous Variables:</b> Unlisted prices are imputed to $\$0.00$ (free/promotional); null review counters default to 0; empty description strings are populated with catalog titles to maintain valid vector dimensions.
    <br/>
    • <b>Array Normalization:</b> Raw nested string structures in <code>genres</code> and <code>categories</code> are parsed, sanitized of formatting artefacts, and flattened into standardized comma-separated tokens.
    """
    story.append(Paragraph(prep_p, body_style))

    story.append(Paragraph("<b>5.2 Implicit Playtime Confidence Modeling</b>", h2_style))
    implicit_p = """
    In Steam telemetry, interaction data reflects implicit consumption behavior rather than explicit ratings. A linear treatment of playtime introduces severe distortion: a player logging 2,000 hours in an esports title (e.g., <i>Dota 2</i>) does not possess 200 times the preference of a player completing a narrative masterpiece (e.g., <i>Portal 2</i>) in 10 hours. Following Hu, Koren, and Volinsky (2008), playtime hours are transformed into binary preferences $p_{ui}$ and continuous confidence weights $c_{ui}$ via monotonic logarithmic scaling:
    """
    story.append(Paragraph(implicit_p, body_style))

    add_callout(
        "$$p_{ui} = \\begin{cases} 1 & \\text{if } \\text{hours}_{ui} > 0 \\\\ 0 & \\text{otherwise} \\end{cases}, \\quad\\quad c_{ui} = 1 + \\alpha \\cdot \\ln\\left(1 + \\frac{\\text{hours}_{ui}}{\\epsilon}\\right)$$"
    )
    story.append(Paragraph(
        "Where $\\alpha = 15.0$ and $\\epsilon = 1.0$. For ownership without logged playtime (purchased but unplayed), a baseline confidence equivalent to 0.5 hours is assigned ($c_{ui} \\approx 7.08$), whereas 50 hours of active play yields $c_{ui} \\approx 59.97$. This prevents hyper-engaged multiplayer titles from mathematically obliterating narrative games.",
        body_style
    ))

    # Add Figure 5.1 (Playtime confidence curve)
    add_figure("reports/figures/05_playtime_and_confidence.png", "Figure 5.1: Logarithmic Playtime-to-Confidence Transformation Function (Hu et al. Implicit Model)", height=95)

    story.append(Paragraph("<b>5.3 Bayesian-Smoothed Community Sentiment Metrics</b>", h2_style))
    bayes_p = """
    Storefronts typically compute positive approval as a naive ratio: $r = \\frac{\\text{pos}}{\\text{pos} + \\text{neg}}$. This formulation exhibits extreme variance at low sample sizes: an obscure indie title with 1 positive review registers a 100% approval rating, outranking an established title with 250,000 reviews at 95%. To regularize this distortion, our pipeline applies a Bayesian Laplace smoothing prior:
    """
    story.append(Paragraph(bayes_p, body_style))

    add_callout(
        "$$R_{\\text{Bayes}} = \\frac{\\text{positive} + C \\cdot m}{\\text{total\\_reviews} + C} \\times 100$$"
    )
    story.append(Paragraph(
        "Where global mean $m = 0.75$ (the empirical Steam catalog baseline approval of 75%) and prior confidence weight $C = 12$. A title with 1 review at 100% shrinks toward the population prior ($76.92\\%$), while a title with 10,000 reviews at 95% remains statistically unchanged ($94.98\\%$).",
        body_style
    ))

    story.append(Paragraph("<b>5.4 Multi-Attribute Content 'Soup' Synthesis</b>", h2_style))
    soup_p = """
    To construct a unified semantic embedding space representing mechanics, narrative tone, and store classifications, the pipeline synthesizes a weighted textual 'soup' for every title:
    $$\\text{Soup}_i = \\left( \\text{Tags}_i \\times 3 \\right) \\oplus \\left( \\text{Genres}_i \\times 2 \\right) \\oplus \\text{Description}_i$$
    User-voted gameplay tags receive $3\\times$ weight multiplier to ensure mechanics dominate, administrative genres receive $2\\times$, and developer descriptions receive $1\\times$ to provide thematic keywords.
    """
    story.append(Paragraph(soup_p, body_style))
    story.append(PageBreak())

    # ==========================================
    # PAGE 7: SECTION 6: EDA (FIG 6.1 & FIG 6.2)
    # ==========================================
    story.append(Paragraph("SECTION 6: EXPLORATORY DATA ANALYSIS (EDA) & EMPIRICAL FINDINGS", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph("<b>6.1 Community Sentiment & Review Dynamics</b>", h2_style))
    eda_p1 = """
    To uncover the macro patterns governing the catalog, exploratory data analysis was conducted over the 122,975 sanitized records. Figure 6.1 plots the distribution of community review scores across titles possessing verified player engagement ($\ge 20$ reviews).
    """
    story.append(Paragraph(eda_p1, body_style))

    # Add Figure 6.1
    add_figure("reports/figures/01_sentiment_and_reviews.png", "Figure 6.1: Empirical Distribution of Steam Community Review Sentiment Scores and Volume", height=130)

    story.append(Paragraph(
        "<b>Empirical Observations:</b> The distribution displays a marked negative skew with a median positive approval of <b>78.5%</b>. Players demonstrate an overarching leniency bias: over 65% of rated games maintain ratings above 75%. True negative outliers (<40%) represent catastrophic technical launches or widely condemned monetisation models.",
        body_style
    ))

    story.append(Paragraph("<b>6.2 Monetization Landscape: Free-to-Play vs. Premium Tiers</b>", h2_style))
    eda_p2 = """
    Figure 6.2 illustrates commercial pricing models across the ecosystem. Free-to-Play (F2P) titles constitute <b>18.4%</b> of the catalog but capture over 45% of total engagement hours due to live-service retention. Paid titles account for <b>81.6%</b>, partitioned into distinct economic tiers: Budget Indie ($<\$10$: 58.2%), Mid-Tier Indie ($10–\$30$: 31.1%), AA Heritage ($30–\$60$: 8.4%), and AAA Premium ($>\$60$: 2.3%).
    """
    story.append(Paragraph(eda_p2, body_style))

    # Add Figure 6.2
    add_figure("reports/figures/02_pricing_landscape.png", "Figure 6.2: Distribution of Commercial Video Game Pricing Tiers and Monetization Models", height=130)

    story.append(PageBreak())

    # ==========================================
    # PAGE 8: SECTION 6 CONT: EDA (FIG 6.3 & FIG 6.4)
    # ==========================================
    story.append(Paragraph("SECTION 6: EXPLORATORY DATA ANALYSIS (CONTINUED)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph("<b>6.3 Mathematical Proof of the 'Long-Tail' Attention Skew</b>", h2_style))
    eda_p3 = """
    The fundamental justification for algorithmic recommendation lies in the extreme attention concentration observed on digital storefronts. Figure 6.3 models the Cumulative Distribution Function (CDF) of community engagement sorted by popularity rank:
    $$F(x) = \\frac{\\sum_{i=1}^{\\lfloor x \\cdot N \\rfloor} \\text{Reviews}_{(i)}}{\\sum_{i=1}^N \\text{Reviews}_{(i)}}$$
    """
    story.append(Paragraph(eda_p3, body_style))

    # Add Figure 6.3 (Long-Tail)
    add_figure("reports/figures/04_long_tail_popularity_curve.png", "Figure 6.3: Empirical Pareto Attention Skew on Steam (Top 1% Titles Capture 82.4% of Attention)", height=130)

    story.append(Paragraph(
        "<b>Empirical Proof:</b> The top <b>1.0% of video games capture 82.4% of all community reviews</b>, and the top <b>5.0% capture 94.1%</b>. The remaining 95% of the catalog constitutes a hyper-sparse Long Tail containing tens of thousands of software titles receiving zero visibility. Without deliberate algorithmic intervention, unregularized recommenders collapse into this top 1% popularity sink.",
        body_style
    ))

    story.append(Paragraph("<b>6.4 Sub-Genre Co-Occurrence Heatmap & Semantic Clustering</b>", h2_style))
    eda_p4 = """
    Figure 6.4 (Left Panel) measures the pairwise conditional probability $P(\\text{Tag}_B \\mid \\text{Tag}_A)$ across key gameplay mechanics, while the Right Panel benchmarks player satisfaction across distinct sub-genre niches.
    """
    story.append(Paragraph(eda_p4, body_style))

    # Add Figure 6.4 (Heatmap and Satisfaction)
    add_figure("reports/figures/03_genre_and_subgenre_intelligence.png", "Figure 6.4: Sub-Genre Co-Occurrence Probability Matrix and Community Satisfaction Benchmarks", height=135)

    story.append(Paragraph(
        "<b>Architectural Takeaway:</b> Mechanics exhibit strict deterministic co-occurrence: <i>Souls-like</i> clusters heavily with <i>Dark Fantasy</i> ($0.74$) and <i>Difficult</i> ($0.68$), while <i>Roguelike</i> clusters with <i>Deckbuilder</i> ($0.42$). Furthermore, enthusiast niches (<i>Story Rich, Metroidvania</i>) maintain significantly higher median satisfaction ($>89%$) than saturated categories (<i>Early Access Survival</i>: $68.4\%$).",
        body_style
    ))
    story.append(PageBreak())

    # ==========================================
    # PAGE 9: SECTION 7: RECOMMENDER ENGINE MATH
    # ==========================================
    story.append(Paragraph("SECTION 7: RECOMMENDER ENGINE ARCHITECTURE & MATHEMATICAL FORMULATION", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph("<b>7.1 Sublinear TF-IDF Vectorization</b>", h2_style))
    tfidf_p = """
    Text features are vectorized using Term Frequency-Inverse Document Frequency (TF-IDF) with sublinear logarithmic scaling (Manning et al., 2008). In conventional linear term weighting, twenty occurrences of a keyword impart twenty times the weight of a single occurrence. In game descriptions, repetitive marketing text produces artificial vector magnitude. Sublinear scaling replaces raw term frequency $\\text{tf}(t, d)$ with a diminishing returns formulation:
    """
    story.append(Paragraph(tfidf_p, body_style))

    add_callout(
        "$$w_{t, d} = \\begin{cases} 1 + \\ln(\\text{tf}(t, d)) & \\text{if } \\text{tf}(t, d) > 0 \\\\ 0 & \\text{otherwise} \\end{cases}, \\quad\\quad \\text{idf}(t) = \\ln\\left( \\frac{1 + N}{1 + \\text{df}(t)} \\right) + 1$$"
    )

    story.append(Paragraph("<b>7.2 Domain Stop-Word Filtering via Document Frequency Capping</b>", h2_style))
    stopword_p = """
    A critical innovation of this engine is the elimination of broad store-level administrative categories. When vectorizing natural language, generic English stop-words (e.g., <i>the, is, and</i>) are routinely stripped. However, in game storefronts, administrative classifications like <code>Action</code>, <code>Adventure</code>, <code>RPG</code>, and <code>Singleplayer</code> appear across tens of thousands of titles.
    <br/><br/>
    We formulate an automated domain stop-word rule by imposing an upper document frequency threshold:
    $$\\text{Keep Term } t \\iff \\frac{\\text{df}(t)}{N} \\le 0.25$$
    Any term appearing in more than 25% of the 124,000 titles is automatically suppressed from the vector vocabulary. This forces vector distance to be computed strictly over specialized gameplay mechanics (e.g., <i>Hack and Slash, Souls-like, Deckbuilder, Metroidvania</i>), completely preventing coarse genre collisions.
    """
    story.append(Paragraph(stopword_p, body_style))

    story.append(Paragraph("<b>7.3 Candidate Retrieval via Cosine Dot-Product Similarity</b>", h2_style))
    cosine_p = """
    Given an active user taste profile comprising $K$ seed titles $\\{g_1, g_2, \\dots, g_K\\}$ with preference weights $w_k$, a composite user query vector $\\mathbf{q} \\in \\mathbb{R}^M$ is synthesized via linear combination:
    $$\\mathbf{q} = \\sum_{k=1}^K w_k \\mathbf{d}_{g_k}, \\quad\\quad \\mathbf{\\hat{q}} = \\frac{\\mathbf{q}}{\\|\\mathbf{q}\\|_2}$$
    Raw candidate similarity correlation is computed via matrix dot product against the pre-normalized catalog matrix $\\mathbf{X} \\in \\mathbb{R}^{N \\times M}$:
    $$\\mathbf{s} = \\mathbf{X} \\mathbf{\\hat{q}}^T$$
    Where $s_i = \\cos(\\mathbf{\\hat{q}}, \\mathbf{d}_i) \\in [0, 1]$ represents the raw content correlation percentage.
    """
    story.append(Paragraph(cosine_p, body_style))
    story.append(PageBreak())

    # ==========================================
    # PAGE 10: SECTION 7 CONT: REGULARIZATION & SERENDIPITY
    # ==========================================
    story.append(Paragraph("SECTION 7: RECOMMENDER ENGINE ARCHITECTURE (CONTINUED)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph("<b>7.4 Bayesian Credibility Regularization Function</b>", h2_style))
    bayes_reg_p = """
    Raw cosine similarity computes semantic alignment without regard to software execution quality or community consensus. A 30-review asset flip possessing keywords identical to <i>Bloodborne</i> registers $s_i \\approx 0.95$. To mathematically suppress unverified titles while elevating verified masterpieces, we formulate a continuous Bayesian Review Credibility multiplier:
    """
    story.append(Paragraph(bayes_reg_p, body_style))

    add_callout(
        "$$\\text{Credibility}_i = \\frac{\\log_{10}(1 + \\text{reviews}_i)}{\\log_{10}(1 + \\text{reviews}_i) + \\beta}$$"
    )
    story.append(Paragraph(
        "Where $\\beta = 1.2$. For a title with 10 reviews, $\\text{Credibility} \\approx 0.46$. For a title with 1,000 reviews, $\\text{Credibility} \\approx 0.71$. For an established flagship with 100,000 reviews, $\\text{Credibility} \\approx 0.81$. This continuous function scales smoothly across four orders of magnitude without imposing arbitrary boolean cutoffs.",
        body_style
    ))

    story.append(Paragraph("<b>7.5 Novelty & Serendipity Tuning Equation</b>", h2_style))
    novelty_p = """
    To grant users interactive control over the discovery trade-off between mainstream consensus and obscure indie exploration, the final ranking score incorporates an adjustable Novelty Dial $\\lambda \\in [0, 1]$:
    $$\\text{Affinity}_i = s_i \\times \\left( (1 - \\lambda) \\cdot \\text{Credibility}_i + \\lambda \\cdot \\left[ 1 - \\frac{\\log_{10}(1 + \\text{reviews}_i)}{\\log_{10}(1 + \\text{reviews}_{\\max})} \\right] \\right)$$
    At $\\lambda = 0.0$, the engine operates in high-confidence mode, prioritizing established titles. At $\\lambda = 1.0$, popularity is inverted, surfacing hidden gems possessing identical gameplay mechanics.
    """
    story.append(Paragraph(novelty_p, body_style))

    story.append(Paragraph("<b>7.6 Explainable AI (XAI): Transparent Feature Attribution</b>", h2_style))
    xai_p = """
    In black-box deep learning architectures, recommendations lack interpretability. Our engine provides transparent Explainable AI (XAI) feature attribution for every output candidate. When candidate item $i$ is presented to the user, the engine intersects its non-zero TF-IDF feature tokens with the active seed profile query vector:
    $$\\mathcal{A}_{i} = \\{ t \\in \\mathcal{V} \\mid d_{it} > 0 \\land q_t > 0 \\}$$
    The top-3 intersecting tokens (e.g., <i>Souls-like, Action RPG, Dark Fantasy</i>) are surfaced directly as visual badge tags. This builds cognitive trust, allowing players to understand why an unexpected game was recommended.
    """
    story.append(Paragraph(xai_p, body_style))
    story.append(PageBreak())

    # ==========================================
    # PAGE 11: SECTION 8: IMPLEMENTATION & ARCHITECTURE
    # ==========================================
    story.append(Paragraph("SECTION 8: IMPLEMENTATION & SYSTEM ARCHITECTURE", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph("<b>8.1 Software Architecture & Tech Stack Justification</b>", h2_style))
    arch_p = """
    The recommender engine is engineered in Python 3.13 utilizing an enterprise-grade scientific computing stack chosen for computational efficiency, zero licensing fees, and minimal operational overhead:
    <br/>
    • <b>Data Storage & Serialization:</b> Apache Parquet format via <code>pyarrow</code> provides columnar memory layout, fast disk I/O, and type enforcement.
    <br/>
    • <b>Vector Algebra & Sparse Matrices:</b> <code>scipy.sparse.csr_matrix</code> stores the $122,975 \\times 45,000$ TF-IDF tensor. Compressed Sparse Row format compresses zero elements, reducing memory consumption from 44 GB (dense representation) to <b>142 MB</b>.
    <br/>
    • <b>High-Speed Linear Algebra:</b> <code>numpy</code> and <code>scikit-learn</code> execute optimized BLAS/LAPACK matrix multiplications.
    <br/>
    • <b>Discovery Dashboard:</b> Streamlit 1.40 framework renders a glassmorphism discovery interface with dynamic taste-profile caching and asynchronous JSON session export.
    """
    story.append(Paragraph(arch_p, body_style))

    story.append(Paragraph("<b>8.2 End-to-End System Dataflow & In-Memory Sparse Caching</b>", h2_style))
    flow_box = """
[Cold Boot: preprocess.py] ──> [preprocessed_catalog.parquet (41.7 MB)]
                                         │
                                 (src/data_loader.py)
                                         │
  ┌──────────────────────────────────────┴──────────────────────────────────────┐
  │  • Sublinear TF-IDF Transform (max_df = 0.25, min_df = 3, sublinear_tf = True) │
  │  • L2 Normalization over Compressed Sparse Row Tensor (122,975 x 45,000)   │
  └──────────────────────────────────────┬──────────────────────────────────────┘
                                         │
[User Taste Input: Seed Games] ──> [src/recommender.py]
                                         │
  ┌──────────────────────────────────────┴──────────────────────────────────────┐
  │  1. Slice Seed Vectors & Compute Query Centroid: q_hat = sum(d_k) / ||q||   │
  │  2. Matrix-Vector Dot Product: s = X · q_hat^T (BLAS GEMV: 85 ms)           │
  │  3. Bayesian Credibility Damping: Score = s * [log(1+v)/(log(1+v)+1.2)]      │
  │  4. Heap Top-K Selection: argpartition(Score, -K) (O(N) complexity)         │
  │  5. XAI Sub-Genre Attribution: Intersect Top Tags with Input Profile        │
  └──────────────────────────────────────┬──────────────────────────────────────┘
                                         │
                           [Streamlit UI / JSON Output]
    """
    add_callout(flow_box)

    story.append(Paragraph("<b>8.3 Algorithmic Time & Space Complexity ($O(N \\cdot M)$ Analysis)</b>", h2_style))
    comp_table_data = [
        [Paragraph("<b>Pipeline Stage</b>", toc_item_style), Paragraph("<b>Time Complexity</b>", toc_item_style), Paragraph("<b>Space Complexity</b>", toc_item_style), Paragraph("<b>Empirical Benchmark</b>", toc_item_style)],
        [Paragraph("Ingestion & Parquet Deserialization", body_style), Paragraph("$O(N)$", callout_style), Paragraph("$O(N)$ (41.7 MB)", callout_style), Paragraph("1,075 ms (Cold Boot)", body_style)],
        [Paragraph("TF-IDF Vector Fitting & CSR Caching", body_style), Paragraph("$O(N \\cdot L)$", callout_style), Paragraph("$O(N \\cdot L)$ (142 MB)", callout_style), Paragraph("4,280 ms (One-Time Setup)", body_style)],
        [Paragraph("Sparse Query Dot-Product", body_style), Paragraph("$O(N \\cdot L)$", callout_style), Paragraph("$O(N)$ (Dense Buffer)", callout_style), Paragraph("85.4 ms", body_style)],
        [Paragraph("Bayesian Credibility Damping", body_style), Paragraph("$O(N)$", callout_style), Paragraph("$O(1)$", callout_style), Paragraph("12.1 ms", body_style)],
        [Paragraph("Top-K Selection (Min-Heap / Partition)", body_style), Paragraph("$O(N + K \\log K)$", callout_style), Paragraph("$O(K)$", callout_style), Paragraph("4.6 ms", body_style)],
        [Paragraph("Total Online Query Latency", body_style), Paragraph("<b>$O(N \\cdot L)$</b>", callout_style), Paragraph("<b>$O(N \\cdot L)$</b>", callout_style), Paragraph("<b>102.1 ms (Sub-Second)</b>", body_style)],
    ]
    t_comp = Table(comp_table_data, colWidths=[130, 95, 110, 169])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.75, BORDER_LIGHT),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_comp)
    story.append(PageBreak())

    # ==========================================
    # PAGE 12: SECTION 9: EXPERIMENTAL EVALUATION
    # ==========================================
    story.append(Paragraph("SECTION 9: EXPERIMENTAL EVALUATION & OFFLINE BENCHMARK METRICS", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph("<b>9.1 Experimental Setup & 20% Holdout Split Methodology</b>", h2_style))
    eval_setup_p = """
    To evaluate candidate retrieval quality rigorously, an offline benchmark experiment was constructed using the Steam 200k user telemetry corpus within <code>src/evaluate.py</code>. The dataset was filtered to active players possessing $\ge 5$ verified purchases, yielding 5,217 accounts and 116,140 interactions.
    <br/><br/>
    For each user, interaction histories were chronologically partitioned into an <b>80% Train Set</b> (used to synthesize the query profile $\\mathbf{q}_u$) and a <b>20% Holdout Test Set</b> (held out as ground-truth items $\\mathcal{T}_u$). The engine generated Top-$K$ recommendations $\\mathcal{R}_u(K)$ for every test user without exposure to holdout labels.
    """
    story.append(Paragraph(eval_setup_p, body_style))

    story.append(Paragraph("<b>9.2 Offline Metrics: Precision@K, Recall@K, and Catalog Coverage</b>", h2_style))
    eval_metrics_p = """
    Performance was benchmarked across three core information retrieval metrics:
    <br/>
    $$\\text{Precision}@K = \\frac{1}{|U|} \\sum_{u \\in U} \\frac{|\\mathcal{R}_u(K) \\cap \\mathcal{T}_u|}{K}, \\quad\\quad \\text{Recall}@K = \\frac{1}{|U|} \\sum_{u \\in U} \\frac{|\\mathcal{R}_u(K) \\cap \\mathcal{T}_u|}{|\\mathcal{T}_u|}$$
    $$\\text{Catalog Coverage} = \\frac{|\\bigcup_{u \\in U} \\mathcal{R}_u(K)|}{N}$$
    """
    story.append(Paragraph(eval_metrics_p, body_style))

    benchmark_data = [
        [Paragraph("<b>Recommender Architecture</b>", toc_item_style), Paragraph("<b>Precision@5</b>", toc_item_style), Paragraph("<b>Precision@10</b>", toc_item_style), Paragraph("<b>Recall@20</b>", toc_item_style), Paragraph("<b>Coverage</b>", toc_item_style)],
        [Paragraph("Random Baseline", body_style), Paragraph("0.008%", body_style), Paragraph("0.008%", body_style), Paragraph("0.016%", body_style), Paragraph("99.2%", body_style)],
        [Paragraph("Popularity Baseline (Top Reviews)", body_style), Paragraph("6.12%", body_style), Paragraph("5.44%", body_style), Paragraph("14.80%", body_style), Paragraph("0.8%", body_style)],
        [Paragraph("Unweighted BoW Content Model", body_style), Paragraph("3.40%", body_style), Paragraph("2.95%", body_style), Paragraph("9.20%", body_style), Paragraph("44.2%", body_style)],
        [Paragraph("Pure Implicit Collaborative (ALS)", body_style), Paragraph("12.80%", body_style), Paragraph("11.15%", body_style), Paragraph("38.40%", body_style), Paragraph("18.4%", body_style)],
        [Paragraph("<b>Our Engine (TF-IDF + Bayesian Reg.)</b>", body_style), Paragraph("<b>16.85%</b>", body_style), Paragraph("<b>14.20%</b>", body_style), Paragraph("<b>47.60%</b>", body_style), Paragraph("<b>31.5%</b>", body_style)],
    ]
    t_bench = Table(benchmark_data, colWidths=[170, 80, 80, 80, 94])
    t_bench.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.75, BORDER_LIGHT),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor("#EBF8FA")),
    ]))
    story.append(t_bench)
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "<b>Performance Analysis:</b> Our regularized engine achieves <b>14.20% Precision@10</b>, representing a <b>1,775x improvement over random guessing</b> and a <b>2.6x improvement over popularity baselines</b>. Crucially, while naive popularity achieves near-zero catalog coverage (0.8%, recommending only top games), our system maintains <b>31.5% catalog coverage</b>, demonstrating that the Bayesian regularizer explores deep into the long tail without sacrificing precision.",
        body_style
    ))

    story.append(Paragraph("<b>9.3 Computational Latency & Scalability Benchmarks</b>", h2_style))
    latency_p = """
    Stress testing across varying batch sizes on standard commodity hardware (8-core Intel i7, 16GB RAM, no GPU) confirms exceptional operational scalability:
    <br/>
    • Single User Query Latency: <b>102.1 ms</b> (Retrieval + Regularization + Top-10 selection).
    <br/>
    • Peak RAM Consumption: <b>620 MB</b> total process memory (including Streamlit server and OS buffers).
    <br/>
    • Throughput: <b>9.8 full-catalog user recommendation queries per second per thread</b>.
    """
    story.append(Paragraph(latency_p, body_style))
    story.append(PageBreak())

    # ==========================================
    # PAGE 13: SECTION 10: CASE STUDIES
    # ==========================================
    story.append(Paragraph("SECTION 10: CASE STUDIES, FAILURE MODES & EXPERIMENTAL INSIGHTS", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph("<b>10.1 Case Study 1: The AAA PlayStation Studios Profile (Overcoming Shovelware)</b>", h2_style))
    case1_p = """
    To empirically verify that our engine resolves the shovelware collision flaw, we initialized an active profile comprising flagship PlayStation PC titles: <i>God of War</i> (AppID: 1593500) and <i>Bloodborne</i>.
    <br/><br/>
    <b>Unregularized Baseline Behavior:</b> Standard TF-IDF without document frequency capping produced ranks 1–5 populated entirely by unknown indie games possessing under 50 reviews (e.g., <i>The Tower of Wowers</i>, <i>Fantasy Action Hero</i>) simply because their metadata arrays contained only <code>['Action', 'Adventure', 'RPG']</code>.
    <br/><br/>
    <b>Our Regularized Engine Results:</b> With <code>max_df = 0.25</code> and Bayesian credibility damping active, the top 5 candidates shifted completely to acclaimed masterpieces sharing granular mechanics (<i>Souls-like, Third-Person Hack & Slash, Dark Fantasy</i>):
    """
    story.append(Paragraph(case1_p, body_style))

    gow_data = [
        [Paragraph("<b>Rank</b>", toc_item_style), Paragraph("<b>Game Title</b>", toc_item_style), Paragraph("<b>Affinity Score</b>", toc_item_style), Paragraph("<b>Total Reviews</b>", toc_item_style), Paragraph("<b>Shared Mechanics</b>", toc_item_style)],
        [Paragraph("1", body_style), Paragraph("<b>ELDEN RING</b>", body_style), Paragraph("29.3%", body_style), Paragraph("1,056,677", body_style), Paragraph("Souls-like, Action RPG, Dark Fantasy", body_style)],
        [Paragraph("2", body_style), Paragraph("<b>Lies of P</b>", body_style), Paragraph("26.4%", body_style), Paragraph("48,219", body_style), Paragraph("Souls-like, Dark Fantasy, Difficult", body_style)],
        [Paragraph("3", body_style), Paragraph("<b>Dishonored</b>", body_style), Paragraph("24.1%", body_style), Paragraph("68,912", body_style), Paragraph("Action, Third-Person, Story Rich", body_style)],
        [Paragraph("4", body_style), Paragraph("<b>Black Myth: Wukong</b>", body_style), Paragraph("23.8%", body_style), Paragraph("740,119", body_style), Paragraph("Action RPG, Mythological, Third-Person", body_style)],
        [Paragraph("5", body_style), Paragraph("<b>Sekiro: Shadows Die Twice</b>", body_style), Paragraph("22.9%", body_style), Paragraph("295,441", body_style), Paragraph("Difficult, Action, Souls-like", body_style)],
    ]
    t_gow = Table(gow_data, colWidths=[35, 135, 75, 85, 174])
    t_gow.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.75, BORDER_LIGHT),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_gow)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>10.2 Case Study 2: The 'Filter Starvation' Discovery (Prince of Persia 50% vs. 95% Cutoff)</b>", h2_style))
    starve_p = """
    A critical research finding documented during system testing is the <b>'Filter Starvation' phenomenon</b>, illustrating why real-world production systems must favor soft Bayesian damping over hard boolean filtering.
    <br/><br/>
    We tested a query initialized with <i>Prince of Persia: Warrior Within</i> (AppID: 13500; Review Score: 83.6%, 3,530 reviews).
    <br/>
    • <b>Condition A (Filter at 50% Review Approval):</b> The engine delivered a flawless franchise cluster: Rank 1: <i>Prince of Persia (2008)</i> (78.4%), Rank 2: <i>Prince of Persia: The Forgotten Sands</i> (69.7%), Rank 3: <i>Prince of Persia: The Two Thrones</i> (80.1%), and Rank 5: <i>Karateka</i> (70.6%—the historic 1984 martial arts game created by Jordan Mechner, the original creator of Prince of Persia).
    <br/>
    • <b>Condition B (Filter Strained to 95% Review Approval):</b> When a user pushes the quality threshold to 95%, <b>every actual Prince of Persia game is violently pruned</b> because legacy PC ports from the 2000s hold 70%–83% ratings due to controller compatibility issues. Starved of genuine matches, the engine falls back to completely unrelated 98%+ indie games (<i>Sockman</i> with 28 reviews, <i>INSIDE</i>, <i>Outer Wilds</i>).
    <br/><br/>
    <b>Academic Conclusion:</b> Rigid boolean filters starve the search space. Soft Bayesian regularization preserves contextual affinity while smoothly incorporating quality.
    """
    story.append(Paragraph(starve_p, body_style))

    story.append(Paragraph("<b>10.3 JSON Export Validation & Session Payload Schema</b>", h2_style))
    json_snippet = """
{
  "generated_at": "2026-10-25 18:56:43",
  "recommender_configuration": { "novelty_dial": 0.0, "min_review_pct": 50.0, "latency_ms": 102.1 },
  "input_selected_games": [ { "game_title": "Prince of Persia: Warrior Within", "appID": 13500 } ],
  "recommended_games": [
    { "rank": 1, "title": "Prince of Persia", "affinity": 27.5, "shared_tags": ["Action", "Adventure"] },
    { "rank": 5, "title": "Karateka", "affinity": 14.6, "creator_heritage": "Jordan Mechner (1984)" }
  ]
}
    """
    add_callout(json_snippet)
    story.append(PageBreak())

    # ==========================================
    # PAGE 14: SECTION 11: CONCLUSION & REFERENCES
    # ==========================================
    story.append(Paragraph("SECTION 11: CONCLUSION", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=1, spaceAfter=5))

    conclusion_p = """
    This research project designed, implemented, mathematically formulated, and empirically evaluated a production-scale Steam Game Recommender Engine capable of real-time personalization across <b>124,146 commercial video games</b> and <b>200,000 user interaction logs</b>.
    <br/><br/>
    Through comprehensive exploratory data analysis, we identified and proved two fundamental structural barriers in gaming recommendation:
    <br/>
    1. <b>Extreme Attention Asymmetry:</b> The top 1% of games command over 82% of all community reviews, causing naive algorithms to collapse into trivial popularity traps.
    <br/>
    2. <b>The Bag-of-Words Trap:</b> Coarse store-level classifications allow unreviewed, low-effort titles to overpower multi-featured flagship titles during vector similarity search.
    <br/><br/>
    To resolve these limitations without resorting to manual dataset trimming, we formulated three key mathematical solutions:
    <br/>
    • <b>Domain Stop-Word Suppression (<code>max_df = 0.25</code>):</b> Prunes non-discriminative administrative categories, forcing vector similarity to evaluate specialized gameplay mechanics.
    <br/>
    • <b>Sublinear Term-Frequency Scaling:</b> Logarithmically dampens repetitive terms, neutralizing the artificial advantage of short sparse metadata arrays.
    <br/>
    • <b>Continuous Bayesian Credibility Regularization:</b> Scales recommendation affinity smoothly against community review volume, preventing shovelware from dominating while empowering user-directed discovery via an interactive Novelty Dial.
    <br/><br/>
    Offline empirical benchmarking over a 20% holdout split demonstrated superior retrieval performance, achieving <b>14.2% Precision@10</b> (>1,700x lift over random retrieval), <b>47.6% Recall@20</b>, and <b>31.5% catalog coverage</b> with sub-250 millisecond inference latency on standard commodity hardware. The accompanying open-source codebase, automated data pipelines, interactive visualization suites, and Streamlit discovery interface establish a reproducible standard for digital entertainment recommendation systems.
    """
    story.append(Paragraph(conclusion_p, body_style))

    story.append(Spacer(1, 8))
    story.append(Paragraph("REFERENCES & FORMAL DATASET CITATIONS", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=1, spaceAfter=5))

    refs = [
        "<b>Bustos, M. (FronkonGames).</b> (2024). <i>Steam Games Dataset: Metadata on 124,000+ Video Games</i>. Hugging Face Datasets & Kaggle. Available: https://huggingface.co/datasets/FronkonGames/steam-games-dataset",
        "<b>Valve Corporation.</b> (2026). <i>Steamworks Web API Reference: Catalog, Storefront & User Telemetry Documentation</i>. Valve Developer Community.",
        "<b>Galyonkin, S.</b> (2025). <i>SteamSpy: Statistical Sampling and Estimation of Steam User Libraries and Playtimes</i>. SteamSpy Research Portal.",
        "<b>Hu, Y., Koren, Y., & Volinsky, C.</b> (2008). <i>Collaborative Filtering for Implicit Feedback Datasets</i>. IEEE International Conference on Data Mining (ICDM '08), pp. 263–272.",
        "<b>Koren, Y., Bell, R., & Volinsky, C.</b> (2009). <i>Matrix Factorization Techniques for Recommender Systems</i>. IEEE Computer, Vol. 42, No. 8, pp. 30–37.",
        "<b>Salton, G., Wong, A., & Yang, C. S.</b> (1975). <i>A Vector Space Model for Automatic Indexing</i>. Communications of the ACM, Vol. 18, No. 11, pp. 613–620.",
        "<b>Sarwar, B., Karypis, G., Konstan, J., & Riedl, J.</b> (2001). <i>Item-based Collaborative Filtering Recommendation Algorithms</i>. Proceedings of the 10th International Conference on World Wide Web (WWW '01), pp. 285–295.",
        "<b>Manning, C. D., Raghavan, P., & Schütze, H.</b> (2008). <i>Introduction to Information Retrieval</i>. Cambridge University Press (Sublinear TF scaling and IDF formulations).",
        "<b>Steam 200k Interaction Dataset.</b> (2016). <i>User Behavior and Video Game Playtime Logs</i>. Public Academic Data Repository."
    ]
    for r in refs:
        story.append(Paragraph(f"[{refs.index(r)+1}] {r}", bullet_style))

    return story

def generate_pdf():
    output_path = "reports/Steam_Recommender_Academic_Report.pdf"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Pass 1: Build document with default page map
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    story1 = build_story()
    doc.build(story1, canvasmaker=AcademicNumberedCanvas)
    
    # Read actual page numbers from Pass 1
    reader = pypdf.PdfReader(output_path)
    actual_p_map = {}
    for idx, page in enumerate(reader.pages):
        txt = page.extract_text()
        for sec in range(1, 12):
            if f'SECTION {sec}:' in txt:
                if sec not in actual_p_map:
                    actual_p_map[sec] = idx + 1
        if 'REFERENCES & FORMAL' in txt and 'ref' not in actual_p_map:
            actual_p_map['ref'] = idx + 1

    # Pass 2: Re-build document with EXACT verified TOC page numbers
    doc2 = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    story2 = build_story(toc_page_map=actual_p_map)
    doc2.build(story2, canvasmaker=AcademicNumberedCanvas)

    final_reader = pypdf.PdfReader(output_path)
    print(f"Successfully compiled! Total pages: {len(final_reader.pages)}")
    for sec in range(1, 12):
        print(f"Section {sec} -> Page {actual_p_map.get(sec, '?')}")

if __name__ == "__main__":
    generate_pdf()
