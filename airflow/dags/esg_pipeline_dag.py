"""
ESG Pipeline DAG
----------------
Orchestrates: World Bank extraction -> load raw JSON into Postgres -> dbt run.

This is a skeleton to fill in once your extraction and loading scripts are
working standalone (run them manually first - don't debug through Airflow).
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "marcel",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="esg_pipeline",
    default_args=default_args,
    description="World Bank ESG indicators: extract -> load -> transform",
    schedule_interval="@weekly",  # ESG indicators update infrequently
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["esg", "data-engineering-portfolio"],
) as dag:

    extract = PythonOperator(
        task_id="extract_worldbank_esg",
        python_callable=lambda: __import__(
            "extraction.extract_worldbank_esg", fromlist=["main"]
        ).main(),
    )

    # TODO: implement load_raw_to_postgres.py - reads JSON landing files,
    # loads each indicator into its raw_esg.<indicator_name> table
    load = PythonOperator(
        task_id="load_raw_to_postgres",
        python_callable=lambda: print("TODO: implement loader"),
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /path/to/esg-pipeline/dbt_esg && dbt run",
    )

    extract >> load >> dbt_run
