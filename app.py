import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import random

# ---------------------------------------------------------------------------
# 1. Page Configuration & UI Styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Signal | Competitor Intelligence",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for a high-end "FinTech/SaaS" feel
st.markdown("""
    <style>
    /* Main background and font */
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    
    /* Metric Card Styling */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        color: #00D4FF;
    }
    
    /* Header styling */
    .main-header {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        letter-spacing: -1px;
        background: linear-gradient(90deg, #00D4FF, #0055FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        margin-bottom: 0px;
    }
    
    /* Digest Box */
    .digest-container {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 25px;
        line-height: 1.8;
        font-size: 1.1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    .status-tag {
        background: #238636;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 2. Config & Synthetic Data Engine
# ---------------------------------------------------------------------------
DAYS = 14
PRODUCTS = [
    {"name": "Glacier 32oz Insulated Bottle", "brand": "Kelvra", "price": 27.99, "rating": 4.6, "reviews": 4210, "rank": 812, "seed": 11},
    {"name": "TrailMate Steel Bottle 24oz", "brand": "Northfare", "price": 22.5, "rating": 4.4, "reviews": 8890, "rank": 340, "seed": 23},
    {"name": "Everchill Sport Flask 40oz", "brand": "Everchill", "price": 31.99, "rating": 4.7, "reviews": 2130, "rank": 1450, "seed": 37},
    {"name": "CamperPro Vacuum Bottle 20oz", "brand": "CamperPro", "price": 19.99, "rating": 4.3, "reviews": 15600, "rank": 128, "seed": 51},
    {"name": "AlpineSeal Wide Mouth 32oz", "brand": "AlpineSeal", "price": 25.0, "rating": 4.5, "reviews": 5460, "rank": 590, "seed": 67},
]

@st.cache_data(show_spinner=False)
def get_historical_data():
    all_series = []
    for p in PRODUCTS:
        rng = random.Random(p["seed"])
        price, reviews, rank = p["price"], p["reviews"], p["rank"]
        for d in range(DAYS):
            # Dynamic movement
            price += (rng.random() - 0.5) * (4 if rng.random() < 0.12 else 0.4)
            price = max(9.99, round(price, 2))
            reviews += round(rng.random() * 25 + (120 if rng.random() < 0.1 else 0))
            rank += round((rng.random() - 0.5) * (300 if rng.random() < 0.15 else 40))
            rank = max(1, rank)
            all_series.append({
                "Date": f"Day {d+1}",
                "DayNum": d,
                "Brand": p["brand"],
                "Product": p["name"],
                "Price": price,
                "Reviews": reviews,
                "BSR": rank,
                "Rating": p["rating"]
            })
    return pd.DataFrame(all_series)

data = get_historical_data()

# ---------------------------------------------------------------------------
# 3. Header Section
# ---------------------------------------------------------------------------
col_h1, col_h2 = st.columns([2, 1])

with col_h1:
    st.markdown('<p class="main-header">SIGNAL</p>', unsafe_allow_html=True)
    st.markdown("<p style='font-family:monospace; color:#8595A8; letter-spacing:2px;'>COMPETITOR INTELLIGENCE PROTOTYPE</p>", unsafe_allow_html=True)

with col_h2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<span class="status-tag">● Live Analysis Enabled</span>', unsafe_allow_html=True)
    st.caption("Category: Insulated Water Bottles · Last 14 Days")

st.divider()

# ---------------------------------------------------------------------------
# 4. Top KPIs (Market Snapshot)
# ---------------------------------------------------------------------------
latest_data = data[data["DayNum"] == DAYS-1]
first_data = data[data["DayNum"] == 0]

# Calculate aggregate stats
avg_price = latest_data["Price"].mean()
total_reviews = latest_data["Reviews"].sum()
top_performer = latest_data.loc[latest_data["BSR"].idxmin(), "Brand"]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Avg Category Price", f"${avg_price:.2f}", "-1.2%")
m2.metric("Total Tracked Reviews", f"{total_reviews:,}", "+420")
m3.metric("Current Category Leader", top_performer)
m4.metric("Market Volatility", "Medium", "Price Elasticity High")

# ---------------------------------------------------------------------------
# 5. Visual Intelligence (Graphs)
# ---------------------------------------------------------------------------
st.subheader("Market Dynamics")
tab1, tab2, tab3 = st.tabs(["📈 Price Trends", "🏆 Rank Movement (BSR)", "📊 Review Growth"])

with tab1:
    fig_price = px.line(data, x="Date", y="Price", color="Brand", 
                        markers=True, template="plotly_dark",
                        color_discrete_sequence=px.colors.qualitative.Safe)
    fig_price.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_price, use_container_width=True)

with tab2:
    # We invert the Y-axis for BSR because 1 is better than 1000
    fig_rank = px.line(data, x="Date", y="BSR", color="Brand", 
                       markers=True, template="plotly_dark",
                       color_discrete_sequence=px.colors.qualitative.Safe)
    fig_rank.update_yaxes(autorange="reversed")
    fig_rank.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_rank, use_container_width=True)

with tab3:
    fig_rev = px.area(data, x="Date", y="Reviews", color="Brand", 
                      template="plotly_dark",
                      color_discrete_sequence=px.colors.qualitative.Vivid)
    fig_rev.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_rev, use_container_width=True)

# ---------------------------------------------------------------------------
# 6. AI Digest & Data Table
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([1, 1.5])

with col_left:
    st.subheader("Weekly Intelligence Digest")
    digest_text = (
        "**Price War Alert:** **Northfare** initiated a aggressive -12% price correction on Day 4, "
        "successfully reclaiming the #2 BSR position within 48 hours. <br><br>"
        "**Growth Signal:** **CamperPro** is seeing anomalous review growth (+8% vs category avg), "
        "suggesting a high-spend Vine campaign or off-Amazon influencer push. <br><br>"
        "**Inventory Risk:** **Everchill's** rank decay correlates with their price premium. "
        "If they don't adjust to the $25.00 anchor set by AlpineSeal, further market share loss is projected."
    )
    st.markdown(f"""
        <div class="digest-container">
            {digest_text}
        </div>
    """, unsafe_allow_html=True)

with col_right:
    st.subheader("Raw Competitive Snapshot")
    # Clean up dataframe for display
    display_df = latest_data[["Brand", "Product", "Price", "Reviews", "BSR"]].copy()
    
    # Calculate simple delta for the table
    price_deltas = latest_data["Price"].values - first_data["Price"].values
    display_df["14d Change"] = [f"{'+' if x>0 else ''}{x:.2f}" for x in price_deltas]
    
    st.dataframe(
        display_df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Price": st.column_config.NumberColumn(format="$%.2f"),
            "Reviews": st.column_config.NumberColumn(format="%d"),
            "BSR": st.column_config.NumberColumn(format="#%d"),
        }
    )

# ---------------------------------------------------------------------------
# 7. Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption("PROTOTYPE VERSION 1.2 — SYSTEM RUNNING ON SYNTHETIC AMAZON PA-API REPLICA")
