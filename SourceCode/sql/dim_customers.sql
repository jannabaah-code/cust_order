-- ============================================================
-- DDL SCRIPT: dim_customers
-- Type: Dimension Table
-- Description: Deduplicated customer reference data.
--              Each row represents one distinct customer.
-- Source: customer_orders.csv
-- Generated: 2026-09-14
-- ============================================================

CREATE TABLE dim_customers (
    customer_id     INT             NOT NULL,
    customer_name   VARCHAR(100)    NOT NULL,
    customer_email  VARCHAR(150)    NOT NULL,

    CONSTRAINT pk_dim_customers PRIMARY KEY (customer_id),
    CONSTRAINT uq_dim_customers_email UNIQUE (customer_email)
);

-- Column descriptions:
-- customer_id    : Unique numeric identifier for each customer (PK)
-- customer_name  : Full name of the customer
-- customer_email : Unique email address used to identify the customer
