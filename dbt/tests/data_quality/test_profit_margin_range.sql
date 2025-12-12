-- Ensure product profit margins are within a sane range when present
select
    product_id,
    profit_margin_pct
from {{ ref('gld_product_performance') }}
where profit_margin_pct is not null
  and (profit_margin_pct < -1000 or profit_margin_pct > 1000)

