# ESG Country Trends Pipeline

A data engineering portfolio project: World Bank ESG indicators, tracked
across countries and years, surfaced in a Power BI dashboard.

**Story:** how do Environmental, Social, and Governance metrics move
together (or diverge) for a country over time?

## Architecture

```
World Bank API --> Python extraction --> raw JSON landing
                                              |
                                              v
                                   Postgres (raw_esg schema)
                                              |
                                              v
                                    dbt (staging -> marts)
                                              |
                                              v
                                         Power BI
```

Orchestrated end-to-end by Airflow (weekly schedule - ESG indicators
don't update daily).

## Indicators

| Pillar | Indicator | World Bank Code |
|---|---|---|
| Environmental | CO2 emissions per capita | `EN.ATM.CO2E.PC` |
| Environmental | Renewable energy consumption % | `EG.FEC.RNEW.ZS` |
| Environmental | PM2.5 air pollution | `EN.ATM.PM25.MC.M3` |
| Social | Gini index (inequality) | `SI.POV.GINI` |
| Social | Unemployment rate | `SL.UEM.TOTL.ZS` |
| Social | Life expectancy | `SP.DYN.LE00.IN` |
| Governance | Control of corruption | `CC.EST` |
| Governance | Regulatory quality | `RQ.EST` |
| Governance | Rule of law | `RL.EST` |

## Build order (recommended)

1. **Extraction** - run `extraction/extract_worldbank_esg.py` standalone,
   confirm raw JSON lands correctly in `data/raw/<date>/`. Start here.
2. **Loader** - write a small script (`extraction/load_raw_to_postgres.py`,
   not yet created) that reads each JSON file and loads it into a
   `raw_esg.<indicator_name>` table in Postgres. `pandas.json_normalize()`
   + `to_sql()` is the fastest path.
3. **dbt staging** - one model per indicator (see `stg_co2_emissions.sql`
   as the template). Flattens and cleans each raw table.
4. **dbt marts** - `mart_country_esg_trends.sql` joins all 9 staging
   models into one wide country-year table. Currently only wired up for
   CO2 - extend the joins as you add staging models.
5. **Power BI** - connect directly to the `mart_country_esg_trends` table
   in Postgres. Build line charts of indicator trends per country, plus
   a country comparison view.
6. **Airflow** - once steps 1-4 work manually, wire them into
   `airflow/dags/esg_pipeline_dag.py`.

## Setup

```bash
cd extraction
pip install -r requirements.txt
python extract_worldbank_esg.py
```

Requires a Postgres instance for the load/dbt steps (local install or
Docker). dbt config (`profiles.yml`, `dbt_project.yml`) not yet created -
add once the loader is working.

## Notes

- No API key needed for World Bank data.
- Some country-year combinations will be null in the source data - the
  staging models filter these out; decide whether you want to keep them
  as explicit "missing" markers instead once you get to the marts layer.
- This is designed to swap Postgres for Snowflake later without touching
  the extraction or dbt logic - only the warehouse connection changes.
