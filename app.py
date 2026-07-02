"""
Nifty 50 Stock Performance Dashboard
Streamlit application implementing all analysis requirements from the project brief.

Run with:
    streamlit run app.py
"""

import os
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))
import analysis as an  # noqa: E402

# ---------------------------------------------------------------------------
# Page config & theme
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Nifty 50 Stock Performance Dashboard",
    page_icon="📈",
    layout="wide",
)

GREEN = "#1B7A43"
RED = "#C0392B"
ACCENT = "#2C5F8A"

st.markdown(
    """
    <style>
    .metric-card {
        background-color: #F7F9FB;
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid #E3E8EE;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------

DB_URL = "sqlite:///" + os.path.join(os.path.dirname(__file__), "..", "sql", "stock_data.db")


@st.cache_resource
def get_engine():
    return an.get_engine(DB_URL)


@st.cache_data
def load_data():
    engine = get_engine()
    prices = an.load_prices(engine)
    sector_map = an.load_sector_map(engine)
    return prices, sector_map


prices, sector_map = load_data()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.title("📈 Nifty 50 Dashboard")
st.sidebar.markdown(
    f"**Data range:** {prices['date'].min().date()} → {prices['date'].max().date()}  \n"
    f"**Symbols:** {prices['symbol'].nunique()}  \n"
    f"**Trading days:** {prices['date'].nunique()}"
)

page = st.sidebar.radio(
    "Section",
    [
        "Market Overview",
        "Top Gainers & Losers",
        "Volatility Analysis",
        "Cumulative Returns",
        "Sector Performance",
        "Price Correlation",
        "Monthly Gainers & Losers",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption("Data source: NSE Nifty 50 daily OHLCV, Oct 2023 – Nov 2024")

# ---------------------------------------------------------------------------
# Market Overview
# ---------------------------------------------------------------------------

if page == "Market Overview":
    st.title("Market Overview")
    summary = an.market_summary(prices)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Green Stocks", f"{summary['green_stocks']}", f"{summary['green_pct']}%")
    c2.metric("Red Stocks", f"{summary['red_stocks']}", f"-{summary['red_pct']}%", delta_color="inverse")
    c3.metric("Average Price", f"₹{summary['average_price']:,.2f}")
    c4.metric("Average Volume", f"{summary['average_volume']:,.0f}")

    st.markdown("### Green vs Red Stocks")
    pie_df = pd.DataFrame(
        {"status": ["Green", "Red"], "count": [summary["green_stocks"], summary["red_stocks"]]}
    )
    fig = px.pie(
        pie_df, names="status", values="count",
        color="status", color_discrete_map={"Green": GREEN, "Red": RED}, hole=0.5,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### All Stocks — Yearly Return")
    yr = an.yearly_returns(prices).sort_values("yearly_return_pct", ascending=False)
    yr["color"] = yr["yearly_return_pct"].apply(lambda x: GREEN if x > 0 else RED)
    fig2 = px.bar(yr, x="symbol", y="yearly_return_pct", color="color",
                  color_discrete_map="identity", labels={"yearly_return_pct": "Yearly Return (%)"})
    fig2.update_layout(showlegend=False, xaxis_tickangle=-60)
    st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------------------------
# Top Gainers & Losers
# ---------------------------------------------------------------------------

elif page == "Top Gainers & Losers":
    st.title("Top 10 Gainers & Losers (Yearly)")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🟢 Top 10 Green Stocks")
        top_g = an.top_green_stocks(prices, 10)
        fig = px.bar(top_g, x="yearly_return_pct", y="symbol", orientation="h",
                     color_discrete_sequence=[GREEN], labels={"yearly_return_pct": "Return (%)"})
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top_g, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("🔴 Top 10 Loss Stocks")
        top_l = an.top_loss_stocks(prices, 10)
        fig = px.bar(top_l, x="yearly_return_pct", y="symbol", orientation="h",
                     color_discrete_sequence=[RED], labels={"yearly_return_pct": "Return (%)"})
        fig.update_layout(yaxis={"categoryorder": "total descending"})
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top_l, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Volatility Analysis
# ---------------------------------------------------------------------------

elif page == "Volatility Analysis":
    st.title("Volatility Analysis")
    st.caption("Volatility = standard deviation of daily returns. Higher = riskier / more price fluctuation.")
    top_vol = an.top_volatile_stocks(prices, 10)
    fig = px.bar(top_vol, x="symbol", y="volatility", color_discrete_sequence=[ACCENT],
                 labels={"volatility": "Volatility (Std Dev of Daily Returns)"})
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(top_vol, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Cumulative Returns
# ---------------------------------------------------------------------------

elif page == "Cumulative Returns":
    st.title("Cumulative Return — Top 5 Performing Stocks")
    cum5 = an.top5_cumulative_return_series(prices)
    fig = px.line(cum5, x="date", y="cumulative_return", color="symbol",
                  labels={"cumulative_return": "Cumulative Return", "date": "Date"})
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Sector Performance
# ---------------------------------------------------------------------------

elif page == "Sector Performance":
    st.title("Average Yearly Return by Sector")
    sec_perf = an.sector_performance(prices, sector_map)
    sec_perf["color"] = sec_perf["avg_yearly_return_pct"].apply(lambda x: GREEN if x > 0 else RED)
    fig = px.bar(sec_perf, x="sector", y="avg_yearly_return_pct", color="color",
                 color_discrete_map="identity", labels={"avg_yearly_return_pct": "Avg Yearly Return (%)"})
    fig.update_layout(showlegend=False, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(sec_perf.drop(columns="color"), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Price Correlation
# ---------------------------------------------------------------------------

elif page == "Price Correlation":
    st.title("Stock Price Correlation Heatmap")
    corr = an.price_correlation_matrix(prices)
    fig = go.Figure(data=go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.columns,
        colorscale="RdBu", zmid=0, zmin=-1, zmax=1,
    ))
    fig.update_layout(height=800)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Monthly Gainers & Losers
# ---------------------------------------------------------------------------

elif page == "Monthly Gainers & Losers":
    st.title("Top 5 Gainers & Losers by Month")
    monthly_data = an.monthly_top_gainers_losers(prices, 5)
    months = sorted(monthly_data.keys())
    selected_month = st.selectbox("Select month", months, index=len(months) - 1)

    g = monthly_data[selected_month]["gainers"]
    l = monthly_data[selected_month]["losers"]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"🟢 Top 5 Gainers — {selected_month}")
        fig = px.bar(g, x="monthly_return_pct", y="symbol", orientation="h",
                     color_discrete_sequence=[GREEN], labels={"monthly_return_pct": "Return (%)"})
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader(f"🔴 Top 5 Losers — {selected_month}")
        fig = px.bar(l, x="monthly_return_pct", y="symbol", orientation="h",
                     color_discrete_sequence=[RED], labels={"monthly_return_pct": "Return (%)"})
        fig.update_layout(yaxis={"categoryorder": "total descending"})
        st.plotly_chart(fig, use_container_width=True)
