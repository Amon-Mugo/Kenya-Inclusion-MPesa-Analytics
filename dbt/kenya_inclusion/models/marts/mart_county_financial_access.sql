with base as (
    select * from {{ ref('stg_finaccess_county') }}
),
final as (
    select
     county_code,
     county,
     formal_inclusion_pct,
     mobile_money_pct,
     bank_account_pct,
     excluded_pct,
     mobile_only_gap,
     CASE
        WHEN formal_inclusion_pct >= 80 THEN 'HIGH'
        WHEN formal_inclusion_pct >= 60 THEN 'MEDIUM'
        WHEN formal_inclusion_pct >= 40 THEN 'LOW'
        ELSE 'VERY LOW INCLUSION'
     END as inclusion_segment,
     CASE
        WHEN excluded_pct >= 25 THEN 'HIGH'
        WHEN excluded_pct >= 10 THEN 'MEDIUM'
        ELSE 'LOW'
     END as exclusion_risk,
     survey_year,
     ingested_at
    from base
)
select * from final
