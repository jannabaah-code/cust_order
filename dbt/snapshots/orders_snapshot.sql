{% snapshot orders_snapshot %}
    {{
        config(
            target_schema='snapshots',
            unique_key='order_id',
            strategy='timestamp',
            updated_at='updated_at'
        )
    }}

    select
        order_id,
        customer_id,
        product_id,
        order_amount,
        order_currency,
        order_date,
        order_status,
        updated_at
    from {{ ref('stg_orders') }}
{% endsnapshot %}
