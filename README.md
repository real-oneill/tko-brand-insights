# TKO Combat Brand Analyzer

Competitive intelligence platform for a martial arts equipment brand, built as a Databricks App. Compares TKO Combat's performance against 5 competitors (Century Martial Arts, Everlast, Hayabusa, Venum, RDX Sports) across Amazon, Walmart, and Target using Nimble marketplace data.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Databricks App                       │
│  ┌──────────────┐    ┌──────────────────────────────┐   │
│  │  React UI    │───▶│  FastAPI Backend (app.py)     │   │
│  │  (Recharts)  │    │  - 20+ API endpoints         │   │
│  │  8 views     │    │  - Scenario simulator         │   │
│  └──────────────┘    │    (Monte Carlo, elasticity)  │   │
│                      └──────────┬───────────────────┘   │
└─────────────────────────────────┼───────────────────────┘
                                  │ SQL via databricks-sql-connector
                                  ▼
                    ┌─────────────────────────────┐
                    │  Serverless SQL Warehouse    │
                    │  (d75e71068b3fa181)          │
                    └──────────┬──────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                                 ▼
┌──────────────────────────┐  ┌──────────────────────────────────┐
│ catalog_01_9tu9cg        │  │ Nimble Delta Share               │
│  .brand_analyzer         │  │  .nimble_rtl                     │
│  - us_households_daily   │  │  - us_households_daily           │
│  - us_serps_daily        │  │  - us_serps_daily                │
│  (mock TKO Combat data)  │  │  (real marketplace data)         │
└──────────────────────────┘  └──────────────────────────────────┘
```

## Databricks Services

| Service | Purpose |
|---------|---------|
| **Databricks Apps** | Hosts the FastAPI + React application with managed OAuth |
| **Serverless SQL Warehouse** | Executes analytical queries against Unity Catalog tables |
| **Unity Catalog** | Governs schema/table access and service principal permissions |
| **Delta Sharing** | Provides real-time Nimble marketplace data (pricing, reviews, SERP) |

## ML Components (Current)

The Scenario Planner runs in-process models that power interactive what-if analysis:

| Model | Method | Purpose |
|-------|--------|---------|
| **Price Elasticity** | Log-linear coefficients | Estimates market share shift from price changes (1% price drop ~ 1.8% share gain) |
| **Monte Carlo Simulation** | 1,000 random samples | Generates probability distributions and confidence intervals for projected outcomes |
| **Lever Importance** | Weighted attribution | Decomposes share impact across price, rating, and availability levers |

Users adjust sliders (price +-30%, rating +-1.0, availability +-20%) and see projected market share, revenue impact, P(share > 15%), and a Monte Carlo histogram — all computed on-the-fly.

## Next Phase: Model Serving for Real-Time Inference

The current in-process models will be replaced with three **Databricks Model Serving** endpoints, enabling scalable inference, model versioning, and A/B testing without redeploying the app.

### Planned Endpoints

| Endpoint | Model | Input | Output |
|----------|-------|-------|--------|
| `brand-analyzer-scenario` | Price Elasticity (log-linear) + Market Choice (multinomial logit) + Monte Carlo | `{"price_change_pct": -10, "brand": "TKO Combat", "category": "Boxing Gloves", "rating_change": 0.3}` | Projected share, confidence interval, revenue impact, lever importance |
| `brand-analyzer-forecast` | Prophet time series | `{"brand": "TKO Combat", "metric": "market_share", "horizon_days": 90}` | Forecast values with upper/lower confidence bounds |
| `brand-analyzer-anomaly` | Isolation Forest | `{"brand": "Everlast", "date": "2025-02-15"}` | Anomaly score and alert flag for competitor moves |

### Implementation Steps

1. **Train models** in a Databricks notebook using the combined brand_analyzer + Nimble data
   - Fit price elasticity (scikit-learn log-linear regression on daily brand share aggregations)
   - Fit market choice model (multinomial logit: `P(brand) = exp(V) / sum(exp(V))` where `V = B1*price + B2*rating + B3*availability + B4*search_rank`)
   - Fit Prophet forecasters per brand/metric for 30/60/90 day projections
   - Fit Isolation Forest on competitor price and availability time series for anomaly detection
2. **Log to MLflow** as custom pyfunc models wrapping the fitted coefficients and simulation logic
3. **Register** in the MLflow Model Registry under Unity Catalog
4. **Create Model Serving endpoints** via Databricks API pointing at registered model versions
5. **Update the FastAPI backend** to call endpoints via `databricks-sdk` instead of computing in-process — the backend becomes a thin proxy
6. **Add forecast overlays** to trend charts (dashed lines with shaded confidence bands)
7. **Add anomaly alerts** as badges on the Executive Dashboard when competitor behavior is flagged

### Architecture (Target State)

```
React UI ──▶ FastAPI ──┬──▶ SQL Warehouse (analytics queries)
                       │
                       ├──▶ Model Serving: brand-analyzer-scenario
                       │     (elasticity + choice + Monte Carlo)
                       │
                       ├──▶ Model Serving: brand-analyzer-forecast
                       │     (Prophet time series)
                       │
                       └──▶ Model Serving: brand-analyzer-anomaly
                             (Isolation Forest alerts)
```

This decouples ML inference from the app container — models can be retrained and endpoints updated without redeploying the app.

## Analytics Views

| View | What it shows |
|------|--------------|
| **Dashboard** | KPI cards, price trends, brand comparison table |
| **Price Intelligence** | Price by brand, price gap vs competitors, trend lines |
| **Market Share** | Share of shelf pie chart, share by retailer, trends |
| **Brand Performance** | Health index scorecards, radar chart, rating distribution |
| **Search Visibility** | SERP share of voice, position rankings, keyword analysis |
| **Inventory** | Availability by brand/retailer, in-stock rate trends |
| **Sentiment** | Rating trends, review growth, sentiment distribution |
| **Scenario Planner** | What-if simulator with Monte Carlo confidence intervals |

## Data

Mock data generated by `generate_mock_data.py`:
- **19,260 rows** in `us_households_daily` — 25 products x 6 brands x 3 retailers x ~60 days
- **285 rows** in `us_serps_daily` — 15 keywords x 6 brands across 9 domains

## Local Development

```bash
cd brand-analyzer-app/frontend
npm install && npm run build

cd ..
DATABRICKS_PROFILE=tko-buildcon uvicorn app:app --reload --port 8000
```

## Deployment

```bash
# Sync to workspace
databricks sync . /Users/<email>/brand-analyzer \
  --exclude node_modules --exclude .venv --exclude __pycache__ \
  --exclude "frontend/src" --exclude "frontend/public" \
  --full --profile=tko-buildcon

# Deploy
databricks apps deploy brand-analyzer \
  --source-code-path /Workspace/Users/<email>/brand-analyzer \
  --profile=tko-buildcon
```
