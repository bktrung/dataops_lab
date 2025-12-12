{{
    config(
        materialized='table'
    )
}}

with bronze_customers as (
    select
        CustomerID,
        FirstName,
        LastName,
        EmailPromotion,
        StoreID,
        TerritoryID,
        last_modified_date
    from {{ ref('brnz_customers') }}
),

cleaned as (
    select
        CustomerID as customer_id,
        EmailPromotion as email_promotion,
        StoreID as store_id,
        TerritoryID as territory_id,
        last_modified_date,
        coalesce(FirstName, 'Unknown') as first_name,
        coalesce(LastName, 'Unknown') as last_name,
        concat(coalesce(FirstName, 'Unknown'), ' ', coalesce(LastName, 'Unknown')) as full_name
    from bronze_customers
)

select
    customer_id,
    first_name,
    last_name,
    full_name,
    email_promotion,
    store_id,
    territory_id,
    last_modified_date
from cleaned
