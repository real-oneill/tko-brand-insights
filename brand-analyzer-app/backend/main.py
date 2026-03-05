"""FastAPI backend for Brand Analyzer Databricks App."""

import os
import json
import math
import random
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from databricks.sdk import WorkspaceClient
from databricks import sql as dbsql

from . import queries

app = FastAPI(title="TKO Combat Brand Analyzer")

WAREHOUSE_ID = os.environ.get("WAREHOUSE_ID", "d75e71068b3fa181")


def get_connection():
    w = WorkspaceClient()
    return dbsql.connect(
        server_hostname=w.config.host.replace("https://", ""),
        http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
        credentials_provider=lambda: w.config.authenticate,
    )


def execute_query(sql: str, params: dict = None) -> list[dict]:
    """Execute a SQL query and return results as list of dicts."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Replace named params with values
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
    """Make data JSON-serializable."""
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


# ---- API Endpoints ----

@app.get("/api/filters")
def get_filters():
    date_range = execute_query(queries.DATE_RANGE)
    filter_opts = execute_query(queries.FILTER_OPTIONS)
    filters = {}
    for row in filter_opts:
        filters[row["filter_type"]] = row["options"] if isinstance(row["options"], list) else json.loads(row["options"]) if isinstance(row["options"], str) else []
    return {
        "date_range": serialize(date_range)[0] if date_range else {},
        "filters": filters
    }


@app.get("/api/dashboard/kpis")
def dashboard_kpis(
    start_date: str = "2025-01-01",
    end_date: str = "2025-03-01",
    brands: Optional[str] = None,
    retailers: Optional[str] = None
):
    data = execute_query(queries.DASHBOARD_KPIS, {
        "start_date": start_date, "end_date": end_date,
        "brands": brands, "retailers": retailers
    })
    return serialize(data)


@app.get("/api/dashboard/trends")
def dashboard_trends(
    start_date: str = "2025-01-01",
    end_date: str = "2025-03-01",
    brands: Optional[str] = None
):
    data = execute_query(queries.DASHBOARD_TRENDS, {
        "start_date": start_date, "end_date": end_date, "brands": brands
    })
    return serialize(data)


@app.get("/api/price/comparison")
def price_comparison(
    start_date: str = "2025-01-01",
    end_date: str = "2025-03-01",
    brands: Optional[str] = None,
    retailers: Optional[str] = None
):
    data = execute_query(queries.PRICE_COMPARISON, {
        "start_date": start_date, "end_date": end_date,
        "brands": brands, "retailers": retailers
    })
    return serialize(data)


@app.get("/api/price/trends")
def price_trends(
    start_date: str = "2025-01-01",
    end_date: str = "2025-03-01",
    brands: Optional[str] = None,
    category: Optional[str] = None
):
    data = execute_query(queries.PRICE_TRENDS, {
        "start_date": start_date, "end_date": end_date,
        "brands": brands, "category": category
    })
    return serialize(data)


@app.get("/api/price/gap")
def price_gap(
    start_date: str = "2025-01-01",
    end_date: str = "2025-03-01",
    retailers: Optional[str] = None
):
    data = execute_query(queries.PRICE_GAP, {
        "start_date": start_date, "end_date": end_date, "retailers": retailers
    })
    return serialize(data)


@app.get("/api/market/share")
def market_share(
    start_date: str = "2025-01-01",
    end_date: str = "2025-03-01",
    retailers: Optional[str] = None,
    category: Optional[str] = None
):
    data = execute_query(queries.MARKET_SHARE, {
        "start_date": start_date, "end_date": end_date,
        "retailers": retailers, "category": category
    })
    return serialize(data)


@app.get("/api/market/share-by-retailer")
def market_share_by_retailer(
    start_date: str = "2025-01-01",
    end_date: str = "2025-03-01",
    brands: Optional[str] = None
):
    data = execute_query(queries.MARKET_SHARE_BY_RETAILER, {
        "start_date": start_date, "end_date": end_date, "brands": brands
    })
    return serialize(data)


@app.get("/api/market/share-trend")
def market_share_trend(
    start_date: str = "2025-01-01",
    end_date: str = "2025-03-01"
):
    data = execute_query(queries.MARKET_SHARE_TREND, {
        "start_date": start_date, "end_date": end_date
    })
    return serialize(data)


@app.get("/api/brand/scorecard")
def brand_scorecard(
    start_date: str = "2025-01-01",
    end_date: str = "2025-03-01",
    retailers: Optional[str] = None
):
    data = execute_query(queries.BRAND_SCORECARD, {
        "start_date": start_date, "end_date": end_date, "retailers": retailers
    })
    return serialize(data)


@app.get("/api/brand/rating-distribution")
def rating_distribution(
    start_date: str = "2025-01-01",
    end_date: str = "2025-03-01",
    brands: Optional[str] = None
):
    data = execute_query(queries.RATING_DISTRIBUTION, {
        "start_date": start_date, "end_date": end_date, "brands": brands
    })
    return serialize(data)


@app.get("/api/serp/rankings")
def serp_rankings():
    data = execute_query(queries.SERP_RANKINGS)
    return serialize(data)


@app.get("/api/serp/share-of-voice")
def serp_share_of_voice():
    data = execute_query(queries.SERP_SHARE_OF_VOICE)
    return serialize(data)


@app.get("/api/serp/by-keyword")
def serp_by_keyword():
    data = execute_query(queries.SERP_BY_KEYWORD)
    return serialize(data)


@app.get("/api/inventory/by-brand")
def inventory_by_brand(
    start_date: str = "2025-01-01",
    end_date: str = "2025-03-01",
    retailers: Optional[str] = None
):
    data = execute_query(queries.AVAILABILITY_BY_BRAND, {
        "start_date": start_date, "end_date": end_date, "retailers": retailers
    })
    return serialize(data)


@app.get("/api/inventory/trend")
def inventory_trend(
    start_date: str = "2025-01-01",
    end_date: str = "2025-03-01",
    brands: Optional[str] = None
):
    data = execute_query(queries.AVAILABILITY_TREND, {
        "start_date": start_date, "end_date": end_date, "brands": brands
    })
    return serialize(data)


@app.get("/api/inventory/by-retailer")
def inventory_by_retailer(
    start_date: str = "2025-01-01",
    end_date: str = "2025-03-01"
):
    data = execute_query(queries.AVAILABILITY_BY_RETAILER, {
        "start_date": start_date, "end_date": end_date
    })
    return serialize(data)


@app.get("/api/sentiment/trends")
def sentiment_trends(
    start_date: str = "2025-01-01",
    end_date: str = "2025-03-01",
    brands: Optional[str] = None
):
    data = execute_query(queries.REVIEW_TRENDS, {
        "start_date": start_date, "end_date": end_date, "brands": brands
    })
    return serialize(data)


@app.get("/api/sentiment/comparison")
def sentiment_comparison(
    start_date: str = "2025-01-01",
    end_date: str = "2025-03-01"
):
    data = execute_query(queries.SENTIMENT_COMPARISON, {
        "start_date": start_date, "end_date": end_date
    })
    return serialize(data)


@app.get("/api/scenario/base-data")
def scenario_base_data(
    start_date: str = "2025-01-01",
    end_date: str = "2025-03-01"
):
    data = execute_query(queries.SCENARIO_BASE_DATA, {
        "start_date": start_date, "end_date": end_date
    })
    return serialize(data)


@app.get("/api/scenario/simulate")
def scenario_simulate(
    price_change_pct: float = 0,
    rating_change: float = 0,
    availability_change: float = 0,
    category: Optional[str] = None
):
    """Simple scenario simulation using elasticity coefficients.
    In production this would call a Model Serving endpoint."""
    # Elasticity coefficients (simplified model)
    price_elasticity = -1.8  # 1% price drop -> 1.8% share gain
    rating_impact = 12.0     # 0.1 rating improvement -> 1.2% share gain
    availability_impact = 0.5  # 1% availability gain -> 0.5% share gain

    base_share = 16.7  # ~1/6 of market
    base_revenue = 125000

    share_delta = (
        price_change_pct * price_elasticity / 100 +
        rating_change * rating_impact +
        availability_change * availability_impact / 100
    )
    projected_share = max(0, min(100, base_share + share_delta))

    # Monte Carlo simulation (simplified)
    random.seed(42)
    simulations = []
    for _ in range(1000):
        noise = random.gauss(0, abs(share_delta) * 0.3 + 0.5)
        simulations.append(projected_share + noise)
    simulations.sort()

    revenue_multiplier = (1 + price_change_pct / 100) * (projected_share / base_share)
    projected_revenue = round(base_revenue * revenue_multiplier, 0)

    return {
        "projected_share": round(projected_share, 2),
        "share_delta": round(share_delta, 2),
        "confidence_interval": [round(simulations[50], 2), round(simulations[949], 2)],
        "probability_above_15pct": round(sum(1 for s in simulations if s > 15) / 1000, 2),
        "projected_revenue": projected_revenue,
        "revenue_change_pct": round((revenue_multiplier - 1) * 100, 1),
        "lever_importance": {
            "price": round(abs(price_change_pct * price_elasticity / 100) / max(0.01, abs(share_delta)) * 100, 0) if share_delta != 0 else 33,
            "rating": round(abs(rating_change * rating_impact) / max(0.01, abs(share_delta)) * 100, 0) if share_delta != 0 else 33,
            "availability": round(abs(availability_change * availability_impact / 100) / max(0.01, abs(share_delta)) * 100, 0) if share_delta != 0 else 34
        },
        "monte_carlo_histogram": [
            {"bucket": f"{i}-{i+1}", "count": sum(1 for s in simulations if i <= s < i+1)}
            for i in range(int(min(simulations)), int(max(simulations)) + 1)
        ]
    }


# Serve React static files
static_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "build")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(static_dir, "static")), name="static")

    @app.get("/{path:path}")
    def serve_frontend(path: str = ""):
        file_path = os.path.join(static_dir, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))
