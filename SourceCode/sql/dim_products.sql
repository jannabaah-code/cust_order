-- ============================================================
-- DDL SCRIPT: dim_products
-- Type: Dimension Table
-- Description: Deduplicated product catalog with category.
--              Each row represents one distinct product.
-- Source: customer_orders.csv
-- Generated: 2026-09-14
-- ============================================================

CREATE TABLE dim_products (
    product_id       INT             NOT NULL,
    product_name     VARCHAR(100)    NOT NULL,
    product_category VARCHAR(50)     NOT NULL,

    CONSTRAINT pk_dim_products PRIMARY KEY (product_id)
);

-- Column descriptions:
-- product_id       : Unique numeric identifier for each product (PK)
-- product_name     : Name of the product as listed in orders
-- product_category : High-level product grouping.
--                    Accepted values: 'Electronics', 'Furniture', 'Office Supplies'
