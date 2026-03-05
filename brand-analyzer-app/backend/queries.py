"""SQL query templates for all analytics views."""

SCHEMA = "catalog_01_9tu9cg.brand_analyzer"

# -- Executive Dashboard --

DASHBOARD_KPIS = f"""
SELECT
    BRAND,
    ROUND(AVG(PRODUCT_PRICE), 2) as avg_price,
    ROUND(AVG(ITEM_REVIEW_RATING), 2) as avg_rating,
    ROUND(AVG(ITEM_REVIEW_COUNT), 0) as avg_reviews,
    ROUND(SUM(CASE WHEN AVAILABILITY_INDICATOR = 'IN_STOCK' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as availability_pct,
    COUNT(DISTINCT ITEM_ID) as product_count
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:brands IS NULL OR BRAND IN (SELECT explode(split(:brands, ','))))
  AND (:retailers IS NULL OR COMPANY_NAME IN (SELECT explode(split(:retailers, ','))))
GROUP BY BRAND
ORDER BY BRAND
"""

DASHBOARD_TRENDS = f"""
SELECT
    PRICE_SCRAPE_DATE as date,
    BRAND,
    ROUND(AVG(PRODUCT_PRICE), 2) as avg_price,
    ROUND(AVG(ITEM_REVIEW_RATING), 2) as avg_rating,
    ROUND(SUM(CASE WHEN AVAILABILITY_INDICATOR = 'IN_STOCK' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as availability_pct
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:brands IS NULL OR BRAND IN (SELECT explode(split(:brands, ','))))
GROUP BY PRICE_SCRAPE_DATE, BRAND
ORDER BY PRICE_SCRAPE_DATE, BRAND
"""

# -- Price Intelligence --

PRICE_COMPARISON = f"""
SELECT
    BRAND,
    BENCHMARK_SUBCATG as category,
    ROUND(AVG(PRODUCT_PRICE), 2) as avg_price,
    ROUND(MIN(PRODUCT_PRICE), 2) as min_price,
    ROUND(MAX(PRODUCT_PRICE), 2) as max_price
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:brands IS NULL OR BRAND IN (SELECT explode(split(:brands, ','))))
  AND (:retailers IS NULL OR COMPANY_NAME IN (SELECT explode(split(:retailers, ','))))
GROUP BY BRAND, BENCHMARK_SUBCATG
ORDER BY BENCHMARK_SUBCATG, avg_price
"""

PRICE_TRENDS = f"""
SELECT
    PRICE_SCRAPE_DATE as date,
    BRAND,
    BENCHMARK_SUBCATG as category,
    ROUND(AVG(PRODUCT_PRICE), 2) as avg_price
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:brands IS NULL OR BRAND IN (SELECT explode(split(:brands, ','))))
  AND (:category IS NULL OR BENCHMARK_SUBCATG = :category)
GROUP BY PRICE_SCRAPE_DATE, BRAND, BENCHMARK_SUBCATG
ORDER BY PRICE_SCRAPE_DATE, BRAND
"""

PRICE_GAP = f"""
WITH brand_prices AS (
    SELECT
        BENCHMARK_SUBCATG as category,
        BRAND,
        ROUND(AVG(PRODUCT_PRICE), 2) as avg_price
    FROM {SCHEMA}.us_households_daily
    WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
      AND (:retailers IS NULL OR COMPANY_NAME IN (SELECT explode(split(:retailers, ','))))
    GROUP BY BENCHMARK_SUBCATG, BRAND
),
competitor_avg AS (
    SELECT category, ROUND(AVG(avg_price), 2) as comp_avg_price
    FROM brand_prices
    WHERE BRAND != 'TKO Combat'
    GROUP BY category
)
SELECT
    bp.category,
    bp.BRAND,
    bp.avg_price,
    ca.comp_avg_price,
    ROUND(bp.avg_price - ca.comp_avg_price, 2) as price_gap,
    ROUND((bp.avg_price - ca.comp_avg_price) / ca.comp_avg_price * 100, 1) as gap_pct
FROM brand_prices bp
JOIN competitor_avg ca ON bp.category = ca.category
WHERE bp.BRAND = 'TKO Combat'
ORDER BY bp.category
"""

# -- Market Share --

