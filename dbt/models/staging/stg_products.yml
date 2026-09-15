with source as (
    select * from {{ source('raw', 'products') }}
),

cleaned as (
    select
        product_id,
        product_name,
        product_category
    from source
)

select * from cleaned;
