with source as (
    select * from {{ source('kenya_inclusion_raw', 'raw_finaccess_county') }}
),

renamed as (
    select
        county_code,
        upper(county) as county,
        formal_inclusion_pct,
        mobile_money_pct,
        bank_account_pct,
        excluded_pct,
        round(mobile_money_pct - bank_account_pct, 2) as mobile_only_gap,
        survey_year,
        `source`,
        ingested_at

    from source
)

select * from renamed