MARKET_SHARE = f"""
SELECT
    BRAND,
    COUNT(DISTINCT ITEM_ID) as product_count,
    ROUND(COUNT(DISTINCT ITEM_ID) * 100.0 / SUM(COUNT(DISTINCT ITEM_ID)) OVER(), 1) as share_pct
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:retailers IS NULL OR COMPANY_NAME IN (SELECT explode(split(:retailers, ','))))
  AND (:category IS NULL OR BENCHMARK_SUBCATG = :category)
GROUP BY BRAND
ORDER BY product_count DESC
"""

MARKET_SHARE_BY_RETAILER = f"""
SELECT
    COMPANY_NAME as retailer,
    BRAND,
    COUNT(DISTINCT ITEM_ID) as product_count,
    ROUND(COUNT(DISTINCT ITEM_ID) * 100.0 / SUM(COUNT(DISTINCT ITEM_ID)) OVER(PARTITION BY COMPANY_NAME), 1) as share_pct
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:brands IS NULL OR BRAND IN (SELECT explode(split(:brands, ','))))
GROUP BY COMPANY_NAME, BRAND
ORDER BY COMPANY_NAME, share_pct DESC
"""

MARKET_SHARE_TREND = f"""
SELECT
    PRICE_SCRAPE_DATE as date,
    BRAND,
    COUNT(DISTINCT ITEM_ID) as product_count
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
GROUP BY PRICE_SCRAPE_DATE, BRAND
ORDER BY PRICE_SCRAPE_DATE, BRAND
"""

# -- Brand Performance --

BRAND_SCORECARD = f"""
SELECT
    BRAND,
    ROUND(AVG(ITEM_REVIEW_RATING), 2) as avg_rating,
    ROUND(SUM(ITEM_REVIEW_COUNT), 0) as total_reviews,
    ROUND(AVG(PRODUCT_PRICE), 2) as avg_price,
    ROUND(SUM(CASE WHEN AVAILABILITY_INDICATOR = 'IN_STOCK' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as availability_pct,
    COUNT(DISTINCT ITEM_ID) as product_count,
    COUNT(DISTINCT BENCHMARK_SUBCATG) as category_count,
    ROUND(AVG(ITEM_REVIEW_RATING) * 20 + SUM(CASE WHEN AVAILABILITY_INDICATOR = 'IN_STOCK' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) * 0.3 + COUNT(DISTINCT ITEM_ID) * 0.5, 1) as health_index
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:retailers IS NULL OR COMPANY_NAME IN (SELECT explode(split(:retailers, ','))))
GROUP BY BRAND
ORDER BY health_index DESC
"""

RATING_DISTRIBUTION = f"""
SELECT
    BRAND,
    FLOOR(ITEM_REVIEW_RATING) as rating_bucket,
    COUNT(*) as count
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:brands IS NULL OR BRAND IN (SELECT explode(split(:brands, ','))))
GROUP BY BRAND, FLOOR(ITEM_REVIEW_RATING)
ORDER BY BRAND, rating_bucket
"""

# -- Search Visibility (SERP) --

SERP_RANKINGS = f"""
SELECT
    domain_name,
    benchmark_dept as category,
    ROUND(AVG(position), 1) as avg_position,
    ROUND(AVG(search_engine_ranking), 2) as avg_ranking,
    COUNT(*) as appearances
FROM {SCHEMA}.us_serps_daily
GROUP BY domain_name, benchmark_dept
ORDER BY avg_position
"""

SERP_SHARE_OF_VOICE = f"""
SELECT
    domain_name,
    COUNT(*) as total_appearances,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as share_of_voice
FROM {SCHEMA}.us_serps_daily
WHERE position <= 10
GROUP BY domain_name
ORDER BY total_appearances DESC
"""

SERP_BY_KEYWORD = f"""
SELECT
    benchmark_dept as keyword_category,
    domain_name,
    ROUND(AVG(position), 1) as avg_position,
    COUNT(*) as appearances
FROM {SCHEMA}.us_serps_daily
GROUP BY benchmark_dept, domain_name
ORDER BY benchmark_dept, avg_position
"""

# -- Inventory & Availability --

AVAILABILITY_BY_BRAND = f"""
SELECT
    BRAND,
    AVAILABILITY_INDICATOR as status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(PARTITION BY BRAND), 1) as pct
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:retailers IS NULL OR COMPANY_NAME IN (SELECT explode(split(:retailers, ','))))
GROUP BY BRAND, AVAILABILITY_INDICATOR
ORDER BY BRAND, status
"""

