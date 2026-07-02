"""
04_export_for_powerbi.py

Exports flat, Power-BI-friendly CSVs (one table per analysis view) so the
Power BI dashboard can just import these directly (Get Data > Text/CSV),
or you can connect Power BI straight to sql/stock_data.db via an ODBC/
SQLite connector and build these same views with DAX instead.

Usage:
    python 04_export_for_powerbi.py --db-url sqlite:///../sql/stock_data.db --output ../outputs/powerbi
"""

import argparse
import os

import analysis as an


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url", default="sqlite:///../sql/stock_data.db")
    parser.add_argument("--output", default="../outputs/powerbi")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    engine = an.get_engine(args.db_url)
    prices = an.load_prices(engine)
    sector_map = an.load_sector_map(engine)

    exports = {
        "fact_stock_prices.csv": prices,
        "yearly_returns.csv": an.yearly_returns(prices),
        "top10_green_stocks.csv": an.top_green_stocks(prices, 10),
        "top10_loss_stocks.csv": an.top_loss_stocks(prices, 10),
        "volatility_by_symbol.csv": an.volatility_by_symbol(prices),
        "cumulative_returns_all.csv": an.cumulative_returns(prices),
        "sector_performance.csv": an.sector_performance(prices, sector_map),
        "sector_mapping.csv": sector_map,
        "price_correlation_matrix.csv": an.price_correlation_matrix(prices),
        "monthly_returns.csv": an.monthly_returns(prices),
    }

    for filename, df in exports.items():
        path = os.path.join(args.output, filename)
        df.to_csv(path, index=(filename == "price_correlation_matrix.csv"))
        print(f"Wrote {path}  ({len(df)} rows)")

    print("\nDone. In Power BI: Get Data > Text/CSV > import each file, "
          "then relate fact_stock_prices / sector_mapping on 'symbol'.")


if __name__ == "__main__":
    main()
