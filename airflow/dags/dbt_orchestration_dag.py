from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

default_args = {
    "owner": "janna",
    "retries": 1,
}

with DAG(
    dag_id="dbt_orchestration",
    default_args=default_args,
    schedule_interval="0 */6 * * *",  # every 6 hours
    start_date=days_ago(1),
    catchup=False,
) as dag:

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="""
        cd /usr/local/airflow/dbt && \
        dbt run --profiles-dir /usr/local/airflow/.dbt
        """
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="""
        cd /usr/local/airflow/dbt && \
        dbt test --profiles-dir /usr/local/airflow/.dbt
        """
    )

    dbt_run >> dbt_test