AVAILABILITY_TREND = f"""
SELECT
    PRICE_SCRAPE_DATE as date,
    BRAND,
    ROUND(SUM(CASE WHEN AVAILABILITY_INDICATOR = 'IN_STOCK' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as in_stock_pct
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:brands IS NULL OR BRAND IN (SELECT explode(split(:brands, ','))))
GROUP BY PRICE_SCRAPE_DATE, BRAND
ORDER BY PRICE_SCRAPE_DATE, BRAND
"""

AVAILABILITY_BY_RETAILER = f"""
SELECT
    COMPANY_NAME as retailer,
    BRAND,
    ROUND(SUM(CASE WHEN AVAILABILITY_INDICATOR = 'IN_STOCK' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as in_stock_pct,
    ROUND(SUM(CASE WHEN AVAILABILITY_INDICATOR = 'OUT_OF_STOCK' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as oos_pct
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
GROUP BY COMPANY_NAME, BRAND
ORDER BY COMPANY_NAME, BRAND
"""

# -- Sentiment & Reviews --

REVIEW_TRENDS = f"""
SELECT
    PRICE_SCRAPE_DATE as date,
    BRAND,
    ROUND(AVG(ITEM_REVIEW_RATING), 2) as avg_rating,
    ROUND(AVG(ITEM_REVIEW_COUNT), 0) as avg_review_count
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:brands IS NULL OR BRAND IN (SELECT explode(split(:brands, ','))))
GROUP BY PRICE_SCRAPE_DATE, BRAND
ORDER BY PRICE_SCRAPE_DATE, BRAND
"""

SENTIMENT_COMPARISON = f"""
SELECT
    BRAND,
    ROUND(AVG(ITEM_REVIEW_RATING), 2) as avg_rating,
    ROUND(MAX(ITEM_REVIEW_COUNT), 0) as max_reviews,
    ROUND(AVG(ITEM_REVIEW_COUNT), 0) as avg_reviews,
    SUM(CASE WHEN ITEM_REVIEW_RATING >= 4.5 THEN 1 ELSE 0 END) as excellent_count,
    SUM(CASE WHEN ITEM_REVIEW_RATING >= 4.0 AND ITEM_REVIEW_RATING < 4.5 THEN 1 ELSE 0 END) as good_count,
    SUM(CASE WHEN ITEM_REVIEW_RATING >= 3.5 AND ITEM_REVIEW_RATING < 4.0 THEN 1 ELSE 0 END) as average_count,
    SUM(CASE WHEN ITEM_REVIEW_RATING < 3.5 THEN 1 ELSE 0 END) as below_avg_count
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
GROUP BY BRAND
ORDER BY avg_rating DESC
"""

# -- Scenario Planner --

SCENARIO_BASE_DATA = f"""
SELECT
    BRAND,
    BENCHMARK_SUBCATG as category,
    ROUND(AVG(PRODUCT_PRICE), 2) as avg_price,
    ROUND(AVG(ITEM_REVIEW_RATING), 2) as avg_rating,
    ROUND(SUM(CASE WHEN AVAILABILITY_INDICATOR = 'IN_STOCK' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as availability_pct,
    COUNT(DISTINCT ITEM_ID) as product_count
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
GROUP BY BRAND, BENCHMARK_SUBCATG
ORDER BY BRAND, category
"""

# -- Filters --

FILTER_OPTIONS = f"""
SELECT
    'brands' as filter_type,
    COLLECT_SET(BRAND) as options
FROM {SCHEMA}.us_households_daily
UNION ALL
SELECT
    'retailers' as filter_type,
    COLLECT_SET(COMPANY_NAME) as options
FROM {SCHEMA}.us_households_daily
UNION ALL
SELECT
    'categories' as filter_type,
    COLLECT_SET(BENCHMARK_SUBCATG) as options
FROM {SCHEMA}.us_households_daily
"""

DATE_RANGE = f"""
SELECT
    MIN(PRICE_SCRAPE_DATE) as min_date,
    MAX(PRICE_SCRAPE_DATE) as max_date
FROM {SCHEMA}.us_households_daily
"""
