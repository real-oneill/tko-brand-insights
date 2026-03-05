"""FastAPI backend for Brand Analyzer Databricks App."""

import os
import json
import math
import random
from typing import Optional
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="TKO Combat Brand Analyzer")

WAREHOUSE_ID = os.environ.get("WAREHOUSE_ID", "d75e71068b3fa181")
SCHEMA = "catalog_01_9tu9cg.brand_analyzer"

# Detect environment
IS_DATABRICKS_APP = bool(os.environ.get("DATABRICKS_APP_NAME"))


def get_connection():
    from databricks.sdk import WorkspaceClient
    from databricks import sql as dbsql

    if IS_DATABRICKS_APP:
        w = WorkspaceClient()
    else:
        profile = os.environ.get("DATABRICKS_PROFILE", "tko-buildcon")
        w = WorkspaceClient(profile=profile)

    host = w.config.host
    if host and host.startswith("https://"):
        host = host.replace("https://", "")

    return dbsql.connect(
        server_hostname=host,
        http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
        credentials_provider=lambda: w.config.authenticate,
    )


def execute_query(sql: str, params: dict = None) -> list:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        processed_sql = sql
        if params:
            for key, val in params.items():
                placeholder = f":{key}"
                if val is None:
                    processed_sql = processed_sql.replace(placeholder, "NULL")
                else:
                    processed_sql = processed_sql.replace(placeholder, f"'{val}'")
        cursor.execute(processed_sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()


def serialize(data):
    result = []
    for row in data:
        clean = {}
        for k, v in row.items():
            if v is None:
                clean[k] = None
            elif isinstance(v, (int, float)):
                if math.isnan(v) or math.isinf(v):
                    clean[k] = None
                else:
                    clean[k] = v
            else:
                clean[k] = str(v)
        result.append(clean)
    return result


# ---- SQL Queries ----

Q_DASHBOARD_KPIS = f"""
SELECT BRAND, ROUND(AVG(PRODUCT_PRICE), 2) as avg_price,
  ROUND(AVG(ITEM_REVIEW_RATING), 2) as avg_rating,
  ROUND(AVG(ITEM_REVIEW_COUNT), 0) as avg_reviews,
  ROUND(SUM(CASE WHEN AVAILABILITY_INDICATOR = 'IN_STOCK' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as availability_pct,
  COUNT(DISTINCT ITEM_ID) as product_count
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:brands IS NULL OR BRAND IN (SELECT explode(split(:brands, ','))))
  AND (:retailers IS NULL OR COMPANY_NAME IN (SELECT explode(split(:retailers, ','))))
GROUP BY BRAND ORDER BY BRAND
"""

Q_DASHBOARD_TRENDS = f"""
SELECT PRICE_SCRAPE_DATE as date, BRAND,
  ROUND(AVG(PRODUCT_PRICE), 2) as avg_price,
  ROUND(AVG(ITEM_REVIEW_RATING), 2) as avg_rating,
  ROUND(SUM(CASE WHEN AVAILABILITY_INDICATOR = 'IN_STOCK' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as availability_pct
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:brands IS NULL OR BRAND IN (SELECT explode(split(:brands, ','))))
GROUP BY PRICE_SCRAPE_DATE, BRAND ORDER BY PRICE_SCRAPE_DATE, BRAND
"""

Q_PRICE_COMPARISON = f"""
SELECT BRAND, BENCHMARK_SUBCATG as category,
  ROUND(AVG(PRODUCT_PRICE), 2) as avg_price,
  ROUND(MIN(PRODUCT_PRICE), 2) as min_price,
  ROUND(MAX(PRODUCT_PRICE), 2) as max_price
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:brands IS NULL OR BRAND IN (SELECT explode(split(:brands, ','))))
  AND (:retailers IS NULL OR COMPANY_NAME IN (SELECT explode(split(:retailers, ','))))
GROUP BY BRAND, BENCHMARK_SUBCATG ORDER BY BENCHMARK_SUBCATG, avg_price
"""

Q_PRICE_TRENDS = f"""
SELECT PRICE_SCRAPE_DATE as date, BRAND, BENCHMARK_SUBCATG as category,
  ROUND(AVG(PRODUCT_PRICE), 2) as avg_price
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:brands IS NULL OR BRAND IN (SELECT explode(split(:brands, ','))))
  AND (:category IS NULL OR BENCHMARK_SUBCATG = :category)
GROUP BY PRICE_SCRAPE_DATE, BRAND, BENCHMARK_SUBCATG ORDER BY PRICE_SCRAPE_DATE, BRAND
"""

Q_PRICE_GAP = f"""
WITH brand_prices AS (
  SELECT BENCHMARK_SUBCATG as category, BRAND, ROUND(AVG(PRODUCT_PRICE), 2) as avg_price
  FROM {SCHEMA}.us_households_daily
  WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
    AND (:retailers IS NULL OR COMPANY_NAME IN (SELECT explode(split(:retailers, ','))))
  GROUP BY BENCHMARK_SUBCATG, BRAND
), competitor_avg AS (
  SELECT category, ROUND(AVG(avg_price), 2) as comp_avg_price
  FROM brand_prices WHERE BRAND != 'TKO Combat' GROUP BY category
)
SELECT bp.category, bp.avg_price, ca.comp_avg_price,
  ROUND(bp.avg_price - ca.comp_avg_price, 2) as price_gap,
  ROUND((bp.avg_price - ca.comp_avg_price) / ca.comp_avg_price * 100, 1) as gap_pct
FROM brand_prices bp JOIN competitor_avg ca ON bp.category = ca.category
WHERE bp.BRAND = 'TKO Combat' ORDER BY bp.category
"""

Q_MARKET_SHARE = f"""
SELECT BRAND, COUNT(DISTINCT ITEM_ID) as product_count,
  ROUND(COUNT(DISTINCT ITEM_ID) * 100.0 / SUM(COUNT(DISTINCT ITEM_ID)) OVER(), 1) as share_pct
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:retailers IS NULL OR COMPANY_NAME IN (SELECT explode(split(:retailers, ','))))
  AND (:category IS NULL OR BENCHMARK_SUBCATG = :category)
GROUP BY BRAND ORDER BY product_count DESC
"""

Q_MARKET_SHARE_BY_RETAILER = f"""
SELECT COMPANY_NAME as retailer, BRAND, COUNT(DISTINCT ITEM_ID) as product_count,
  ROUND(COUNT(DISTINCT ITEM_ID) * 100.0 / SUM(COUNT(DISTINCT ITEM_ID)) OVER(PARTITION BY COMPANY_NAME), 1) as share_pct
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:brands IS NULL OR BRAND IN (SELECT explode(split(:brands, ','))))
GROUP BY COMPANY_NAME, BRAND ORDER BY COMPANY_NAME, share_pct DESC
"""

Q_MARKET_SHARE_TREND = f"""
SELECT PRICE_SCRAPE_DATE as date, BRAND, COUNT(DISTINCT ITEM_ID) as product_count
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
GROUP BY PRICE_SCRAPE_DATE, BRAND ORDER BY PRICE_SCRAPE_DATE, BRAND
"""

Q_BRAND_SCORECARD = f"""
SELECT BRAND, ROUND(AVG(ITEM_REVIEW_RATING), 2) as avg_rating,
  ROUND(SUM(ITEM_REVIEW_COUNT), 0) as total_reviews,
  ROUND(AVG(PRODUCT_PRICE), 2) as avg_price,
  ROUND(SUM(CASE WHEN AVAILABILITY_INDICATOR = 'IN_STOCK' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as availability_pct,
  COUNT(DISTINCT ITEM_ID) as product_count,
  COUNT(DISTINCT BENCHMARK_SUBCATG) as category_count,
  ROUND(AVG(ITEM_REVIEW_RATING) * 20 + SUM(CASE WHEN AVAILABILITY_INDICATOR = 'IN_STOCK' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) * 0.3 + COUNT(DISTINCT ITEM_ID) * 0.5, 1) as health_index
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:retailers IS NULL OR COMPANY_NAME IN (SELECT explode(split(:retailers, ','))))
GROUP BY BRAND ORDER BY health_index DESC
"""

Q_RATING_DISTRIBUTION = f"""
SELECT BRAND, FLOOR(ITEM_REVIEW_RATING) as rating_bucket, COUNT(*) as count
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:brands IS NULL OR BRAND IN (SELECT explode(split(:brands, ','))))
GROUP BY BRAND, FLOOR(ITEM_REVIEW_RATING) ORDER BY BRAND, rating_bucket
"""

Q_SERP_RANKINGS = f"""
SELECT domain_name, benchmark_dept as category,
  ROUND(AVG(position), 1) as avg_position,
  ROUND(AVG(search_engine_ranking), 2) as avg_ranking,
  COUNT(*) as appearances
FROM {SCHEMA}.us_serps_daily
GROUP BY domain_name, benchmark_dept ORDER BY avg_position
"""

Q_SERP_SOV = f"""
SELECT domain_name, COUNT(*) as total_appearances,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as share_of_voice
FROM {SCHEMA}.us_serps_daily WHERE position <= 10
GROUP BY domain_name ORDER BY total_appearances DESC
"""

Q_SERP_BY_KEYWORD = f"""
SELECT benchmark_dept as keyword_category, domain_name,
  ROUND(AVG(position), 1) as avg_position, COUNT(*) as appearances
FROM {SCHEMA}.us_serps_daily
GROUP BY benchmark_dept, domain_name ORDER BY benchmark_dept, avg_position
"""

Q_AVAIL_BY_BRAND = f"""
SELECT BRAND, AVAILABILITY_INDICATOR as status, COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(PARTITION BY BRAND), 1) as pct
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:retailers IS NULL OR COMPANY_NAME IN (SELECT explode(split(:retailers, ','))))
GROUP BY BRAND, AVAILABILITY_INDICATOR ORDER BY BRAND, status
"""

Q_AVAIL_TREND = f"""
SELECT PRICE_SCRAPE_DATE as date, BRAND,
  ROUND(SUM(CASE WHEN AVAILABILITY_INDICATOR = 'IN_STOCK' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as in_stock_pct
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:brands IS NULL OR BRAND IN (SELECT explode(split(:brands, ','))))
GROUP BY PRICE_SCRAPE_DATE, BRAND ORDER BY PRICE_SCRAPE_DATE, BRAND
"""

Q_AVAIL_BY_RETAILER = f"""
SELECT COMPANY_NAME as retailer, BRAND,
  ROUND(SUM(CASE WHEN AVAILABILITY_INDICATOR = 'IN_STOCK' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as in_stock_pct,
  ROUND(SUM(CASE WHEN AVAILABILITY_INDICATOR = 'OUT_OF_STOCK' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as oos_pct
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
GROUP BY COMPANY_NAME, BRAND ORDER BY COMPANY_NAME, BRAND
"""

Q_REVIEW_TRENDS = f"""
SELECT PRICE_SCRAPE_DATE as date, BRAND,
  ROUND(AVG(ITEM_REVIEW_RATING), 2) as avg_rating,
  ROUND(AVG(ITEM_REVIEW_COUNT), 0) as avg_review_count
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
  AND (:brands IS NULL OR BRAND IN (SELECT explode(split(:brands, ','))))
GROUP BY PRICE_SCRAPE_DATE, BRAND ORDER BY PRICE_SCRAPE_DATE, BRAND
"""

Q_SENTIMENT_COMPARISON = f"""
SELECT BRAND, ROUND(AVG(ITEM_REVIEW_RATING), 2) as avg_rating,
  ROUND(MAX(ITEM_REVIEW_COUNT), 0) as max_reviews,
  ROUND(AVG(ITEM_REVIEW_COUNT), 0) as avg_reviews,
  SUM(CASE WHEN ITEM_REVIEW_RATING >= 4.5 THEN 1 ELSE 0 END) as excellent_count,
  SUM(CASE WHEN ITEM_REVIEW_RATING >= 4.0 AND ITEM_REVIEW_RATING < 4.5 THEN 1 ELSE 0 END) as good_count,
  SUM(CASE WHEN ITEM_REVIEW_RATING >= 3.5 AND ITEM_REVIEW_RATING < 4.0 THEN 1 ELSE 0 END) as average_count,
  SUM(CASE WHEN ITEM_REVIEW_RATING < 3.5 THEN 1 ELSE 0 END) as below_avg_count
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
GROUP BY BRAND ORDER BY avg_rating DESC
"""

Q_SCENARIO_BASE = f"""
SELECT BRAND, BENCHMARK_SUBCATG as category,
  ROUND(AVG(PRODUCT_PRICE), 2) as avg_price,
  ROUND(AVG(ITEM_REVIEW_RATING), 2) as avg_rating,
  ROUND(SUM(CASE WHEN AVAILABILITY_INDICATOR = 'IN_STOCK' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as availability_pct,
  COUNT(DISTINCT ITEM_ID) as product_count
FROM {SCHEMA}.us_households_daily
WHERE PRICE_SCRAPE_DATE BETWEEN :start_date AND :end_date
GROUP BY BRAND, BENCHMARK_SUBCATG ORDER BY BRAND, category
"""

Q_FILTER_OPTIONS = f"""
SELECT 'brands' as filter_type, COLLECT_SET(BRAND) as options FROM {SCHEMA}.us_households_daily
UNION ALL
SELECT 'retailers', COLLECT_SET(COMPANY_NAME) FROM {SCHEMA}.us_households_daily
UNION ALL
SELECT 'categories', COLLECT_SET(BENCHMARK_SUBCATG) FROM {SCHEMA}.us_households_daily
"""

Q_DATE_RANGE = f"""
SELECT MIN(PRICE_SCRAPE_DATE) as min_date, MAX(PRICE_SCRAPE_DATE) as max_date
FROM {SCHEMA}.us_households_daily
"""


# ---- API Endpoints ----

@app.get("/api/filters")
def get_filters():
    date_range = execute_query(Q_DATE_RANGE)
    filter_opts = execute_query(Q_FILTER_OPTIONS)
    filters = {}
    for row in filter_opts:
        opts = row["options"]
        filters[row["filter_type"]] = opts if isinstance(opts, list) else json.loads(opts) if isinstance(opts, str) else []
    return {
        "date_range": serialize(date_range)[0] if date_range else {},
        "filters": filters
    }


@app.get("/api/dashboard/kpis")
def dashboard_kpis(start_date: str = "2025-01-01", end_date: str = "2025-03-01",
                   brands: Optional[str] = None, retailers: Optional[str] = None):
    return serialize(execute_query(Q_DASHBOARD_KPIS, {
        "start_date": start_date, "end_date": end_date, "brands": brands, "retailers": retailers}))

@app.get("/api/dashboard/trends")
def dashboard_trends(start_date: str = "2025-01-01", end_date: str = "2025-03-01",
                     brands: Optional[str] = None):
    return serialize(execute_query(Q_DASHBOARD_TRENDS, {
        "start_date": start_date, "end_date": end_date, "brands": brands}))

@app.get("/api/price/comparison")
def price_comparison(start_date: str = "2025-01-01", end_date: str = "2025-03-01",
                     brands: Optional[str] = None, retailers: Optional[str] = None):
    return serialize(execute_query(Q_PRICE_COMPARISON, {
        "start_date": start_date, "end_date": end_date, "brands": brands, "retailers": retailers}))

@app.get("/api/price/trends")
def price_trends(start_date: str = "2025-01-01", end_date: str = "2025-03-01",
                 brands: Optional[str] = None, category: Optional[str] = None):
    return serialize(execute_query(Q_PRICE_TRENDS, {
        "start_date": start_date, "end_date": end_date, "brands": brands, "category": category}))

@app.get("/api/price/gap")
def price_gap(start_date: str = "2025-01-01", end_date: str = "2025-03-01",
              retailers: Optional[str] = None):
    return serialize(execute_query(Q_PRICE_GAP, {
        "start_date": start_date, "end_date": end_date, "retailers": retailers}))

@app.get("/api/market/share")
def market_share(start_date: str = "2025-01-01", end_date: str = "2025-03-01",
                 retailers: Optional[str] = None, category: Optional[str] = None):
    return serialize(execute_query(Q_MARKET_SHARE, {
        "start_date": start_date, "end_date": end_date, "retailers": retailers, "category": category}))

@app.get("/api/market/share-by-retailer")
def market_share_by_retailer(start_date: str = "2025-01-01", end_date: str = "2025-03-01",
                             brands: Optional[str] = None):
    return serialize(execute_query(Q_MARKET_SHARE_BY_RETAILER, {
        "start_date": start_date, "end_date": end_date, "brands": brands}))

@app.get("/api/market/share-trend")
def market_share_trend(start_date: str = "2025-01-01", end_date: str = "2025-03-01"):
    return serialize(execute_query(Q_MARKET_SHARE_TREND, {
        "start_date": start_date, "end_date": end_date}))

@app.get("/api/brand/scorecard")
def brand_scorecard(start_date: str = "2025-01-01", end_date: str = "2025-03-01",
                    retailers: Optional[str] = None):
    return serialize(execute_query(Q_BRAND_SCORECARD, {
        "start_date": start_date, "end_date": end_date, "retailers": retailers}))

@app.get("/api/brand/rating-distribution")
def rating_distribution(start_date: str = "2025-01-01", end_date: str = "2025-03-01",
                        brands: Optional[str] = None):
    return serialize(execute_query(Q_RATING_DISTRIBUTION, {
        "start_date": start_date, "end_date": end_date, "brands": brands}))

@app.get("/api/serp/rankings")
def serp_rankings():
    return serialize(execute_query(Q_SERP_RANKINGS))

@app.get("/api/serp/share-of-voice")
def serp_share_of_voice():
    return serialize(execute_query(Q_SERP_SOV))

@app.get("/api/serp/by-keyword")
def serp_by_keyword():
    return serialize(execute_query(Q_SERP_BY_KEYWORD))

@app.get("/api/inventory/by-brand")
def inventory_by_brand(start_date: str = "2025-01-01", end_date: str = "2025-03-01",
                       retailers: Optional[str] = None):
    return serialize(execute_query(Q_AVAIL_BY_BRAND, {
        "start_date": start_date, "end_date": end_date, "retailers": retailers}))

@app.get("/api/inventory/trend")
def inventory_trend(start_date: str = "2025-01-01", end_date: str = "2025-03-01",
                    brands: Optional[str] = None):
    return serialize(execute_query(Q_AVAIL_TREND, {
        "start_date": start_date, "end_date": end_date, "brands": brands}))

@app.get("/api/inventory/by-retailer")
def inventory_by_retailer(start_date: str = "2025-01-01", end_date: str = "2025-03-01"):
    return serialize(execute_query(Q_AVAIL_BY_RETAILER, {
        "start_date": start_date, "end_date": end_date}))

@app.get("/api/sentiment/trends")
def sentiment_trends(start_date: str = "2025-01-01", end_date: str = "2025-03-01",
                     brands: Optional[str] = None):
    return serialize(execute_query(Q_REVIEW_TRENDS, {
        "start_date": start_date, "end_date": end_date, "brands": brands}))

@app.get("/api/sentiment/comparison")
def sentiment_comparison(start_date: str = "2025-01-01", end_date: str = "2025-03-01"):
    return serialize(execute_query(Q_SENTIMENT_COMPARISON, {
        "start_date": start_date, "end_date": end_date}))

@app.get("/api/scenario/base-data")
def scenario_base_data(start_date: str = "2025-01-01", end_date: str = "2025-03-01"):
    return serialize(execute_query(Q_SCENARIO_BASE, {
        "start_date": start_date, "end_date": end_date}))

@app.get("/api/scenario/simulate")
def scenario_simulate(price_change_pct: float = 0, rating_change: float = 0,
                      availability_change: float = 0, category: Optional[str] = None):
    price_elasticity = -1.8
    rating_impact = 12.0
    availability_impact = 0.5
    base_share = 16.7
    base_revenue = 125000

    share_delta = (
        price_change_pct * price_elasticity / 100 +
        rating_change * rating_impact +
        availability_change * availability_impact / 100
    )
    projected_share = max(0, min(100, base_share + share_delta))

    random.seed(42)
    simulations = []
    for _ in range(1000):
        noise = random.gauss(0, abs(share_delta) * 0.3 + 0.5)
        simulations.append(projected_share + noise)
    simulations.sort()

    revenue_multiplier = (1 + price_change_pct / 100) * (projected_share / base_share)
    projected_revenue = round(base_revenue * revenue_multiplier, 0)

    total_impact = abs(share_delta) if share_delta != 0 else 1
    return {
        "projected_share": round(projected_share, 2),
        "share_delta": round(share_delta, 2),
        "confidence_interval": [round(simulations[50], 2), round(simulations[949], 2)],
        "probability_above_15pct": round(sum(1 for s in simulations if s > 15) / 1000, 2),
        "projected_revenue": projected_revenue,
        "revenue_change_pct": round((revenue_multiplier - 1) * 100, 1),
        "lever_importance": {
            "price": round(abs(price_change_pct * price_elasticity / 100) / total_impact * 100, 0),
            "rating": round(abs(rating_change * rating_impact) / total_impact * 100, 0),
            "availability": round(abs(availability_change * availability_impact / 100) / total_impact * 100, 0)
        },
        "monte_carlo_histogram": [
            {"bucket": f"{i}-{i+1}", "count": sum(1 for s in simulations if i <= s < i+1)}
            for i in range(int(min(simulations)), int(max(simulations)) + 1)
        ]
    }


# Serve React frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend", "build")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")

    @app.get("/{path:path}")
    def serve_frontend(path: str = ""):
        file_path = os.path.join(frontend_dir, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dir, "index.html"))
