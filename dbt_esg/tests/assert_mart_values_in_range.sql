-- Fails if any indicator has an impossible value.
select *
from {{ ref('mart_country_esg_trends') }}
where (renewable_energy_pct is not null and renewable_energy_pct not between 0 and 100)
   or (unemployment_rate   is not null and unemployment_rate   not between 0 and 100)
   or (gini_index          is not null and gini_index          not between 0 and 100)
   or (life_expectancy     is not null and life_expectancy     not between 20 and 100)
   or (co2_emissions_per_capita is not null and co2_emissions_per_capita < 0)
   or (pm25_air_pollution  is not null and pm25_air_pollution  < 0)
   or co2_emissions_per_capita > 60