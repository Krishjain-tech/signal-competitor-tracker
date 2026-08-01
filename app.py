"""
Signal — Competitor Tracking Prototype
A lightweight AI agent that tracks Amazon competitor data (price, rating,
reviews, best-seller rank) and turns it into a plain-English weekly digest
using an AI language model.

This demo version uses realistic synthetic data so it works without any
paid data API. The digest generation below is fully live — it calls an
AI model in real time, it isn't scripted.

Setup:
  1. pip install -r requirements.txt
  2. Add ANTHROPIC_API_KEY to .streamlit/secrets.toml (locally) or under
     "Secrets" in Streamlit Community Cloud (when deployed).
  3. streamlit run app.py
"""

import json
import random

import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Signal — Competitor Tracking", page_icon="📡", layout="wide")

ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

DAYS = 14

PRODUCTS = [
    {"name": "Glacier 32oz Insulated Bottle", "brand": "Kelvra", "price": 27.99, "rating": 4.6, "reviews": 4210, "rank": 812, "seed": 11},
    {"name": "TrailMate Steel Bottle 24oz", "brand": "Northfare", "price": 22.5, "rating": 4.4, "reviews": 8890, "rank": 340, "seed": 23},
    {"name": "Everchill Sport Flask 40oz", "brand": "Everchill", "price": 31.99, "rating": 4.7, "reviews": 2130, "rank": 1450, "seed": 37},
    {"name": "CamperPro Vacuum Bottle 20oz", "brand": "CamperPro", "price": 19.99, "rating": 4.3, "reviews": 15600, "rank": 128, "seed": 51},
    {"name": "AlpineSeal Wide Mouth 32oz", "brand": "AlpineSeal", "price": 25.0, "rating": 4.5, "reviews": 5460, "rank": 590, "seed": 67},
]

# ---------------------------------------------------------------------------
# Synthetic data generation (deterministic per product via seed)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def build_series():
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


def generate_digest(rows: list) -> str:
    """Call the AI model to turn the snapshot + 14-day deltas into a plain-English digest."""
    payload = [
        {
            "product": f"{r['brand']} — {r['title']}",
            "price": f"${r['price']}", "price_change_14d": r["price_delta"],
            "rating": r["rating"],
            "reviews": r["reviews"], "review_change_14d": r["reviews_delta"],
            "bsr": r["rank"], "bsr_change_14d": r["rank_delta"],
        }
        for r in rows
    ]

    prompt = (
        "You are a market intelligence analyst at an Amazon marketing agency. "
        "Given this 14-day competitive snapshot (JSON below), write a 120-160 "
        "word plain-English digest for a marketing strategist: call out the "
        "2-3 most important moves, note any pattern across competitors, and "
        "end with one recommended action. Flowing prose, no bullet points, "
        "no markdown.\n\n"
        f"Data:\n{json.dumps(payload, indent=2)}"
    )

    resp = requests.post(
        ANTHROPIC_URL,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        json={
            "model": "claude-sonnet-5",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
    return "\n".join(text_blocks).strip()


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
    "for this demo — the digest underneath it is generated live by AI, not scripted."
)

if not ANTHROPIC_API_KEY:
    st.warning(
        "Missing API key. Add `ANTHROPIC_API_KEY` under **Settings → Secrets** in "
        "Streamlit Community Cloud (or `.streamlit/secrets.toml` locally)."
    )

series = build_series()
rows = snapshot_rows(series)

df = pd.DataFrame(rows)[["brand", "title", "price", "price_delta", "rating", "reviews", "reviews_delta", "rank", "rank_delta"]]
df.columns = ["Brand", "Product", "Price ($)", "Δ 14d ($)", "Rating", "Reviews", "Δ 14d", "BSR", "Δ 14d "]

st.subheader("Snapshot")
st.dataframe(df, use_container_width=True, hide_index=True)

st.subheader("Weekly digest — generated live")
if st.button("Generate digest", type="primary"):
    with st.spinner("Reading the week's changes…"):
        try:
            digest = generate_digest(rows)
            st.session_state["digest"] = digest
        except Exception as e:
            st.error(f"Couldn't generate digest: {e}")

if "digest" in st.session_state:
    st.markdown(
        f"<div style='background:#111823;border:1px solid #232D3B;border-radius:10px;"
        f"padding:18px;line-height:1.7;color:#E7ECF2;'>{st.session_state['digest']}</div>",
        unsafe_allow_html=True,
    )

st.caption(
    "Prototype — data above is synthetic for this demo. A production version pulls live "
    "pricing, reviews, and BSR via the Amazon Product Advertising API or a provider such "
    "as Rainforest/Keepa, refreshed on a daily schedule to show real day-over-day change."
)
