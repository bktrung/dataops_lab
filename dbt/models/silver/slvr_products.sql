{{
    config(
        materialized='table'
    )
}}

with bronze_products as (
    select
        ProductID,
        ProductName,
        ProductNumber,
        Color,
        StandardCost,
        ListPrice,
        [Size] as product_size,
        Weight,
        ProductLine,
        product_class,
        product_style,
        ProductSubcategoryID,
        SubcategoryName,
        ProductCategoryID,
        SellStartDate,
        SellEndDate,
        DiscontinuedDate,
        last_modified_date
    from {{ ref('brnz_products') }}
),

cleaned as (
    select
        ProductID as product_id,
        ProductName as product_name,
        ProductNumber as product_number,
        StandardCost as standard_cost,
        ListPrice as list_price,
        ProductLine as product_line,
        product_class,
        ProductSubcategoryID as subcategory_id,
        ProductCategoryID as category_id,
        SellStartDate as sell_start_date,
        SellEndDate as sell_end_date,
        last_modified_date,
        coalesce(Color, 'N/A') as color,
        coalesce(product_size, 'N/A') as [size],
        coalesce(Weight, 0) as weight,
        coalesce(product_style, 'N/A') as product_style,
        coalesce(SubcategoryName, 'Uncategorized') as subcategory_name,
        case when DiscontinuedDate is not null then 1 else 0 end as is_discontinued
    from bronze_products
)

select
    product_id,
    product_name,
    product_number,
    color,
    standard_cost,
    list_price,
    [size],
    weight,
    product_line,
    product_class,
    product_style,
    subcategory_id,
    subcategory_name,
    category_id,
    sell_start_date,
    sell_end_date,
    is_discontinued,
    last_modified_date
from cleaned
