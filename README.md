# Data-Driven Stock Analysis: Nifty 50 Performance Dashboard

Organizing, cleaning, and visualizing a year of Nifty 50 daily stock data — from raw YAML files to an interactive Streamlit dashboard and Power BI-ready exports.

**Domain:** Finance / Data Analytics
**Skills:** Pandas, Python, SQL, Streamlit, Power BI, Statistics, Data Cleaning

---

## Problem Statement

The Stock Performance Dashboard provides a comprehensive visualization and analysis of Nifty 50 stocks' performance over a year of daily trading data (open, close, high, low, volume). It identifies top/bottom performers, computes volatility and correlation, breaks down performance by sector, and surfaces monthly gainers/losers — via both a Streamlit app and Power BI-ready data exports.

## Project Structure

```
.
├── data_raw/data/<YYYY-MM>/<YYYY-MM-DD_...>.yaml   # raw source data (284 daily files, Oct 2023–Nov 2024)
├── csv_data/<SYMBOL>.csv                            # 50 per-symbol CSVs (extraction output)
├── scripts/
│   ├── 01_extract_yaml_to_csv.py    # YAML -> per-symbol CSV
│   ├── 02_clean_sector_mapping.py   # cleans raw sector CSV, fixes ticker mismatches
│   ├── 03_load_to_sql.py            # loads CSVs into SQL (SQLite by default)
│   ├── 04_export_for_powerbi.py     # exports flat analysis tables for Power BI
│   └── analysis.py                  # core analysis functions (shared by Streamlit + exports)
├── sql/
│   ├── stock_data.db                # generated SQLite database
│   ├── sector_mapping_clean.csv     # cleaned sector lookup
│   └── analysis_queries.sql         # reference SQL for key metrics
├── outputs/
│   └── powerbi/                     # flat CSVs ready to import into Power BI
├── streamlit_app/
│   └── app.py                       # interactive dashboard
├── requirements.txt
└── README.md
```

## Data Source

Raw data is provided as YAML files organized by month (`data/<YYYY-MM>/`), one file per trading day, each containing OHLCV records for all 50 Nifty symbols. Sector classifications come from a separate `Sector_data.csv` mapping company → sector → ticker.

**Note on sector data cleaning:** the source sector CSV had a malformed `Symbol` column (`"COMPANY NAME: TICKER"`) and a few tickers that didn't match the real NSE symbols used in the price data (e.g. `ADANIGREEN` → should be `ADANIENT`, `AIRTEL` → `BHARTIARTL`, `TATACONSUMER` → `TATACONSUM`). `scripts/02_clean_sector_mapping.py` fixes these and adds one missing mapping (`BRITANNIA` → FMCG) so all 50 symbols have a sector.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Workflow / Execution

Run each step from the `scripts/` directory, in order:

```bash
cd scripts

# 1. Extract YAML -> 50 per-symbol CSVs
python 01_extract_yaml_to_csv.py --input ../data_raw/data --output ../csv_data

# 2. Clean the sector mapping CSV
python 02_clean_sector_mapping.py --input ../data_raw/Sector_data.csv --csv-data ../csv_data --output ../sql/sector_mapping_clean.csv

# 3. Load everything into SQL (SQLite by default, no server needed)
python 03_load_to_sql.py --csv-data ../csv_data --sector-csv ../sql/sector_mapping_clean.csv --db-url sqlite:///../sql/stock_data.db

# 4. (Optional) Export flat CSVs for Power BI
python 04_export_for_powerbi.py --db-url sqlite:///../sql/stock_data.db --output ../outputs/powerbi
```

Then launch the dashboard:

```bash
cd ../streamlit_app
streamlit run app.py
```

### Switching to PostgreSQL / MySQL

The pipeline uses SQLAlchemy, so switching databases only requires changing the `--db-url` (and matching driver in `requirements.txt`):

```bash
# PostgreSQL
python 03_load_to_sql.py --db-url postgresql://user:password@localhost:5432/stockdb

# MySQL
python 03_load_to_sql.py --db-url mysql+pymysql://user:password@localhost:3306/stockdb
```

Update `streamlit_app/app.py`'s `DB_URL` the same way.

## Analysis Covered

| # | Analysis | Method |
|---|----------|--------|
| 1 | Top 10 Green / Loss stocks | Sort by yearly return |
| 2 | Market summary | Green/red counts, avg price, avg volume |
| 3 | Volatility | Std dev of daily returns, top 10 chart |
| 4 | Cumulative return | Running product of (1 + daily return) for top 5 performers |
| 5 | Sector performance | Avg yearly return grouped by sector |
| 6 | Price correlation | `pandas.DataFrame.corr()` on closing prices, heatmap |
| 7 | Monthly gainers/losers | Top 5 per month, 14 months covered |

## Power BI Dashboard

Import the CSVs in `outputs/powerbi/` via **Get Data → Text/CSV**, then relate `fact_stock_prices` and `sector_mapping` on the `symbol` column to build the same visuals (bar charts, heatmap via matrix visual, line chart for cumulative returns) natively in Power BI. Alternatively, connect Power BI directly to `sql/stock_data.db` with a SQLite ODBC connector and use `sql/analysis_queries.sql` as a starting point for DAX/M queries.

## Tech Stack

- **Languages:** Python 3
- **Database:** SQLite (portable default; SQLAlchemy makes Postgres/MySQL a one-line swap)
- **Libraries:** Pandas, PyYAML, SQLAlchemy, Plotly
- **Visualization:** Streamlit (interactive web app), Power BI (exported flat tables)

## Coding Standards

- PEP 8 compliant, modular scripts (one responsibility per script)
- Shared analysis logic lives once in `scripts/analysis.py`, imported by both the Streamlit app and the Power BI export script — no duplicated logic
- All scripts are CLI-driven with `argparse` for reproducibility
