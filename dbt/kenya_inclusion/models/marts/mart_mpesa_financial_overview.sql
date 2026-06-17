with overview as (

    select * from {{ ref('int_kenya_financial_overview') }}

),

with_lags as (

    select
        *,
        lag(transactions_millions) over (order by year) as prev_transactions_millions,
        lag(value_ksh_billions) over (order by year) as prev_value_ksh_billions,
        lag(customers_millions) over (order by year) as prev_customers_millions

    from overview

),

with_growth as (

    select
        year,
        agents,
        customers_millions,
        transactions_millions,
        value_ksh_billions,
        avg_value_per_customer_ksh_thousands,
        account_ownership_pct,
        bank_branches_per_100k,
        atms_per_100k,

        round((transactions_millions - prev_transactions_millions) / prev_transactions_millions * 100, 1) as transactions_yoy_growth_pct,
        round((value_ksh_billions - prev_value_ksh_billions) / prev_value_ksh_billions * 100, 1) as value_yoy_growth_pct,
        round((customers_millions - prev_customers_millions) / prev_customers_millions * 100, 1) as customers_yoy_growth_pct

    from with_lags

),

final as (

    select
        year,
        agents,
        customers_millions,
        transactions_millions,
        value_ksh_billions,
        avg_value_per_customer_ksh_thousands,
        account_ownership_pct,
        bank_branches_per_100k,
        atms_per_100k,
        transactions_yoy_growth_pct,
        value_yoy_growth_pct,
        customers_yoy_growth_pct,
        round(agents / (customers_millions * 1000), 2) as agents_per_1000_customers,
        round(account_ownership_pct, 1) as formal_account_ownership_pct

    from with_growth

)

select * from final