{{
    config(
        materialized='table'
    )
}}

with customers as (
    select * from {{ ref('slvr_customers') }}
),

sales as (
    select * from {{ ref('slvr_sales_orders') }}
),

customer_sales as (
    select
        c.customer_id,
        c.full_name,
        c.territory_id,
        s.territory_group,
        count(distinct s.sales_order_id) as total_orders,
        sum(s.line_total) as total_revenue,
        sum(s.line_net) as net_revenue,
        sum(s.order_qty) as total_items_purchased,
        avg(nullif(s.line_total,0)) as avg_order_value,
        min(s.order_date) as first_order_date,
        max(s.order_date) as last_order_date,
        sum(case when s.has_discount = 1 then 1 else 0 end) as orders_with_discount
    from customers c
    left join sales s
        on c.customer_id = s.customer_id
    group by c.customer_id, c.full_name, c.territory_id, s.territory_group
)

select * from customer_sales
