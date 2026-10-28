"""
Load raw World Bank ESG JSON landing files into Postgres.
-----------------------------------------------------------
Reads each indicator's JSON file from data/raw/<run_date>/ and loads it
into a table under the raw_esg schema - one table per indicator,
matching dbt_esg/models/staging/sources.yml.

Run this AFTER extract_worldbank_esg.py, and AFTER you've created the
database + schema manually:

    CREATE DATABASE esg_pipeline;
    \\c esg_pipeline
    CREATE SCHEMA IF NOT EXISTS raw_esg;

Usage:
    python load_raw_to_postgres.py                  # loads today's run
    python load_raw_to_postgres.py 2026-10-02        # loads a specific date
"""

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

# --- Config --------------------------------------------------------------

# Adjust these to match your local Postgres setup.
DB_USER = "postgres"
import os
DB_PASSWORD = os.getenv("DBT_POSTGRES_PASSWORD")
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "esg_pipeline"

RAW_DIR = RAW_DIR = Path(__file__).parent.parent / "data" / "raw"


def get_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def flatten_records(records: list[dict]) -> pd.DataFrame:
    """
    World Bank API records look like:
    {
      "indicator": {"id": "EG.FEC.RNEW.ZS", "value": "Renewable energy..."},
      "country": {"id": "NG", "value": "Nigeria"},
      "countryiso3code": "NGA",
      "date": "2021",
      "value": 84.5,
      "unit": "", "obs_status": "", "decimal": 1
    }
    Flatten to: country_iso3, country_name, year, value, indicator_code
    """
    rows = []
    for r in records:
        rows.append({
            "country_iso3": r.get("countryiso3code"),
            "country_name": (r.get("country") or {}).get("value"),
            "year": int(r["date"]) if r.get("date") else None,
            "value": r.get("value"),
            "indicator_code": (r.get("indicator") or {}).get("id"),
        })
    return pd.DataFrame(rows)


def load_indicator_file(path: Path, engine) -> int:
    with path.open() as f:
        payload = json.load(f)

    name = payload["indicator_name"]
    records = payload["records"]

    df = flatten_records(records)
    # Drop rows with no country code (these are regional/aggregate rollups
    # like "World" or "Sub-Saharan Africa" - keep countries only for now)
    df = df.dropna(subset=["country_iso3"])

    df.to_sql(
        name,
        engine,
        schema="raw_esg",
        if_exists="replace",  # full refresh each run - simplest for a portfolio project
        index=False,
    )
    return len(df)


def main():
    run_date = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    run_dir = RAW_DIR / run_date

    if not run_dir.exists():
        print(f"No raw data found for {run_date} at {run_dir}")
        sys.exit(1)

    engine = get_engine()
    json_files = sorted(run_dir.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in {run_dir}")
        sys.exit(1)

    print(f"Loading {len(json_files)} indicator file(s) from {run_dir} into Postgres...")

    for path in json_files:
        try:
            row_count = load_indicator_file(path, engine)
            print(f"  -> raw_esg.{path.stem}: {row_count} rows loaded")
        except Exception as e:
            print(f"  !! Failed to load {path.name}: {e}")

    print("Load complete.")


if __name__ == "__main__":
    main()
