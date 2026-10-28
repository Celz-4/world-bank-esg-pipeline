-- Mart: one row per country-year with all indicators as columns.
-- Power BI connects to this table.
-- A country-year "spine" is built first so a year with only some indicators
-- still appears (missing indicators show as NULL rather than dropping the row).

with all_keys as (

    select country_iso3, country_name, year from {{ ref('stg_co2_emissions_per_capita') }}
    union all select country_iso3, country_name, year from {{ ref('stg_renewable_energy_pct') }}
    union all select country_iso3, country_name, year from {{ ref('stg_pm25_air_pollution') }}
    union all select country_iso3, country_name, year from {{ ref('stg_gini_index') }}
    union all select country_iso3, country_name, year from {{ ref('stg_unemployment_rate') }}
    union all select country_iso3, country_name, year from {{ ref('stg_life_expectancy') }}

),

spine as (

    select
        country_iso3,
        max(country_name) as country_name,
        year
    from all_keys
    group by country_iso3, year

)

select
    s.country_iso3,
    s.country_name,
    s.year,
    co2.co2_emissions_per_capita,
    renew.renewable_energy_pct,
    pm.pm25_air_pollution,
    gini.gini_index,
    unemp.unemployment_rate,
    life.life_expectancy
from spine s
left join {{ ref('stg_co2_emissions_per_capita') }} co2
    on s.country_iso3 = co2.country_iso3 and s.year = co2.year
left join {{ ref('stg_renewable_energy_pct') }} renew
    on s.country_iso3 = renew.country_iso3 and s.year = renew.year
left join {{ ref('stg_pm25_air_pollution') }} pm
    on s.country_iso3 = pm.country_iso3 and s.year = pm.year
left join {{ ref('stg_gini_index') }} gini
    on s.country_iso3 = gini.country_iso3 and s.year = gini.year
left join {{ ref('stg_unemployment_rate') }} unemp
    on s.country_iso3 = unemp.country_iso3 and s.year = unemp.year
left join {{ ref('stg_life_expectancy') }} life
    on s.country_iso3 = life.country_iso3 and s.year = life.year
order by s.country_iso3, s.year
