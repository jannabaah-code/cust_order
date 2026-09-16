with source as (
    select * from {{ source('raw', 'orders') }}
),

cleaned as (
    select
        order_id,
        customer_id,
        product_id,
        cast(order_amount as float) as order_amount,
        order_currency,
        order_date,
        order_status
    from source
)

select * from cleaned;
