"""
analysis.py

Core analysis functions for the Stock Performance Dashboard.
Reads from the SQL database (stock_prices, sector_mapping) and returns
pandas DataFrames ready for visualization in Streamlit / Power BI / notebooks.

All functions take a SQLAlchemy engine so they work identically regardless
of whether the backend is SQLite, PostgreSQL, or MySQL.
"""

import pandas as pd
from sqlalchemy import create_engine


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def get_engine(db_url="sqlite:///../sql/stock_data.db"):
    return create_engine(db_url)


def load_prices(engine) -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM stock_prices", engine, parse_dates=["date"])
    return df.sort_values(["symbol", "date"]).reset_index(drop=True)


def load_sector_map(engine) -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM sector_mapping", engine)


# ---------------------------------------------------------------------------
# Daily returns (building block for volatility & cumulative return)
# ---------------------------------------------------------------------------

def add_daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    df = prices.copy()
    df["daily_return"] = df.groupby("symbol")["close"].pct_change()
    return df


# ---------------------------------------------------------------------------
# Yearly return & Top Gainers / Losers
# ---------------------------------------------------------------------------

def yearly_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Yearly return per symbol = (last close - first close) / first close."""
    first_last = (
        prices.groupby("symbol")
        .agg(first_close=("close", "first"), last_close=("close", "last"))
        .reset_index()
    )
    first_last["yearly_return_pct"] = (
        (first_last["last_close"] - first_last["first_close"]) / first_last["first_close"] * 100
    )
    return first_last


def top_green_stocks(prices: pd.DataFrame, n=10) -> pd.DataFrame:
    yr = yearly_returns(prices)
    return yr.sort_values("yearly_return_pct", ascending=False).head(n).reset_index(drop=True)


def top_loss_stocks(prices: pd.DataFrame, n=10) -> pd.DataFrame:
    yr = yearly_returns(prices)
    return yr.sort_values("yearly_return_pct", ascending=True).head(n).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Market Summary
# ---------------------------------------------------------------------------

def market_summary(prices: pd.DataFrame) -> dict:
    yr = yearly_returns(prices)
    green = (yr["yearly_return_pct"] > 0).sum()
    red = (yr["yearly_return_pct"] <= 0).sum()
    return {
        "green_stocks": int(green),
        "red_stocks": int(red),
        "green_pct": round(green / len(yr) * 100, 2),
        "red_pct": round(red / len(yr) * 100, 2),
        "average_price": round(prices["close"].mean(), 2),
        "average_volume": round(prices["volume"].mean(), 2),
        "total_symbols": len(yr),
    }


# ---------------------------------------------------------------------------
# Volatility Analysis
# ---------------------------------------------------------------------------

def volatility_by_symbol(prices: pd.DataFrame) -> pd.DataFrame:
    df = add_daily_returns(prices)
    vol = (
        df.groupby("symbol")["daily_return"]
        .std()
        .reset_index()
        .rename(columns={"daily_return": "volatility"})
    )
    return vol.sort_values("volatility", ascending=False).reset_index(drop=True)


def top_volatile_stocks(prices: pd.DataFrame, n=10) -> pd.DataFrame:
    return volatility_by_symbol(prices).head(n)


# ---------------------------------------------------------------------------
# Cumulative Return Over Time
# ---------------------------------------------------------------------------

def cumulative_returns(prices: pd.DataFrame) -> pd.DataFrame:
    df = add_daily_returns(prices)
    df["daily_return"] = df["daily_return"].fillna(0)
    df["cumulative_return"] = df.groupby("symbol")["daily_return"].transform(
        lambda x: (1 + x).cumprod() - 1
    )
    return df[["symbol", "date", "cumulative_return"]]


def top5_cumulative_return_series(prices: pd.DataFrame) -> pd.DataFrame:
    """Cumulative return time series for the top 5 performing stocks (by final cumulative return)."""
    cum = cumulative_returns(prices)
    final = cum.groupby("symbol")["cumulative_return"].last().sort_values(ascending=False)
    top5_symbols = final.head(5).index.tolist()
    return cum[cum["symbol"].isin(top5_symbols)]


# ---------------------------------------------------------------------------
# Sector-wise Performance
# ---------------------------------------------------------------------------

def sector_performance(prices: pd.DataFrame, sector_map: pd.DataFrame) -> pd.DataFrame:
    yr = yearly_returns(prices)
    merged = yr.merge(sector_map, on="symbol", how="left")
    sector_avg = (
        merged.groupby("sector")["yearly_return_pct"]
        .mean()
        .reset_index()
        .rename(columns={"yearly_return_pct": "avg_yearly_return_pct"})
        .sort_values("avg_yearly_return_pct", ascending=False)
        .reset_index(drop=True)
    )
    return sector_avg


# ---------------------------------------------------------------------------
# Stock Price Correlation
# ---------------------------------------------------------------------------

def price_correlation_matrix(prices: pd.DataFrame) -> pd.DataFrame:
    pivot = prices.pivot(index="date", columns="symbol", values="close")
    return pivot.corr()


# ---------------------------------------------------------------------------
# Top 5 Gainers / Losers by Month
# ---------------------------------------------------------------------------

def monthly_returns(prices: pd.DataFrame) -> pd.DataFrame:
    df = prices.copy()
    df["month"] = df["date"].dt.to_period("M").astype(str)
    monthly = (
        df.groupby(["symbol", "month"])
        .agg(first_close=("close", "first"), last_close=("close", "last"))
        .reset_index()
    )
    monthly["monthly_return_pct"] = (
        (monthly["last_close"] - monthly["first_close"]) / monthly["first_close"] * 100
    )
    return monthly


def monthly_top_gainers_losers(prices: pd.DataFrame, n=5) -> dict:
    """Returns {month: {'gainers': df, 'losers': df}} for every month present in data."""
    monthly = monthly_returns(prices)
    result = {}
    for month, group in monthly.groupby("month"):
        gainers = group.sort_values("monthly_return_pct", ascending=False).head(n)
        losers = group.sort_values("monthly_return_pct", ascending=True).head(n)
        result[month] = {"gainers": gainers, "losers": losers}
    return result


if __name__ == "__main__":
    # quick smoke test
    engine = get_engine()
    prices = load_prices(engine)
    sector_map = load_sector_map(engine)

    print("Market summary:", market_summary(prices))
    print("\nTop 5 green stocks:\n", top_green_stocks(prices, 5))
    print("\nTop 5 loss stocks:\n", top_loss_stocks(prices, 5))
    print("\nTop 5 volatile stocks:\n", top_volatile_stocks(prices, 5))
    print("\nSector performance:\n", sector_performance(prices, sector_map))
