with source as (

    select * from {{ source('raw_esg', 'life_expectancy') }}

),

cleaned as (

    select
        country_iso3,
        country_name,
        cast(year as int) as year,

        -- Fix: source values for CAF 2009 and 2022 are implausible; nulled, not dropped, so other indicators survive
        case
          when cast(value as double precision) between 30 and 95
          then cast(value as double precision)
          else null
        end as life_expectancy

    from source
    where value is not null
      and year between 2000 and 2023
      and trim(country_iso3) <> ''
      and country_iso3 not in (select iso3 from {{ ref('aggregate_codes') }})

)

select * from cleaned
