-- Staging: cleans raw_esg.gini_index
-- One row per country-year. Casts types, filters nulls and out-of-scope years.

with source as (

    select * from {{ source('raw_esg', 'gini_index') }}

),

cleaned as (

    select
        country_iso3,
        country_name,
        cast(year as int)               as year,
        cast(value as double precision) as gini_index
    from source
    where value is not null
      and year between 2000 and 2023
      and trim(country_iso3) <> ''
      and country_iso3 not in (select iso3 from {{ ref('aggregate_codes') }})


)

select * from cleaned
