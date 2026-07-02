-- ============================================================================
-- analysis_queries.sql
-- Reference SQL queries mirroring the Python analysis in scripts/analysis.py
-- Works against the stock_prices / sector_mapping tables created by
-- scripts/03_load_to_sql.py. Written for SQLite syntax; minor tweaks
-- (e.g. STDDEV vs custom variance calc) may be needed for MySQL/Postgres.
-- ============================================================================

-- 1. Market Summary: average price & volume across all stocks
SELECT
    ROUND(AVG(close), 2)  AS average_price,
    ROUND(AVG(volume), 2) AS average_volume
FROM stock_prices;

-- 2. Yearly return per symbol (first close vs last close in the dataset)
WITH bounds AS (
    SELECT symbol,
           MIN(date) AS first_date,
           MAX(date) AS last_date
    FROM stock_prices
    GROUP BY symbol
),
first_last AS (
    SELECT b.symbol,
           (SELECT close FROM stock_prices sp WHERE sp.symbol = b.symbol AND sp.date = b.first_date) AS first_close,
           (SELECT close FROM stock_prices sp WHERE sp.symbol = b.symbol AND sp.date = b.last_date)  AS last_close
    FROM bounds b
)
SELECT symbol,
       first_close,
       last_close,
       ROUND((last_close - first_close) / first_close * 100, 2) AS yearly_return_pct
FROM first_last
ORDER BY yearly_return_pct DESC;

-- 3. Top 10 Green Stocks (highest yearly return) — wrap query #2 as a view/CTE and:
--    ... ORDER BY yearly_return_pct DESC LIMIT 10;

-- 4. Top 10 Loss Stocks (lowest yearly return):
--    ... ORDER BY yearly_return_pct ASC LIMIT 10;

-- 5. Green vs Red stock counts
--    Use query #2 as `yearly_returns`, then:
-- SELECT
--     SUM(CASE WHEN yearly_return_pct > 0 THEN 1 ELSE 0 END) AS green_stocks,
--     SUM(CASE WHEN yearly_return_pct <= 0 THEN 1 ELSE 0 END) AS red_stocks
-- FROM yearly_returns;

-- 6. Sector-wise average yearly return
--    Join yearly_returns to sector_mapping on symbol, then GROUP BY sector, AVG(yearly_return_pct)

-- 7. Monthly return per symbol
SELECT
    symbol,
    strftime('%Y-%m', date) AS month,
    ROUND(
        (
            (SELECT close FROM stock_prices sp2
             WHERE sp2.symbol = sp1.symbol AND strftime('%Y-%m', sp2.date) = strftime('%Y-%m', sp1.date)
             ORDER BY sp2.date DESC LIMIT 1)
            -
            (SELECT close FROM stock_prices sp3
             WHERE sp3.symbol = sp1.symbol AND strftime('%Y-%m', sp3.date) = strftime('%Y-%m', sp1.date)
             ORDER BY sp3.date ASC LIMIT 1)
        )
        /
        (SELECT close FROM stock_prices sp3
         WHERE sp3.symbol = sp1.symbol AND strftime('%Y-%m', sp3.date) = strftime('%Y-%m', sp1.date)
         ORDER BY sp3.date ASC LIMIT 1) * 100
    , 2) AS monthly_return_pct
FROM stock_prices sp1
GROUP BY symbol, month
ORDER BY month, monthly_return_pct DESC;

-- NOTE: Volatility (std dev of daily returns), cumulative return, and the
-- price correlation matrix are computed in Python (scripts/analysis.py)
-- since they require row-over-row daily return calculations and pairwise
-- correlation across 50 columns, which are far more maintainable in
-- pandas than in raw SQL. This mirrors real-world practice: SQL for set-based
-- aggregation, pandas for time-series/statistical transforms.
