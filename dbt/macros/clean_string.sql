{% macro clean_string(column_name) %}
    trim(lower({{ column_name }}))
{% endmacro %}
