-- Staging: cleans raw_esg.co2_emissions_per_capita
-- One row per country-year. Casts types, filters nulls and out-of-scope years.

with source as (

    select * from {{ source('raw_esg', 'co2_emissions_per_capita') }}

),

cleaned as (

    select
        country_iso3,
        country_name,
        cast(year as int) as year,

-- PLW (Palau) CO2 per capita is an extreme outlier here (64-203 t/person). Sources disagree:
-- about 60-83 t in World Bank/EDGAR-based series vs about 13 t in OWID. Excluded from the
-- CO2 analysis as a judgment call; nulled, not dropped, so PLW's other indicators survive.
        case
            when country_iso3 = 'PLW' then null
            else cast(value as double precision)
        end as co2_emissions_per_capita

    from source
    where value is not null
      and year between 2000 and 2023
      and trim(country_iso3) <> ''
      and country_iso3 not in (select iso3 from {{ ref('aggregate_codes') }})

)

select * from cleaned