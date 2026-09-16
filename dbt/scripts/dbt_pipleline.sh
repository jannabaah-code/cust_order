#!/bin/bash

# -----------------------------------------
# DBT Pipeline Execution Script
# Usage:
#   ./dbt_pipeline.sh /path/to/customer_orders.csv
# -----------------------------------------

# Validate input
if [ -z "$1" ]; then
    echo "ERROR: You must provide a data file path."
    echo "Usage: ./dbt_pipeline.sh /path/to/customer_orders.csv"
    exit 1
fi

DATA_FILE="$1"

echo "-----------------------------------------"
echo " DBT Pipeline Execution Started"
echo " Data File: $DATA_FILE"
echo "-----------------------------------------"

# Step 1: Ingest data into raw_orders table
echo "Ingesting data into raw_orders..."
python3 <<EOF
import pandas as pd
from sqlalchemy import create_engine

df = pd.read_csv("$DATA_FILE")
engine = create_engine("postgresql://dbt_user:dbt_password@postgres:5432/analytics")

df.to_sql("raw_orders", engine, if_exists="replace", index=False)
print("Ingestion complete.")
EOF

# Step 2: Navigate to dbt project
cd cust_order/dbt || exit

# Step 3: Install dependencies
echo "Running dbt deps..."
dbt deps

# Step 4: Seed (if seeds exist)
echo "Running dbt seed..."
dbt seed

# Step 5: Run models
echo "Running dbt run..."
dbt run

# Step 6: Execute tests
echo "Running dbt test..."
dbt test

echo "-----------------------------------------"
echo " DBT Pipeline Execution Completed Successfully"
echo "-----------------------------------------"
