def run_ingestion():
    # Example ingestion logic
    import pandas as pd
    from sqlalchemy import create_engine

    engine = create_engine("postgresql://dbt_user:dbt_password@postgres:5432/analytics")

    df = pd.read_csv("/opt/airflow/data/new_orders.csv")
    df.to_sql("raw_orders", engine, if_exists="append", index=False)

    print("Ingestion complete.")
