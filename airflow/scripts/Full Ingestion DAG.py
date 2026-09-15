from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.models import Variable

import sys
import os

# Path to ingestion scripts
INGESTION_PATH = "/opt/airflow/scripts"

sys.path.append(INGESTION_PATH)

# Import your ingestion script
from populate_tables import run_ingestion


default_args = {
    "owner": "janna",
    "retries": 2,
    "retry_delay": 300,  # 5 minutes
}

with DAG(
    dag_id="data_ingestion",
    default_args=default_args,
    schedule_interval="0 * * * *",  # hourly ingestion
    start_date=days_ago(1),
    catchup=False,
    tags=["ingestion", "pipeline"],
) as dag:

    # Step 1 — Run Python ingestion script
    ingest_raw_data = PythonOperator(
        task_id="ingest_raw_data",
        python_callable=run_ingestion,
    )

    # Step 2 — Run dbt seeds (optional)
    dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command="cd /usr/local/airflow/dbt && dbt seed --target prod",
    )

    # Step 3 — Trigger dbt run (optional)
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /usr/local/airflow/dbt && dbt run --target prod",
    )

    # Step 4 — Run dbt tests
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /usr/local/airflow/dbt && dbt test --target prod",
    )

    ingest_raw_data >> dbt_seed >> dbt_run >> dbt_test
