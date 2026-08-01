"""
Signal — Competitor Tracking Dashboard
A modern SaaS-style Streamlit dashboard that tracks Amazon competitor data
(price, rating, reviews, best-seller rank) and turns it into a plain-English
weekly digest.

This demo version uses realistic synthetic data and shows a sample digest
rather than generating one live, so it runs free with no API costs. A
funded version generates the digest on demand from live data.

Setup:
    1. pip install -r requirements.txt
    2. streamlit run app.py
"""

import random
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Signal — Competitor Tracking",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

DAYS = 30  # max days of history we generate; sidebar slider trims this down

PRODUCTS = [
    {"name": "Glacier 32oz Insulated Bottle", "brand": "Kelvra", "price": 27.99, "rating": 4.6, "reviews": 4210, "rank": 812, "seed": 11},
    {"name": "TrailMate Steel Bottle 24oz", "brand": "Northfare", "price": 22.5, "rating": 4.4, "reviews": 8890, "rank": 340, "seed": 23},
    {"name": "Everchill Sport Flask 40oz", "brand": "Everchill", "price": 31.99, "rating": 4.7, "reviews": 2130, "rank": 1450, "seed": 37},
    {"name": "CamperPro Vacuum Bottle 20oz", "brand": "CamperPro", "price": 19.99, "rating": 4.3, "reviews": 15600, "rank": 128, "seed": 51},
    {"name": "AlpineSeal Wide Mouth 32oz", "brand": "AlpineSeal", "price": 25.0, "rating": 4.5, "reviews": 5460, "rank": 590, "seed": 67},
    {"name": "SummitFlow Copper Bottle 26oz", "brand": "SummitFlow", "price": 29.49, "rating": 4.5, "reviews": 3320, "rank": 970, "seed": 79},
]

SAMPLE_DIGEST = (
    "The clearest move this period came from Northfare, which cut price by roughly "
    "$2.40 while holding review growth steady — a signal worth watching if it "
    "continues into next week. CamperPro's review count grew faster than the rest "
    "of the set, suggesting a recent traffic or promotion push rather than organic "
    "drift. Everchill's rank slipped the most of the group, likely tied to its "
    "higher price point relative to competitors moving downward. Recommended watch "
    "item: track whether Northfare's price cut correlates with a rank improvement "
    "over the next reporting cycle — that would confirm price elasticity in this "
    "category."
)

# Color palette used across CSS + charts for a consistent brand feel
PALETTE = {
    "bg": "#0B0F17",
    "panel": "rgba(255,255,255,0.04)",
    "border": "rgba(255,255,255,0.09)",
    "text": "#E7ECF2",
    "muted": "#8595A8",
    "accent1": "#7C5CFF",
    "accent2": "#22D3EE",
    "good": "#34D399",
    "bad": "#FB7185",
    "warn": "#FBBF24",
}

CHART_COLORS = ["#7C5CFF", "#22D3EE", "#FB7185", "#FBBF24", "#34D399", "#F472B6"]


