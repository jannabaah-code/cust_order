-- ============================================================
-- DDL SCRIPT: fct_orders
-- Type: Fact Table
-- Grain: One row per order transaction
-- Measures: order_amount
-- Description: Central fact table storing order transactions.
--              References dim_customers and dim_products via FKs.
-- Source: customer_orders.csv
-- Generated: 2026-09-14
-- ============================================================

CREATE TABLE fct_orders (
    order_id        INT             NOT NULL,
    customer_id     INT             NOT NULL,
    product_id      INT             NOT NULL,
    order_amount    DECIMAL(10, 2)  NOT NULL,
    order_currency  CHAR(3)         NOT NULL DEFAULT 'USD',
    order_date      DATE            NOT NULL,
    order_status    VARCHAR(20)     NOT NULL,

    CONSTRAINT pk_fct_orders
        PRIMARY KEY (order_id),

    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id)
        REFERENCES dim_customers(customer_id),

    CONSTRAINT fk_orders_product
        FOREIGN KEY (product_id)
        REFERENCES dim_products(product_id),

    CONSTRAINT chk_order_status
        CHECK (order_status IN ('delivered', 'shipped', 'processing', 'cancelled'))
);

-- Column descriptions:
-- order_id       : Unique numeric identifier for each order transaction (PK)
-- customer_id    : FK referencing dim_customers(customer_id)
-- product_id     : FK referencing dim_products(product_id)
-- order_amount   : Monetary value of the order in the stated currency
-- order_currency : ISO 4217 currency code. Defaults to 'USD'
-- order_date     : Calendar date the order was placed (YYYY-MM-DD)
-- order_status   : Fulfillment status. Accepted values:
--                  'delivered'  - Successfully delivered to customer
--                  'shipped'    - Dispatched but not yet delivered
--                  'processing' - Being prepared, not yet shipped
--                  'cancelled'  - Order cancelled, will not be fulfilled
