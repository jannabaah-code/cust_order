from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

with DAG(
    dag_id="dbt_snapshots",
    schedule_interval="0 2 * * *",
    start_date=days_ago(1),
    catchup=False
) as dag:

    dbt_snapshot = BashOperator(
        task_id="dbt_snapshot",
        bash_command="cd /usr/local/airflow/dbt && dbt snapshot"
    )
