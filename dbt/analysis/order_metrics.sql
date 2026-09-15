-- Order metrics exploration query
-- This file lives in analysis/ and is not materialized by dbt.

with orders as (
    select *
    from {{ ref('fct_orders') }}
),

customers as (
    select *
    from {{ ref('dim_customers') }}
),

products as (
    select *
    from {{ ref('dim_products') }}
),

order_enriched as (
    select
        o.order_id,
        o.customer_id,
        c.customer_name,
        c.customer_email,
        o.product_id,
        p.product_name,
        p.product_category,
        o.order_amount,
        o.order_currency,
        o.order_date,
        o.order_status
    from orders o
    left join customers c on o.customer_id = c.customer_id
    left join products p on o.product_id = p.product_id
)

select
    customer_id,
    customer_name,
    count(order_id) as total_orders,
    sum(order_amount) as total_revenue,
    avg(order_amount) as avg_order_value,
    min(order_amount) as smallest_order,
    max(order_amount) as largest_order
from order_enriched
group by customer_id, customer_name
order by total_revenue desc;
