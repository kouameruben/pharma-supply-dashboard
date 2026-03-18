# ============================================================================
# data_processing.R — R Alternative Pipeline (data.table)
# Author: Kouamé Ruben
# Description: Same pipeline as Python, but using R data.table for performance
# ============================================================================

library(data.table)
library(arrow)

cat("── R data.table Pipeline ──\n")

# Load
dt <- read_parquet("data/processed/pharma_enriched.parquet") |> setDT()
cat(sprintf("Loaded %s rows\n", format(nrow(dt), big.mark = ",")))

# District aggregation (data.table — fast on 1M+ rows)
district_kpi <- dt[, .(
  total_consumption  = sum(consumption),
  total_value        = sum(consumption_value),
  avg_fill_rate      = mean(fill_rate, na.rm = TRUE),
  stockout_rate      = mean(stockout),
  n_products_stockout = sum(stockout > 0)
), keyby = .(district_id, name, month)]

# Product ranking by risk
latest_month <- max(dt$month)
product_risk <- dt[month == latest_month, .(
  total_stockouts    = sum(stockout),
  avg_days_of_stock  = mean(days_of_stock, na.rm = TRUE),
  avg_fill_rate      = mean(fill_rate, na.rm = TRUE),
  total_consumption  = sum(consumption)
), keyby = .(product_id, product_name, criticality)]

product_risk[, risk_score := round(
  (1 - avg_fill_rate) * 40 +
  total_stockouts * 10 +
  fifelse(avg_days_of_stock < 15, (15 - avg_days_of_stock) * 2, 0)
)]

setorder(product_risk, -risk_score)
cat("\n── Top 10 At-Risk Products ──\n")
print(head(product_risk, 10))

# YoY comparison
dt[, year := year(month)]
yoy <- dt[, .(consumption = sum(consumption)), keyby = .(year, category)]
yoy_wide <- dcast(yoy, category ~ year, value.var = "consumption")

cat("\n── Year-over-Year by Category ──\n")
print(yoy_wide)

cat("\n✅ R pipeline complete.\n")
