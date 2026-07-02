"""
03_load_to_sql.py

Loads the per-symbol CSVs and the sector mapping into a SQL database.

Defaults to SQLite (zero setup, single portable file: sql/stock_data.db).
To use PostgreSQL or MySQL instead, just change DB_URL below (or pass
--db-url) to a SQLAlchemy connection string, e.g.:
    postgresql://user:password@localhost:5432/stockdb
    mysql+pymysql://user:password@localhost:3306/stockdb

Creates two tables:
    stock_prices(symbol, date, open, high, low, close, volume)
    sector_mapping(symbol, company, sector)

Usage:
    python 03_load_to_sql.py --csv-data ../csv_data --sector-csv ../sql/sector_mapping_clean.csv --db-url sqlite:///../sql/stock_data.db
"""

import argparse
import glob
import os

import pandas as pd
from sqlalchemy import create_engine, text


def main():
    parser = argparse.ArgumentParser(description="Load stock CSVs + sector mapping into SQL database")
    parser.add_argument("--csv-data", default="../csv_data")
    parser.add_argument("--sector-csv", default="../sql/sector_mapping_clean.csv")
    parser.add_argument("--db-url", default="sqlite:///../sql/stock_data.db")
    args = parser.parse_args()

    engine = create_engine(args.db_url)

    # --- Load stock prices ---
    csv_files = sorted(glob.glob(os.path.join(args.csv_data, "*.csv")))
    if not csv_files:
        raise FileNotFoundError(f"No CSVs found in {args.csv_data}")

    frames = []
    for path in csv_files:
        symbol = os.path.basename(path).replace(".csv", "")
        df = pd.read_csv(path)
        df["symbol"] = symbol
        frames.append(df)

    all_prices = pd.concat(frames, ignore_index=True)
    all_prices = all_prices[["symbol", "date", "open", "high", "low", "close", "volume"]]
    all_prices.to_sql("stock_prices", engine, if_exists="replace", index=False)
    print(f"Loaded {len(all_prices)} rows into stock_prices ({len(csv_files)} symbols)")

    # --- Load sector mapping ---
    sector_df = pd.read_csv(args.sector_csv)
    sector_df = sector_df[["symbol", "company", "sector"]]
    sector_df.to_sql("sector_mapping", engine, if_exists="replace", index=False)
    print(f"Loaded {len(sector_df)} rows into sector_mapping")

    # --- Helpful indexes for query performance ---
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prices_symbol ON stock_prices(symbol)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prices_date ON stock_prices(date)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sector_symbol ON sector_mapping(symbol)"))
            conn.commit()
        except Exception as e:
            print(f"Index creation skipped/failed (non-fatal): {e}")

    print(f"Database ready at: {args.db_url}")


if __name__ == "__main__":
    main()