# ---------------------------------------------------------------------------
# Custom CSS — glassmorphism, gradient header, rounded cards, hover effects
# ---------------------------------------------------------------------------
def inject_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        .stApp {{
            background:
                radial-gradient(circle at 15% 0%, rgba(124,92,255,0.16), transparent 45%),
                radial-gradient(circle at 85% 10%, rgba(34,211,238,0.12), transparent 40%),
                {PALETTE['bg']};
            color: {PALETTE['text']};
        }}

        /* Hide default streamlit chrome for a cleaner SaaS look */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header[data-testid="stHeader"] {{background: transparent;}}

        /* ---------------- Gradient Hero Header ---------------- */
        .signal-hero {{
            position: relative;
            padding: 34px 38px;
            border-radius: 22px;
            margin-bottom: 26px;
            overflow: hidden;
            background: linear-gradient(120deg, rgba(124,92,255,0.35), rgba(34,211,238,0.22) 60%, rgba(251,113,133,0.18));
            border: 1px solid {PALETTE['border']};
            box-shadow: 0 20px 60px -20px rgba(124,92,255,0.45);
            animation: fadeInDown 0.6s ease;
        }}
        .signal-hero::after {{
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at 90% -10%, rgba(255,255,255,0.15), transparent 55%);
            pointer-events: none;
        }}
        .signal-kicker {{
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 3px;
            font-size: 12px;
            color: {PALETTE['accent2']};
            text-transform: uppercase;
            font-weight: 500;
        }}
        .signal-title {{
            font-size: 40px;
            font-weight: 800;
            margin: 8px 0 6px 0;
            background: linear-gradient(90deg, #FFFFFF, #C7D2FE 65%, {PALETTE['accent2']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .signal-subtitle {{
            color: {PALETTE['muted']};
            font-size: 15px;
            max-width: 720px;
            line-height: 1.6;
        }}
        .signal-pill-row {{
            margin-top: 16px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .signal-pill {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            padding: 6px 14px;
            border-radius: 999px;
            background: rgba(255,255,255,0.08);
            border: 1px solid {PALETTE['border']};
            color: {PALETTE['text']};
        }}

        /* ---------------- Glass Cards ---------------- */
        .glass-card {{
            background: {PALETTE['panel']};
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid {PALETTE['border']};
            border-radius: 18px;
            padding: 22px 22px;
            transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
            animation: fadeInUp 0.5s ease;
        }}
        .glass-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 18px 40px -18px rgba(124,92,255,0.55);
            border-color: rgba(124,92,255,0.55);
        }}

        /* ---------------- KPI Cards ---------------- */
        .kpi-card {{
            background: {PALETTE['panel']};
            backdrop-filter: blur(14px);
            border: 1px solid {PALETTE['border']};
            border-radius: 18px;
            padding: 20px 22px;
            transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
            height: 100%;
            animation: fadeInUp 0.55s ease;
        }}
        .kpi-card:hover {{
            transform: translateY(-5px) scale(1.01);
            box-shadow: 0 18px 44px -18px rgba(34,211,238,0.5);
            border-color: rgba(34,211,238,0.5);
        }}
        .kpi-label {{
            font-size: 12px;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: {PALETTE['muted']};
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .kpi-value {{
            font-size: 30px;
            font-weight: 800;
            margin-top: 10px;
            color: {PALETTE['text']};
        }}
        .kpi-delta-good {{ color: {PALETTE['good']}; font-weight: 600; font-size: 13px; margin-top: 6px; }}
        .kpi-delta-bad {{ color: {PALETTE['bad']}; font-weight: 600; font-size: 13px; margin-top: 6px; }}
        .kpi-delta-neutral {{ color: {PALETTE['muted']}; font-weight: 600; font-size: 13px; margin-top: 6px; }}

        /* ---------------- Section headers ---------------- */
        .section-title {{
            font-size: 21px;
            font-weight: 700;
            margin: 6px 0 14px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .section-sub {{
            color: {PALETTE['muted']};
            font-size: 13px;
            margin-top: -10px;
            margin-bottom: 16px;
        }}

        /* ---------------- AI Insight Card ---------------- */
        .ai-card {{
            position: relative;
            background: linear-gradient(135deg, rgba(124,92,255,0.20), rgba(34,211,238,0.10));
            border: 1px solid rgba(124,92,255,0.45);
            border-radius: 20px;
            padding: 26px 28px;
            line-height: 1.75;
            font-size: 15px;
            color: {PALETTE['text']};
            box-shadow: 0 20px 55px -25px rgba(124,92,255,0.6);
            animation: glowPulse 4s ease-in-out infinite;
        }}
        .ai-card-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            padding: 5px 12px;
            border-radius: 999px;
            background: rgba(124,92,255,0.25);
            border: 1px solid rgba(124,92,255,0.5);
            margin-bottom: 14px;
        }}

        /* ---------------- Status badges ---------------- */
        .badge-up {{
            background: rgba(52,211,153,0.15);
            color: {PALETTE['good']};
            border: 1px solid rgba(52,211,153,0.4);
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
        }}
        .badge-down {{
            background: rgba(251,113,133,0.15);
            color: {PALETTE['bad']};
            border: 1px solid rgba(251,113,133,0.4);
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
        }}
        .badge-flat {{
            background: rgba(251,191,36,0.15);
            color: {PALETTE['warn']};
            border: 1px solid rgba(251,191,36,0.4);
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
        }}

        /* ---------------- Sidebar ---------------- */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #0D1220, #0A0E17);
            border-right: 1px solid {PALETTE['border']};
        }}
        section[data-testid="stSidebar"] .stMarkdown h3 {{
            color: {PALETTE['accent2']};
        }}

        /* ---------------- Dataframe ---------------- */
        [data-testid="stDataFrame"] {{
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid {PALETTE['border']};
        }}

        /* ---------------- Buttons ---------------- */
        .stDownloadButton button, .stButton button {{
            background: linear-gradient(90deg, {PALETTE['accent1']}, {PALETTE['accent2']});
            color: #0B0F17;
            font-weight: 700;
            border: none;
            border-radius: 12px;
            padding: 10px 20px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .stDownloadButton button:hover, .stButton button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 14px 30px -12px rgba(124,92,255,0.7);
        }}

        /* ---------------- Footer ---------------- */
        .signal-footer {{
            text-align: center;
            padding: 26px 0 8px 0;
            color: {PALETTE['muted']};
            font-size: 13px;
            border-top: 1px solid {PALETTE['border']};
            margin-top: 34px;
        }}

        /* ---------------- Animations ---------------- */
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(14px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes fadeInDown {{
            from {{ opacity: 0; transform: translateY(-14px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes glowPulse {{
            0%, 100% {{ box-shadow: 0 20px 55px -25px rgba(124,92,255,0.6); }}
            50% {{ box-shadow: 0 20px 65px -20px rgba(34,211,238,0.55); }}
        }}

        /* Responsive tweaks */
        @media (max-width: 768px) {{
            .signal-title {{ font-size: 28px; }}
            .signal-hero {{ padding: 22px 20px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Synthetic data generation (deterministic per product via seed)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def build_series():
    """Generate deterministic synthetic daily history for every tracked product."""
    all_rows = []
    today = datetime.today()
    for p in PRODUCTS:
        rng = random.Random(p["seed"])
        price, reviews, rank = p["price"], p["reviews"], p["rank"]
        history = []
        for d in range(DAYS):
            price += (rng.random() - 0.5) * (4 if rng.random() < 0.12 else 0.4)
            price = max(9.99, round(price, 2))
            reviews += round(rng.random() * 25 + (120 if rng.random() < 0.1 else 0))
            rank += round((rng.random() - 0.5) * (300 if rng.random() < 0.15 else 40))
            rank = max(1, rank)
            history.append(
                {
                    "day": d + 1,
                    "date": (today - timedelta(days=DAYS - d - 1)).strftime("%Y-%m-%d"),
                    "price": price,
                    "reviews": reviews,
                    "rank": rank,
                }
            )
        all_rows.append({**p, "history": history})
    return all_rows


def trim_history(series, window_days):
    """Return a copy of the series trimmed to the last `window_days` days."""
    trimmed = []
    for p in series:
        h = p["history"][-window_days:]
        trimmed.append({**p, "history": h})
    return trimmed


def snapshot_rows(series):
    """Build the latest-vs-first snapshot used in the table & KPI cards."""
    rows = []
    for p in series:
        first, last = p["history"][0], p["history"][-1]
        rows.append(
            {
                "brand": p["brand"],
                "title": p["name"],
                "price": last["price"],
                "price_delta": round(last["price"] - first["price"], 2),
                "rating": p["rating"],
                "reviews": last["reviews"],
                "reviews_delta": last["reviews"] - first["reviews"],
                "rank": last["rank"],
                "rank_delta": last["rank"] - first["rank"],
            }
        )
    return rows


def status_badge(price_delta, rank_delta):
    """Return an HTML badge summarizing whether a product is trending up/down/flat."""
    score = (-price_delta * 2) + (-rank_delta * 0.02)
    if score > 1.5:
        return "<span class='badge-up'>▲ Improving</span>"
    elif score < -1.5:
        return "<span class='badge-down'>▼ Slipping</span>"
    return "<span class='badge-flat'>● Steady</span>"


# ---------------------------------------------------------------------------
# UI sections
# ---------------------------------------------------------------------------
def render_hero():
    st.markdown(
        f"""
        <div class="signal-hero">
            <div class="signal-kicker">📡 SIGNAL — COMPETITOR TRACKING PROTOTYPE</div>
            <div class="signal-title">Competitor movement, read in one sitting</div>
            <div class="signal-subtitle">
                Track price, rating, reviews, and Best Seller Rank across your category —
                and get a plain-English weekly digest instead of a wall of spreadsheets.
                Data below is synthetic for this demo; the live version pulls real
                day-over-day change.
            </div>
            <div class="signal-pill-row">
                <span class="signal-pill">🏷️ Category: Insulated Water Bottles</span>
                <span class="signal-pill">🧭 {len(PRODUCTS)} Competitors Tracked</span>
                <span class="signal-pill">⚡ No paid APIs · synthetic data</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpis(rows):
    st.markdown("<div class='section-title'>📊 Key Metrics</div>", unsafe_allow_html=True)

    if not rows:
        st.info("No products match the current filters.")
        return

    n_products = len(rows)
    avg_rating = sum(r["rating"] for r in rows) / n_products
    biggest_drop = min(rows, key=lambda r: r["price_delta"])
    fastest_growth = max(rows, key=lambda r: r["reviews_delta"])

    cols = st.columns(4)
    kpi_data = [
        ("📦", "Tracked Products", f"{n_products}", f"across {len({r['brand'] for r in rows})} brands", "neutral"),
        ("⭐", "Average Rating", f"{avg_rating:.2f} / 5", "weighted across selection", "good" if avg_rating >= 4.4 else "neutral"),
        ("💸", "Largest Price Drop", f"${biggest_drop['price_delta']:.2f}", biggest_drop["brand"], "good" if biggest_drop["price_delta"] < 0 else "neutral"),
        ("🚀", "Fastest Review Growth", f"+{fastest_growth['reviews_delta']}", fastest_growth["brand"], "good"),
    ]

    for col, (icon, label, value, sub, tone) in zip(cols, kpi_data):
        delta_class = {"good": "kpi-delta-good", "bad": "kpi-delta-bad", "neutral": "kpi-delta-neutral"}[tone]
        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">{icon} {label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="{delta_class}">{sub}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def hex_to_rgba(hex_color, alpha=0.1):
    """Convert a '#RRGGBB' hex color string to an 'rgba(r,g,b,a)' string."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def plotly_layout(fig, title, y_reversed=False):
    """Apply a shared dark theme + styling to every Plotly figure."""
    fig.update_layout(
        template="plotly_dark",
        title=dict(text=title, font=dict(size=16, family="Inter", color=PALETTE["text"])),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color=PALETTE["text"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=60, b=10),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.06)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.06)")
    if y_reversed:
        fig.update_yaxes(autorange="reversed")
    return fig


def render_charts(series):
    st.markdown("<div class='section-title'>📈 Trends</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-sub'>Hover any chart to inspect exact values. All charts respect the sidebar filters.</div>",
        unsafe_allow_html=True,
    )

    if not series:
        st.info("No products match the current filters.")
        return

    # ---- Price trend ----
    fig_price = go.Figure()
    for i, p in enumerate(series):
        df_h = pd.DataFrame(p["history"])
        fig_price.add_trace(
            go.Scatter(
                x=df_h["day"], y=df_h["price"], mode="lines+markers", name=p["brand"],
                line=dict(color=CHART_COLORS[i % len(CHART_COLORS)], width=3),
                marker=dict(size=4),
            )
        )
    plotly_layout(fig_price, "💰 Price Trend (per day)")

    # ---- Reviews growth ----
    fig_reviews = go.Figure()
    for i, p in enumerate(series):
        df_h = pd.DataFrame(p["history"])
        line_color = CHART_COLORS[i % len(CHART_COLORS)]
        fig_reviews.add_trace(
            go.Scatter(
                x=df_h["day"], y=df_h["reviews"], mode="lines", name=p["brand"],
                line=dict(color=line_color, width=3),
                fill="tozeroy", fillcolor=hex_to_rgba(line_color, 0.08),
            )
        )
    plotly_layout(fig_reviews, "⭐ Review Count Growth")

    # ---- Rank trend (reverse axis: rank 1 = best) ----
    fig_rank = go.Figure()
    for i, p in enumerate(series):
        df_h = pd.DataFrame(p["history"])
        fig_rank.add_trace(
            go.Scatter(
                x=df_h["day"], y=df_h["rank"], mode="lines+markers", name=p["brand"],
                line=dict(color=CHART_COLORS[i % len(CHART_COLORS)], width=3),
                marker=dict(size=4),
            )
        )
    plotly_layout(fig_rank, "🏆 Best Seller Rank Trend (lower is better)", y_reversed=True)

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.plotly_chart(fig_price, use_container_width=True)
    with row1_col2:
        st.plotly_chart(fig_reviews, use_container_width=True)

    st.plotly_chart(fig_rank, use_container_width=True)

    # ---- Price distribution + review growth bar chart ----
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        latest_prices = [p["history"][-1]["price"] for p in series]
        brands = [p["brand"] for p in series]

        # Box trace shows the overall spread; a single color is required here
        # (Plotly box traces don't support per-point marker colors).
        fig_dist = go.Figure()
        fig_dist.add_trace(
            go.Box(
                y=latest_prices,
                x=["All Products"] * len(latest_prices),
                name="Spread",
                boxpoints=False,
                marker=dict(color=PALETTE["accent1"]),
                line=dict(color=PALETTE["accent1"]),
                fillcolor="rgba(124,92,255,0.12)",
                showlegend=False,
            )
        )
        # Overlay each product as its own colored point (this is where
        # per-brand coloring actually belongs).
        for i, (brand, price) in enumerate(zip(brands, latest_prices)):
            fig_dist.add_trace(
                go.Scatter(
                    x=["All Products"],
                    y=[price],
                    mode="markers",
                    name=brand,
                    marker=dict(size=12, color=CHART_COLORS[i % len(CHART_COLORS)], line=dict(width=1, color="#0B0F17")),
                    hovertemplate=f"{brand}<br>$%{{y:.2f}}<extra></extra>",
                )
            )
        plotly_layout(fig_dist, "📦 Current Price Distribution")
        fig_dist.update_xaxes(title=None)
        fig_dist.update_yaxes(title="Price ($)")
        st.plotly_chart(fig_dist, use_container_width=True)

    with row2_col2:
        growth = [p["history"][-1]["reviews"] - p["history"][0]["reviews"] for p in series]
        fig_bar = go.Figure(
            go.Bar(
                x=brands,
                y=growth,
                marker=dict(color=CHART_COLORS[: len(brands)], line=dict(width=0)),
                text=[f"+{g}" for g in growth],
                textposition="outside",
            )
        )
        plotly_layout(fig_bar, "🚀 Review Growth by Brand (window total)")
        fig_bar.update_yaxes(title="New Reviews")
        st.plotly_chart(fig_bar, use_container_width=True)


def render_snapshot_table(rows):
    st.markdown("<div class='section-title'>🗂️ Snapshot</div>", unsafe_allow_html=True)

    if not rows:
        st.info("No products match the current filters.")
        return pd.DataFrame()

    table_rows = []
    for r in rows:
        table_rows.append(
            {
                "Brand": r["brand"],
                "Product": r["title"],
                "Price ($)": r["price"],
                "Rating": r["rating"],
                "Reviews": r["reviews"],
                "BSR": r["rank"],
                "Status": status_badge(r["price_delta"], r["rank_delta"]),
                "Δ Price": f"{'+' if r['price_delta'] >= 0 else ''}{r['price_delta']:.2f}",
                "Δ Reviews": f"{'+' if r['reviews_delta'] >= 0 else ''}{r['reviews_delta']}",
            }
        )
    df = pd.DataFrame(table_rows)

    # Render as HTML so status badges display as colored pills
    st.markdown(
        f"""
        <div class="glass-card" style="padding:0; overflow-x:auto;">
        {df.to_html(escape=False, index=False, classes="signal-table")}
        </div>
        <style>
        .signal-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        .signal-table th {{
            text-align: left;
            padding: 14px 16px;
            color: {PALETTE['muted']};
            font-weight: 600;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 1px;
            border-bottom: 1px solid {PALETTE['border']};
        }}
        .signal-table td {{
            padding: 12px 16px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }}
        .signal-table tr:hover td {{
            background: rgba(255,255,255,0.03);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Return a clean (non-HTML) dataframe for CSV export
    export_rows = []
    for r in rows:
        export_rows.append(
            {
                "Brand": r["brand"],
                "Product": r["title"],
                "Price ($)": r["price"],
                "Rating": r["rating"],
                "Reviews": r["reviews"],
                "BSR": r["rank"],
                "Price Change ($)": r["price_delta"],
                "Review Change": r["reviews_delta"],
                "Rank Change": r["rank_delta"],
            }
        )
    return pd.DataFrame(export_rows)


def render_digest():
    st.markdown("<div class='section-title'>🤖 AI Weekly Digest</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="ai-card">
            <div class="ai-card-badge">✨ AI-Generated Insight — Sample Output</div>
            {SAMPLE_DIGEST}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        "Prototype note: this digest is a representative sample. A production build "
        "generates a fresh digest on demand from real day-over-day tracked changes."
    )


def render_comparison(rows):
    st.markdown("<div class='section-title'>⚖️ Product Comparison</div>", unsafe_allow_html=True)

    if len(rows) < 2:
        st.info("Select at least two products in the sidebar to compare them.")
        return

    options = [f"{r['brand']} — {r['title']}" for r in rows]
    col_a, col_b = st.columns(2)
    with col_a:
        pick_a = st.selectbox("Product A", options, index=0, key="cmp_a")
    with col_b:
        default_b = 1 if len(options) > 1 else 0
        pick_b = st.selectbox("Product B", options, index=default_b, key="cmp_b")

    row_a = rows[options.index(pick_a)]
    row_b = rows[options.index(pick_b)]

    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💵 Price", f"${row_a['price']:.2f}", f"{row_a['price'] - row_b['price']:+.2f} vs B")
    m2.metric("⭐ Rating", f"{row_a['rating']:.1f}", f"{row_a['rating'] - row_b['rating']:+.1f} vs B")
    m3.metric("📝 Reviews", f"{row_a['reviews']:,}", f"{row_a['reviews'] - row_b['reviews']:+,} vs B")
    m4.metric("🏆 BSR", f"{row_a['rank']:,}", f"{row_b['rank'] - row_a['rank']:+,} better" if row_a["rank"] < row_b["rank"] else f"{row_a['rank'] - row_b['rank']:+,} worse")
    st.markdown("</div>", unsafe_allow_html=True)


def render_footer():
    st.markdown(
        "<div class='signal-footer'>Built with Streamlit + Plotly ⚡ · Signal Prototype · Synthetic data for demo purposes</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
def render_sidebar(series):
    st.sidebar.markdown("### 🎛️ Filters")

    all_brands = sorted({p["brand"] for p in series})
    selected_brands = st.sidebar.multiselect("🏷️ Brand", all_brands, default=all_brands)

    filtered_by_brand = [p for p in series if p["brand"] in selected_brands]
    all_titles = sorted({p["name"] for p in filtered_by_brand})
    selected_titles = st.sidebar.multiselect("📦 Product", all_titles, default=all_titles)

    st.sidebar.markdown("### ⏱️ Time Range")
    window_days = st.sidebar.slider("Days of history", min_value=3, max_value=DAYS, value=14, step=1)

    st.sidebar.markdown("### 🔍 Search")
    search_term = st.sidebar.text_input("Search by product or brand name", "")

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "📡 **Signal** tracks price, rating, reviews, and Best Seller Rank for your "
        "category and turns it into a plain-English weekly digest — no spreadsheets required."
    )

    return selected_brands, selected_titles, window_days, search_term


def apply_filters(series, selected_brands, selected_titles, search_term):
    filtered = [p for p in series if p["brand"] in selected_brands and p["name"] in selected_titles]
    if search_term.strip():
        term = search_term.strip().lower()
        filtered = [p for p in filtered if term in p["name"].lower() or term in p["brand"].lower()]
    return filtered


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    inject_css()
    render_hero()

    full_series = build_series()
    selected_brands, selected_titles, window_days, search_term = render_sidebar(full_series)

    filtered_series = apply_filters(full_series, selected_brands, selected_titles, search_term)
    windowed_series = trim_history(filtered_series, window_days)
    rows = snapshot_rows(windowed_series)

    render_kpis(rows)
    st.write("")
    render_charts(windowed_series)
    st.write("")
    export_df = render_snapshot_table(rows)

    if not export_df.empty:
        st.download_button(
            label="⬇️ Download Snapshot as CSV",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name="signal_competitor_snapshot.csv",
            mime="text/csv",
        )

    st.write("")
    render_digest()
    st.write("")
    render_comparison(rows)

    render_footer()


if __name__ == "__main__":
    main()
