with src_product as (
    select * from {{ source('adventureworks_production', 'Product') }}
),

src_product_subcategory as (
    select * from {{ source('adventureworks_production', 'ProductSubcategory') }}
),

staged as (
    select
        p.ProductID,
        p.Name as ProductName,
        p.ProductNumber,
        p.MakeFlag,
        p.FinishedGoodsFlag,
        p.Color,
        p.SafetyStockLevel,
        p.ReorderPoint,
        p.StandardCost,
        p.ListPrice,
        p.Size,
        p.SizeUnitMeasureCode,
        p.WeightUnitMeasureCode,
        p.Weight,
        p.DaysToManufacture,
        p.ProductLine,
        p.[Class] as product_class,
        p.Style as product_style,
        p.ProductSubcategoryID,
        p.ProductModelID,
        p.SellStartDate,
        p.SellEndDate,
        p.DiscontinuedDate,
        ps.Name as SubcategoryName,
        ps.ProductCategoryID,
        p.ModifiedDate as last_modified_date
    from src_product as p
    left join src_product_subcategory as ps
        on p.ProductSubcategoryID = ps.ProductSubcategoryID
)

select
    ProductID,
    ProductName,
    ProductNumber,
    MakeFlag,
    FinishedGoodsFlag,
    Color,
    SafetyStockLevel,
    ReorderPoint,
    StandardCost,
    ListPrice,
    Size,
    SizeUnitMeasureCode,
    WeightUnitMeasureCode,
    Weight,
    DaysToManufacture,
    ProductLine,
    product_class,
    product_style,
    ProductSubcategoryID,
    ProductModelID,
    SellStartDate,
    SellEndDate,
    DiscontinuedDate,
    SubcategoryName,
    ProductCategoryID,
    last_modified_date
from staged
