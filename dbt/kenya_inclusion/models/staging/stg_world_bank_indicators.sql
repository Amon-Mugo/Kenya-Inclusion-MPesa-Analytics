with source as (
    select * from {{ source('kenya_inclusion_raw', 'raw_world_bank_indicators') }}
),

renamed as (
    select
        indicator_code,
        indicator_name,
        country,
        country_code,
        year,
        round(value, 4) as value,
        ingested_at

    from source
    where value is not null
)

select * from renamed
