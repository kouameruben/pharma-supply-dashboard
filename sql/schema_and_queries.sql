-- ============================================================================
-- create_tables.sql — Database Schema for Pharma Supply Chain
-- Author: Kouamé Ruben
-- ============================================================================

CREATE TABLE IF NOT EXISTS products (
    product_id      VARCHAR(10) PRIMARY KEY,
    product_name    VARCHAR(100) NOT NULL,
    category        VARCHAR(50),
    unit_cost_fcfa  INTEGER,
    lead_time_days  INTEGER,
    shelf_life_months INTEGER,
    criticality     VARCHAR(20) CHECK (criticality IN ('Vital', 'Essentiel', 'Non-essentiel'))
);

CREATE TABLE IF NOT EXISTS districts (
    district_id VARCHAR(10) PRIMARY KEY,
    name        VARCHAR(50) NOT NULL,
    pop         INTEGER,
    lat         DECIMAL(6,2),
    lon         DECIMAL(6,2)
);

CREATE TABLE IF NOT EXISTS consumption_monthly (
    product_id      VARCHAR(10) REFERENCES products(product_id),
    district_id     VARCHAR(10) REFERENCES districts(district_id),
    month           DATE NOT NULL,
    consumption     INTEGER DEFAULT 0,
    stock_beginning INTEGER DEFAULT 0,
    orders_received INTEGER DEFAULT 0,
    stock_end       INTEGER DEFAULT 0,
    stockout        BOOLEAN DEFAULT FALSE,
    rainfall_mm     DECIMAL(5,1),
    PRIMARY KEY (product_id, district_id, month)
);

CREATE INDEX idx_consumption_month ON consumption_monthly(month);
CREATE INDEX idx_consumption_district ON consumption_monthly(district_id);

-- ============================================================================
-- kpi_queries.sql — KPI Calculation Queries
-- ============================================================================

-- Global KPIs for latest month
WITH latest AS (SELECT MAX(month) as max_month FROM consumption_monthly)
SELECT 
    c.month,
    COUNT(DISTINCT c.product_id) AS n_products,
    COUNT(DISTINCT c.district_id) AS n_districts,
    SUM(c.consumption) AS total_consumption,
    SUM(c.consumption * p.unit_cost_fcfa) AS total_value_fcfa,
    ROUND(AVG(CASE WHEN c.consumption > 0 
        THEN LEAST(1.0, (c.stock_beginning + c.orders_received)::FLOAT / c.consumption) 
        ELSE 1.0 END), 3) AS avg_fill_rate,
    ROUND(AVG(c.stockout::INT), 3) AS stockout_rate,
    SUM(CASE WHEN c.stockout AND p.criticality = 'Vital' THEN 1 ELSE 0 END) AS critical_stockouts
FROM consumption_monthly c
JOIN products p ON c.product_id = p.product_id
CROSS JOIN latest l
WHERE c.month = l.max_month
GROUP BY c.month;

-- District ranking by stockout severity
SELECT 
    d.name AS district_name,
    d.pop AS population,
    COUNT(*) AS total_records,
    SUM(c.stockout::INT) AS stockout_count,
    ROUND(AVG(c.stockout::INT), 3) AS stockout_rate,
    SUM(CASE WHEN c.stockout AND p.criticality = 'Vital' THEN 1 ELSE 0 END) AS vital_stockouts,
    SUM(c.consumption * p.unit_cost_fcfa) AS total_value_fcfa
FROM consumption_monthly c
JOIN districts d ON c.district_id = d.district_id
JOIN products p ON c.product_id = p.product_id
WHERE c.month = (SELECT MAX(month) FROM consumption_monthly)
GROUP BY d.name, d.pop
ORDER BY stockout_rate DESC;

-- Monthly trend with YoY comparison
SELECT 
    DATE_TRUNC('month', c.month) AS month,
    SUM(c.consumption) AS total_consumption,
    SUM(c.consumption * p.unit_cost_fcfa) AS total_value,
    ROUND(AVG(c.stockout::INT), 3) AS stockout_rate,
    LAG(SUM(c.consumption), 12) OVER (ORDER BY DATE_TRUNC('month', c.month)) AS consumption_yoy,
    ROUND(
        (SUM(c.consumption)::FLOAT / NULLIF(LAG(SUM(c.consumption), 12) 
         OVER (ORDER BY DATE_TRUNC('month', c.month)), 0) - 1), 3
    ) AS yoy_growth
FROM consumption_monthly c
JOIN products p ON c.product_id = p.product_id
GROUP BY DATE_TRUNC('month', c.month)
ORDER BY month;

-- Top products at risk of stockout
SELECT 
    p.product_id,
    p.product_name,
    p.criticality,
    p.category,
    SUM(c.stockout::INT) AS districts_in_stockout,
    ROUND(AVG(CASE WHEN c.consumption > 0 
        THEN c.stock_end::FLOAT / (c.consumption / 30.0) ELSE NULL END), 1) AS avg_days_of_stock,
    SUM(c.consumption) AS total_demand
FROM consumption_monthly c
JOIN products p ON c.product_id = p.product_id
WHERE c.month = (SELECT MAX(month) FROM consumption_monthly)
GROUP BY p.product_id, p.product_name, p.criticality, p.category
HAVING SUM(c.stockout::INT) > 0
ORDER BY 
    CASE p.criticality WHEN 'Vital' THEN 1 WHEN 'Essentiel' THEN 2 ELSE 3 END,
    districts_in_stockout DESC;
