flowchart TD

    subgraph Airflow
        A[dbt_orchestration DAG] --> B[dbt run]
        B --> C[dbt test]
        A --> D[dbt snapshot DAG]
        D --> E[dbt snapshot]
    end

    subgraph Sources
        S1[raw_customers]
        S2[raw_products]
        S3[raw_orders]
    end

    subgraph Staging
        ST1[stg_customers]
        ST2[stg_products]
        ST3[stg_orders]
    end

    subgraph Marts
        M1[dim_customers]
        M2[dim_products]
        M3[fct_orders]
    end

    subgraph Snapshots
        SS1[customers_snapshot]
        SS2[products_snapshot]
        SS3[orders_snapshot]
    end

    subgraph Reporting
        R1[order_summary]
    end

    %% Source → Staging
    S1 --> ST1
    S2 --> ST2
    S3 --> ST3

    %% Staging → Marts
    ST1 --> M1
    ST2 --> M2
    ST3 --> M3

    %% Marts → Reporting
    M1 --> R1
    M3 --> R1

    %% Snapshots
    ST1 --> SS1
    ST2 --> SS2
    ST3 --> SS3

    %% Airflow triggers dbt
    A --> B
    A --> D
