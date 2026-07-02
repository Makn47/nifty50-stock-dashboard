"""
01_extract_yaml_to_csv.py

Extracts Nifty 50 daily OHLCV data from month-wise YAML files and
transforms it into per-symbol CSV files.

Input : data/<YYYY-MM>/<YYYY-MM-DD_HH-MM-SS>.yaml
Output: csv_data/<SYMBOL>.csv   (one file per stock symbol)

Each output CSV has columns: date, open, high, low, close, volume
sorted chronologically.

Usage:
    python 01_extract_yaml_to_csv.py --input ../data_raw/data --output ../csv_data
"""

import argparse
import glob
import os
from collections import defaultdict

import pandas as pd
import yaml


def load_all_records(input_dir: str) -> list[dict]:
    """Walk every month folder and every daily YAML file, return flat list of records."""
    records = []
    yaml_files = sorted(glob.glob(os.path.join(input_dir, "*", "*.yaml")))

    if not yaml_files:
        raise FileNotFoundError(
            f"No .yaml files found under {input_dir}. "
            "Expected structure: <input_dir>/<YYYY-MM>/<YYYY-MM-DD_...>.yaml"
        )

    for path in yaml_files:
        with open(path, "r", encoding="utf-8") as f:
            day_data = yaml.safe_load(f)
        if not day_data:
            continue
        records.extend(day_data)

    return records


def records_to_symbol_frames(records: list[dict]) -> dict[str, pd.DataFrame]:
    """Group flat records by Ticker symbol into a dict of DataFrames."""
    by_symbol = defaultdict(list)
    for r in records:
        by_symbol[r["Ticker"]].append(
            {
                "date": pd.to_datetime(r["date"]).date(),
                "open": r["open"],
                "high": r["high"],
                "low": r["low"],
                "close": r["close"],
                "volume": r["volume"],
            }
        )

    frames = {}
    for symbol, rows in by_symbol.items():
        df = pd.DataFrame(rows)
        df = df.drop_duplicates(subset="date").sort_values("date").reset_index(drop=True)
        frames[symbol] = df

    return frames


def main():
    parser = argparse.ArgumentParser(description="Extract YAML stock data into per-symbol CSVs")
    parser.add_argument("--input", default="../data_raw/data", help="Path to month-wise YAML root folder")
    parser.add_argument("--output", default="../csv_data", help="Path to write per-symbol CSV files")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    print(f"Reading YAML files from: {args.input}")
    records = load_all_records(args.input)
    print(f"Loaded {len(records)} total daily records")

    frames = records_to_symbol_frames(records)
    print(f"Found {len(frames)} unique symbols")

    for symbol, df in sorted(frames.items()):
        out_path = os.path.join(args.output, f"{symbol}.csv")
        df.to_csv(out_path, index=False)

    print(f"Wrote {len(frames)} CSV files to {args.output}")

    # quick sanity summary
    counts = {s: len(df) for s, df in frames.items()}
    print(f"Rows per symbol - min: {min(counts.values())}, max: {max(counts.values())}")


if __name__ == "__main__":
    main()
