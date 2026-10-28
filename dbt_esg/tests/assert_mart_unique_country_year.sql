-- Fails if any country-year appears more than once in the mart.
select country_iso3, year, count(*) as n
from {{ ref('mart_country_esg_trends') }}
group by country_iso3, year
having count(*) > 1
