{# Use the schema a model names as is, so `metrics` means metrics, not
   <target schema>_metrics. #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name | trim if custom_schema_name else target.schema }}
{%- endmacro %}
