with customer_raw as (
    select * from {{ source('raw', 'customer') }}
),

orders_raw as (
    select * from {{ source('raw', 'orders') }}
),

lineitem_raw as (
    select * from {{ source('raw', 'lineitem') }}
)

select
    c._c0 as customer_key,
    c._c1 as customer_name,
    c._c3 as market_segment,
    count(distinct o._c0) as total_orders,
    sum(l._c5) as total_revenue
from customer_raw c
join orders_raw o on c._c0 = o._c1
join lineitem_raw l on o._c0 = l._c0
group by c._c0, c._c1, c._c3
order by total_revenue desc