{% snapshot customers_snapshot %}
    {{
        config(
            target_schema='snapshots',
            unique_key='customer_id',
            strategy='timestamp',
            updated_at='updated_at'
        )
    }}

    select
        customer_id,
        customer_name,
        customer_email,
        updated_at
    from {{ ref('stg_customers') }}
{% endsnapshot %}
