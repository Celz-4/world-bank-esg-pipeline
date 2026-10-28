"""
World Bank ESG Indicator Extraction
------------------------------------
Pulls a curated set of Environmental, Social, and Governance indicators
from the World Bank API (v2) for all countries and lands them as raw
JSON files, one per indicator, partitioned by extraction date.

API docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
No API key required.
"""

import json
import time
from datetime import date
from pathlib import Path

import requests

# --- Config -----------------------------------------------------------

BASE_URL = "http://api.worldbank.org/v2/country/all/indicator/{code}"

# Curated ESG indicator set: (code, human-readable name, pillar, source_db)
# source_db is the World Bank API "source" parameter:
#   2 = World Development Indicators (WDI) - the default, used when source_db is None
#   3 = Worldwide Governance Indicators (WGI) - governance estimates live here, NOT in WDI
INDICATORS = [
    # Environmental
    # NOTE: EN.ATM.CO2E.PC was retired/archived by World Bank; replaced with the
    # AR5-methodology equivalent below.
    ("EN.GHG.CO2.PC.CE.AR5", "co2_emissions_per_capita", "environmental", None),
    ("EG.FEC.RNEW.ZS", "renewable_energy_pct", "environmental", None),
    ("EN.ATM.PM25.MC.M3", "pm25_air_pollution", "environmental", None),
    # Social
    ("SI.POV.GINI", "gini_index", "social", None),
    ("SL.UEM.TOTL.ZS", "unemployment_rate", "social", None),
    ("SP.DYN.LE00.IN", "life_expectancy", "social", None),
    # Governance (World Bank Governance Indicators - WGI, source=3)
    ("CC.EST", "control_of_corruption", "governance", 3),
    ("RQ.EST", "regulatory_quality", "governance", 3),
    ("RL.EST", "rule_of_law", "governance", 3),
]

DATE_RANGE = "2000:2023"
PER_PAGE = 1000  # smaller page size - some World Bank sources (e.g. WGI, source=3)
                  # reject very large per_page values; pagination handles the rest
RAW_DIR = Path(__file__).parent.parent / "data" / "raw"


# --- Extraction ---------------------------------------------------------

def fetch_indicator(code: str, source_db: int | None = None) -> list[dict]:
    """Fetch a single indicator for all countries/years, following pagination.

    source_db selects which World Bank database to query (e.g. 3 for WGI).
    Omit (None) to use the API's default (WDI).
    """
    all_records = []
    page = 1

    while True:
        params = {
            "format": "json",
            "per_page": PER_PAGE,
            "page": page,
        }
        # The WGI source (3) has rejected the "date=2000:2023" range syntax
        # that works fine against WDI (source 2) - omit it there and pull
        # full available history instead (WGI only goes back to ~1996 anyway).
        if source_db is None:
            params["date"] = DATE_RANGE
        else:
            params["source"] = source_db
        url = BASE_URL.format(code=code)
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()

        # World Bank API returns [metadata, data] - errors come back as a dict instead
        if isinstance(payload, dict) or len(payload) < 2 or payload[1] is None:
            raise ValueError(f"Unexpected response for {code}: {payload}")

        meta, records = payload
        all_records.extend(records)

        if page >= meta.get("pages", 1):
            break
        page += 1
        time.sleep(0.2)  # be polite to the API

    return all_records


def land_raw(code: str, name: str, pillar: str, records: list[dict], run_date: str) -> Path:
    """Write raw records to a JSON landing file."""
    out_dir = RAW_DIR / run_date
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{name}.json"

    with out_path.open("w") as f:
        json.dump(
            {
                "indicator_code": code,
                "indicator_name": name,
                "pillar": pillar,
                "extracted_at": run_date,
                "record_count": len(records),
                "records": records,
            },
            f,
            indent=2,
        )
    return out_path


def main():
    run_date = date.today().isoformat()
    print(f"Starting World Bank ESG extraction for {run_date}")

    for code, name, pillar, source_db in INDICATORS:
        print(f"  Fetching {code} ({name})...")
        try:
            records = fetch_indicator(code, source_db)
            path = land_raw(code, name, pillar, records, run_date)
            print(f"    -> {len(records)} records landed at {path}")
        except Exception as e:
            print(f"    !! Failed to fetch {code}: {e}")

    print("Extraction complete.")


if __name__ == "__main__":
    main()
