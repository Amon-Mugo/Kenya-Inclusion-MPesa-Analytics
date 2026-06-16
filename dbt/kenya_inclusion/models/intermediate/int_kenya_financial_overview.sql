with world_bank as(
    select *from{{ref('stg_world_bank_indicators')}}
),
mpesa as(
    SELECT * FROM {{ref('stg_mpesa_statistics')}}
),
--pivoting the world bank data to get the indicators as columns
account_ownership as (
    select year, value as account_ownership_pct
    from world_bank
    where indicator_name = 'account_ownership_pct'

),
bank_branches as (
    select year,value as bank_branches_per_100k
    from world_bank
    where indicator_name= 'bank_branches_per_100k'
),
atms as (
    select year,value as atms_per_100k
    from world_bank
    where indicator_name= 'atms_per_100k'
),
joined as (
    select 
    m.year,
    m.agents,
    m.customers_millions,
    m.transactions_millions,
    m.value_ksh_billions,
    m.avg_value_per_customer_ksh_thousands,
    ao.account_ownership_pct,
    bb.bank_branches_per_100k,
    a.atms_per_100k
    from mpesa m
    left join account_ownership ao on m.year = ao.year
    left join bank_branches bb on m.year = bb.year
    left join atms a on m.year = a.year
)
select * from joined