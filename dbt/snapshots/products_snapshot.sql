{% snapshot products_snapshot %}
    {{
        config(
            target_schema='snapshots',
            unique_key='product_id',
            strategy='timestamp',
            updated_at='updated_at'
        )
    }}

    select
        product_id,
        product_name,
        product_category,
        updated_at
    from {{ ref('stg_products') }}
{% endsnapshot %}
