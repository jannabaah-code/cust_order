select
    o.order_id,
    o.customer_id,
    o.product_id,
    o.order_amount,
    o.order_currency,
    o.order_date,
    o.order_status
from {{ ref('stg_orders') }} o
