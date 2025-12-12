{{
    config(materialized='view')
}}

with territory as (
    select
        TerritoryID as territory_id,
        Name as territory_name,
        CountryRegionCode as country_region_code,
        "Group" as territory_group,
        SalesYTD as sales_ytd,
        SalesLastYear as sales_last_year,
        CostYTD as cost_ytd,
        CostLastYear as cost_last_year,
        ModifiedDate as last_modified_date
    from {{ source('adventureworks', 'SalesTerritory') }}
)

select
    territory_id,
    territory_name,
    country_region_code,
    territory_group,
    sales_ytd,
    sales_last_year,
    cost_ytd,
    cost_last_year,
    last_modified_date
from territory
