with source as (
    select * from {{ source('raw', 'customers') }}
),

cleaned as (
    select
        customer_id,
        initcap(customer_name) as customer_name,
        lower(customer_email) as customer_email
    from source
)

select * from cleaned;
