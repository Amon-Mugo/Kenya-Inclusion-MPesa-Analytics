with base as (
    select * from {{ source('kenya_inclusion_raw', 'raw_mpesa_statistics') }}
),

renamed as (
    select
        year,
        month,
        agents,
        customers_millions,
        transactions_millions,
        value_ksh_billions,
        round(value_ksh_billions / customers_millions, 2) as avg_value_per_customer_ksh_thousands,
        `source`,
        country,
        country_code,
        ingested_at

    from base
)

select * from renamed
