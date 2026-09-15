select
    c.customer_id,
    c.customer_name,
    count(o.order_id) as total_orders,
    sum(o.order_amount) as total_revenue
from {{ ref('fct_orders') }} o
join {{ ref('dim_customers') }} c
  on o.customer_id = c.customer_id
group by c.customer_id, c.customer_name
order by total_revenue desc;
