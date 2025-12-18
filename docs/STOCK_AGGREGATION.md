# Stock Aggregation

This project stores stock in two forms:

- **Current stock snapshot (per location):** `stock_levels.current_stock`
- **Historical stock trend (aggregated):** `ts_demand_daily.stock_on_date`

## Source-of-truth tables

### `stock_levels` (per location)
- One row per `(client_id, item_id, location_id)`
- Represents “how much is on hand **at this location** right now”

### `ts_demand_daily.stock_on_date` (aggregated)
- One value per `(client_id, item_id, date_local)`
- Represents “total stock on that date **across all locations**”

## Default aggregation rule

Unless an endpoint explicitly takes a `location_id`, **“current_stock” in API responses and metric calculations means aggregated stock**:

```
current_stock(item_id) = SUM(stock_levels.current_stock) across all locations
```

This matches the default granularity of demand (`ts_demand_daily.units_sold` is also aggregated at the SKU level).

## API implications

- **Dashboard / inventory list metrics**: use aggregated stock by default.
- **Product detail** may also return location breakdowns (when available), but headline metrics still use aggregated stock unless `location_id` is specified.

## Query examples

Aggregate stock across locations:
```sql
SELECT item_id, SUM(current_stock) AS total_stock
FROM stock_levels
WHERE client_id = :client_id
GROUP BY item_id;
```

Stock by location:
```sql
SELECT item_id, location_id, current_stock
FROM stock_levels
WHERE client_id = :client_id
  AND item_id = :item_id;
```

