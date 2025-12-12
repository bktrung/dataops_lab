{{
    config(
        materialized='table'
    )
}}

with bronze_sales as (
    select * from {{ ref('brnz_sales_orders') }}
),

products as (
    select * from {{ ref('slvr_products') }}
),

customers as (
    select * from {{ ref('slvr_customers') }}
),

territory as (
    select * from {{ ref('brnz_territory') }}
),

cleaned as (
    select
        sales_order_id,
        order_detail_id,
        order_date,
        due_date,
        ship_date,
        status,
        sales_order_number,
        purchase_order_number,
        customer_id,
        sales_person_id,
        territory_id,
        product_id,
        order_qty,
        unit_price,
        unit_price_discount,
        line_total,
        subtotal_amount,
        tax_amount,
        freight_amount,
        total_due_amount,
        last_modified_date,
        case
            when online_order_flag = 1 then 'Online'
            else 'Offline'
        end as order_channel,
        unit_price * order_qty as gross_amount,
        line_total / nullif(order_qty, 0) as effective_unit_price,
        case
            when unit_price_discount > 0 then 1
            else 0
        end as has_discount,
        (unit_price * order_qty) * (1 - coalesce(unit_price_discount, 0)) as line_net
    from bronze_sales
    where
        order_qty > 0
        and unit_price >= 0
)

select
    c.sales_order_id,
    c.order_detail_id,
    c.order_date,
    c.due_date,
    c.ship_date,
    c.status,
    c.order_channel,
    c.sales_order_number,
    c.purchase_order_number,
    c.customer_id,
    c.sales_person_id,
    c.territory_id,
    c.product_id,
    c.order_qty,
    c.unit_price,
    c.unit_price_discount,
    c.line_total,
    c.gross_amount,
    c.effective_unit_price,
    c.has_discount,
    c.subtotal_amount,
    c.tax_amount,
    c.freight_amount,
    c.total_due_amount,
    c.last_modified_date,
    c.line_net,
    p.product_name,
    p.category_id,
    p.subcategory_id,
    p.subcategory_name,
    p.list_price,
    cust.full_name as customer_name,
    cust.territory_id as customer_territory_id,
    t.territory_name,
    t.territory_group
from cleaned as c
left join products as p
    on c.product_id = p.product_id
left join customers as cust
    on c.customer_id = cust.customer_id
left join territory as t
    on c.territory_id = t.territory_id
