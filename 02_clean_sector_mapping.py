"""
02_clean_sector_mapping.py

Cleans the raw Sector_data CSV (which has a malformed 'Symbol' column in the
form "COMPANY NAME: TICKER") into a simple sector -> symbol lookup table
that matches the tickers found in the extracted stock CSVs.

A few tickers in the source sector file didn't match the actual NSE symbols
used in the price data and are corrected here:
  - ADANIGREEN   -> ADANIENT     (row was for Adani Enterprises)
  - AIRTEL       -> BHARTIARTL   (NSE symbol for Bharti Airtel)
  - TATACONSUMER -> TATACONSUM   (NSE symbol truncation)
  - IOC row has no corresponding price data; BRITANNIA appears in the price
    data with no sector row, so it is added manually (sector: FMCG).

Usage:
    python 02_clean_sector_mapping.py --input <sector_csv> --csv-data ../csv_data --output ../sql/sector_mapping_clean.csv
"""

import argparse
import os

import pandas as pd

SYMBOL_FIXES = {
    "ADANIGREEN": "ADANIENT",
    "AIRTEL": "BHARTIARTL",
    "TATACONSUMER": "TATACONSUM",
}


def main():
    parser = argparse.ArgumentParser(description="Clean sector mapping CSV")
    parser.add_argument("--input", required=True, help="Path to raw Sector_data CSV")
    parser.add_argument("--csv-data", default="../csv_data", help="Path to per-symbol CSVs (for validation)")
    parser.add_argument("--output", default="../sql/sector_mapping_clean.csv", help="Output path")
    args = parser.parse_args()

    sec = pd.read_csv(args.input)
    sec.columns = [c.strip().lower() for c in sec.columns]
    sec["symbol"] = sec["symbol"].str.split(":").str[-1].str.strip()
    sec["sector"] = sec["sector"].str.strip().str.title()
    sec["company"] = sec["company"].str.strip().str.title()
    sec["symbol"] = sec["symbol"].replace(SYMBOL_FIXES)

    # add the one manually-known missing mapping
    if "BRITANNIA" not in sec["symbol"].values:
        sec = pd.concat(
            [sec, pd.DataFrame([{"company": "Britannia Industries", "sector": "Fmcg", "symbol": "BRITANNIA"}])],
            ignore_index=True,
        )

    # drop rows with no matching price data (e.g. IOC)
    available_tickers = {f.replace(".csv", "") for f in os.listdir(args.csv_data)}
    before = len(sec)
    sec = sec[sec["symbol"].isin(available_tickers)].reset_index(drop=True)
    dropped = before - len(sec)
    if dropped:
        print(f"Dropped {dropped} sector row(s) with no matching price data")

    missing = available_tickers - set(sec["symbol"])
    if missing:
        print(f"WARNING: {len(missing)} symbols still have no sector mapping: {sorted(missing)}")

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    sec.to_csv(args.output, index=False)
    print(f"Wrote cleaned sector mapping ({len(sec)} rows) to {args.output}")


if __name__ == "__main__":
    main()
