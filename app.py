"""
Signal — Competitor Tracking Prototype
A lightweight AI agent that pulls live Amazon competitor data (price, rating,
reviews, best-seller rank) and turns it into a plain-English weekly digest.



Setup:
  1. pip install -r requirements.txt
  2. Add RAINFOREST_API_KEY and ANTHROPIC_API_KEY to .streamlit/secrets.toml
     (locally) or under "Secrets" in Streamlit Community Cloud (when deployed).
  3. streamlit run app.py
"""

import json
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Signal — Competitor Tracking", page_icon="📡", layout="wide")

RAINFOREST_API_KEY = st.secrets.get("RAINFOREST_API_KEY", "")
ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")

RAINFOREST_URL = "https://api.rainforestapi.com/request"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_product(asin: str, amazon_domain: str = "amazon.com"):
    """Pull live product data for one ASIN via Rainforest API."""
    params = {
        "api_key": RAINFOREST_API_KEY,
        "type": "product",
        "amazon_domain": amazon_domain,
        "asin": asin,
    }
    resp = requests.get(RAINFOREST_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    product = data.get("product", {})

    price = None
    if product.get("buybox_winner", {}).get("price"):
        price = product["buybox_winner"]["price"].get("value")
    elif product.get("price"):
        price = product["price"].get("value")

    rank = None
    bestsellers = product.get("bestsellers_rank", [])
    if bestsellers:
        rank = bestsellers[0].get("rank")

    return {
        "asin": asin,
        "title": product.get("title", "Unknown product"),
        "brand": product.get("brand", "—"),
        "price": price,
        "rating": product.get("rating"),
        "reviews": product.get("ratings_total"),
        "rank": rank,
        "fetched_at": datetime.utcnow().isoformat(),
    }


def generate_digest(rows: list[dict]) -> str:
    """Call Claude to turn the raw snapshot into a plain-English digest."""
    payload = [
        {
            "product": f"{r['brand']} — {r['title'][:60]}",
            "price": f"${r['price']}" if r["price"] else "unavailable",
            "rating": r["rating"],
            "reviews": r["reviews"],
            "bsr": r["rank"],
        }
        for r in rows
    ]

    prompt = (
        "You are a market intelligence analyst at an Amazon marketing agency. "
        "Given this live snapshot of competing products (JSON below), write a "
        "120-160 word plain-English read for a marketing strategist: note pricing "
        "spread, which products look strongest on reviews/rank, and one recommended "
        "watch-item. Flowing prose, no bullet points, no markdown.\n\n"
        f"Data:\n{json.dumps(payload, indent=2)}"
    )

    resp = requests.post(
        ANTHROPIC_URL,
        headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
        json={
            "model": "claude-sonnet-4-6",
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
st.title("Live competitor snapshot, read in one sitting")
st.caption(
    "Paste 3–5 competitor ASINs from the same Amazon category. This pulls live price, "
    "rating, review count, and Best Seller Rank, then generates a plain-English digest."
)

if not RAINFOREST_API_KEY or not ANTHROPIC_API_KEY:
    st.warning(
        "Missing API keys. Add `RAINFOREST_API_KEY` and `ANTHROPIC_API_KEY` under "
        "**Settings → Secrets** in Streamlit Community Cloud (or `.streamlit/secrets.toml` locally)."
    )

default_asins = "B08GC5J8QK\nB07GJTJ7VD\nB01N7T7JKJ"
asin_input = st.text_area("Competitor ASINs (one per line)", value=default_asins, height=100)
amazon_domain = st.selectbox("Marketplace", ["amazon.com", "amazon.co.uk", "amazon.de", "amazon.in"], index=0)

col1, col2 = st.columns([1, 4])
with col1:
    run = st.button("Pull live data", type="primary", use_container_width=True)

if run:
    asins = [a.strip() for a in asin_input.splitlines() if a.strip()]
    if not asins:
        st.error("Add at least one ASIN.")
    else:
        rows = []
        progress = st.progress(0.0, text="Fetching live data…")
        for i, asin in enumerate(asins):
            try:
                rows.append(fetch_product(asin, amazon_domain))
            except Exception as e:
                st.error(f"Couldn't fetch {asin}: {e}")
            progress.progress((i + 1) / len(asins))
        progress.empty()

        if rows:
            st.session_state["rows"] = rows

if "rows" in st.session_state:
    rows = st.session_state["rows"]
    df = pd.DataFrame(rows)[["brand", "title", "price", "rating", "reviews", "rank"]]
    df.columns = ["Brand", "Product", "Price ($)", "Rating", "Reviews", "BSR"]
    st.subheader("Snapshot")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Weekly digest — generated live")
    if st.button("Generate digest"):
        with st.spinner("Reading the snapshot…"):
            try:
                digest = generate_digest(rows)
                st.session_state["digest"] = digest
            except Exception as e:
                st.error(f"Couldn't generate digest: {e}")

    if "digest" in st.session_state:
        st.markdown(
            f"<div style='background:#111823;border:1px solid #232D3B;border-radius:10px;"
            f"padding:18px;line-height:1.7;'>{st.session_state['digest']}</div>",
            unsafe_allow_html=True,
        )

st.caption(
    "Prototype — live version for a real client would run this on a daily schedule and "
    "store historical snapshots to show day-over-day change, not just a single pull."
)
