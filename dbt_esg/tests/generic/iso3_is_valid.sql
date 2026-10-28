{% test iso3_is_valid(model, column_name) %}

select {{ column_name }}
from {{ model }}
where {{ column_name }} is null
   or length({{ column_name }}) <> 3

{% endtest %}