{% macro audit_model(model_name) %}
    select
        '{{ model_name }}' as model,
        count(*) as row_count,
        count(distinct *) as distinct_rows
    from {{ ref(model_name) }}
{% endmacro %}
