{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select * from {{ source('adventureworks', 'Customer') }}
),

transformed as (
    select
        CustomerID as id,
        AccountNumber as account_number,
        ModifiedDate as created_at,
        ModifiedDate as updated_at
    from source_data
)

select
    id,
    account_number,
    created_at,
    updated_at
from transformed
