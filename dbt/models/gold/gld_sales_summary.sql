{{
    config(
        materialized='table'
    )
}}

with sales as (
    select * from {{ ref('slvr_sales_orders') }}
),

daily_summary as (
    select
        cast(order_date as date) as order_date,
        territory_group,
        territory_name,
        category_id,
        subcategory_id,
        count(distinct sales_order_id) as total_orders,
        count(distinct customer_id) as unique_customers,
        sum(order_qty) as total_items_sold,
        sum(line_total) as total_revenue,
        avg(line_total) as avg_order_line_value,
        sum(line_net) as net_revenue,
        sum(tax_amount) as tax_amount,
        sum(freight_amount) as freight_amount,
        sum(case when order_channel = 'Online' then 1 else 0 end) as online_orders,
        sum(case when order_channel = 'Offline' then 1 else 0 end) as offline_orders,
        sum(case when has_discount = 1 then line_total else 0 end) as discounted_revenue
    from sales
    group by
        cast(order_date as date),
        territory_group,
        territory_name,
        category_id,
        subcategory_id
)

select * from daily_summary
