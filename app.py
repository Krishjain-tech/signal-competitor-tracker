"""
Signal — Competitor Tracking Prototype
A lightweight tool that tracks Amazon competitor data (price, rating,
reviews, best-seller rank) and turns it into a plain-English weekly digest.

This demo version uses realistic synthetic data and shows a sample digest
rather than generating one live, so it runs free with no API costs. A
funded version generates the digest on demand from live data.

Setup:
  1. pip install -r requirements.txt
  2. streamlit run app.py
"""

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Signal — Competitor Tracking", page_icon="📡", layout="wide")

DAYS = 14

PRODUCTS = [
    {"name": "Glacier 32oz Insulated Bottle", "brand": "Kelvra", "price": 27.99, "rating": 4.6, "reviews": 4210, "rank": 812, "seed": 11},
    {"name": "TrailMate Steel Bottle 24oz", "brand": "Northfare", "price": 22.5, "rating": 4.4, "reviews": 8890, "rank": 340, "seed": 23},
    {"name": "Everchill Sport Flask 40oz", "brand": "Everchill", "price": 31.99, "rating": 4.7, "reviews": 2130, "rank": 1450, "seed": 37},
    {"name": "CamperPro Vacuum Bottle 20oz", "brand": "CamperPro", "price": 19.99, "rating": 4.3, "reviews": 15600, "rank": 128, "seed": 51},
    {"name": "AlpineSeal Wide Mouth 32oz", "brand": "AlpineSeal", "price": 25.0, "rating": 4.5, "reviews": 5460, "rank": 590, "seed": 67},
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

# ---------------------------------------------------------------------------
# Synthetic data generation (deterministic per product via seed)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def build_series():
    import random
    all_rows = []
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
            history.append({"day": d + 1, "price": price, "reviews": reviews, "rank": rank})
        all_rows.append({**p, "history": history})
    return all_rows


def snapshot_rows(series):
    rows = []
    for p in series:
        first, last = p["history"][0], p["history"][-1]
        rows.append({
            "brand": p["brand"],
            "title": p["name"],
            "price": last["price"],
            "price_delta": round(last["price"] - first["price"], 2),
            "rating": p["rating"],
            "reviews": last["reviews"],
            "reviews_delta": last["reviews"] - first["reviews"],
            "rank": last["rank"],
            "rank_delta": last["rank"] - first["rank"],
        })
    return rows


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.markdown(
    "<span style='font-family:monospace;letter-spacing:2px;color:#8595A8;'>SIGNAL — COMPETITOR TRACKING PROTOTYPE</span>",
    unsafe_allow_html=True,
)
st.title("Fourteen days of competitor movement, read in one sitting")
st.caption(
    "Category: Insulated Water Bottles · 5 tracked competitors. Data below is synthetic "
    "for this demo. The digest is a representative sample — the live version generates "
    "one on demand from real tracked changes."
)

series = build_series()
rows = snapshot_rows(series)

df = pd.DataFrame(rows)[["brand", "title", "price", "price_delta", "rating", "reviews", "reviews_delta", "rank", "rank_delta"]]
df.columns = ["Brand", "Product", "Price ($)", "Δ 14d ($)", "Rating", "Reviews", "Δ 14d", "BSR", "Δ 14d "]

st.subheader("Snapshot")
st.dataframe(df, use_container_width=True, hide_index=True)

st.subheader("Weekly digest — sample output")
st.markdown(
    f"<div style='background:#111823;border:1px solid #232D3B;border-radius:10px;"
    f"padding:18px;line-height:1.7;color:#E7ECF2;'>{SAMPLE_DIGEST}</div>",
    unsafe_allow_html=True,
)

st.caption(
    "Prototype — data above is synthetic for this demo. A production version pulls live "
    "pricing, reviews, and BSR via the Amazon Product Advertising API or a provider such "
    "as Rainforest/Keepa, and generates a fresh digest on demand from real day-over-day "
    "change."
)
