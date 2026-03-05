#!/usr/bin/env python3
"""
Generate mock brand data for TKO Combat brand analyzer.
Inserts data into catalog_01_9tu9cg.brand_analyzer tables via Databricks SQL API.
"""

import json
import subprocess
import random
import hashlib
from datetime import date, timedelta

PROFILE = "tko-buildcon"
WAREHOUSE_ID = "d75e71068b3fa181"
CATALOG_SCHEMA = "catalog_01_9tu9cg.brand_analyzer"

def run_sql(statement, timeout="50s"):
    """Execute SQL via Databricks API."""
    # Normalize whitespace for JSON serialization
    clean_stmt = " ".join(statement.split())
    payload = {
        "statement": clean_stmt,
        "warehouse_id": WAREHOUSE_ID,
        "format": "JSON_ARRAY",
        "wait_timeout": timeout
    }
    payload_json = json.dumps(payload)
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(payload_json)
        tmp_path = f.name
    try:
        result = subprocess.run(
            ["databricks", "api", "post", "/api/2.0/sql/statements/",
             f"--json=@{tmp_path}", f"--profile={PROFILE}"],
            capture_output=True, text=True
        )
    finally:
        os.unlink(tmp_path)
    stdout = result.stdout.strip()
    if not stdout:
        # Try without @file syntax
        result = subprocess.run(
            ["databricks", "api", "post", "/api/2.0/sql/statements/",
             f"--profile={PROFILE}"],
            input=payload_json,
            capture_output=True, text=True
        )
        stdout = result.stdout.strip()
    if not stdout:
        print(f"SQL ERROR: Empty response. stderr: {result.stderr[:500]}")
        return False
    resp = json.loads(stdout)
    state = resp.get("status", {}).get("state", "")
    if state != "SUCCEEDED":
        error = resp.get("status", {}).get("error", {}).get("message", "Unknown error")
        print(f"SQL ERROR: {error}")
        print(f"Statement: {clean_stmt[:200]}...")
        return False
    return True


def create_tables():
    """Create the two tables matching Nimble schema."""
    print("Creating us_households_daily table...")
    run_sql(f"""
        CREATE OR REPLACE TABLE {CATALOG_SCHEMA}.us_households_daily (
            ITEM_ID DECIMAL(38,0),
            PRICE_SCRAPE_DATE DATE,
            TAXONOMY STRING,
            PRODUCT_TITLE STRING,
            COMPANY_NAME STRING,
            PRODUCT_PRICE DOUBLE,
            BRAND STRING,
            AVAILABILITY_INDICATOR STRING,
            ITEM_REVIEW_RATING DOUBLE,
            ITEM_REVIEW_COUNT DOUBLE,
            MODEL STRING,
            THIRD_PARTY_MERCHANT_NAME STRING,
            SKU STRING,
            WEIGHTS_AND_DIMENSIONS STRING,
            ITEM_NAME STRING,
            BENCHMARK_STORE STRING,
            BENCHMARK_DEPT STRING,
            BENCHMARK_CATG STRING,
            BENCHMARK_CATG_ID DECIMAL(38,0),
            BENCHMARK_SUBCATG STRING,
            BENCHMARK_BRAND_NAME STRING,
            BENCHMARK_UPC_NUM STRING,
            BENCHMARK_ITEM_MDL_NUM STRING,
            BENCHMARK_ITEM_SUB_DESC STRING,
            BENCHMARK_AVLBL_IND BOOLEAN,
            BENCHMARK_COLOR_DESC STRING,
            BENCHMARK_ITEM_ATTRIBS STRING,
            BENCHMARK_BASE_PRICE DOUBLE,
            BENCHMARK_SITE_PRICE DOUBLE
        )
    """)

    print("Creating us_serps_daily table...")
    run_sql(f"""
        CREATE OR REPLACE TABLE {CATALOG_SCHEMA}.us_serps_daily (
            domain_name STRING,
            benchmark_dept STRING,
            search_engine_ranking DOUBLE,
            number_of_products BIGINT,
            position BIGINT,
            term_key BIGINT,
            item_id BIGINT,
            benchmark_site_price DOUBLE,
            search_engine STRING,
            country STRING,
            displayed_url STRING,
            entity_type STRING,
            snippet STRING,
            url STRING,
            product_title STRING
        )
    """)
    print("Tables created.")


# --- Product Catalog ---

BRANDS = {
    "TKO Combat": {"prefix": "TKO", "price_mult": 1.0},
    "Century Martial Arts": {"prefix": "CMA", "price_mult": 1.05},
    "Everlast": {"prefix": "EVL", "price_mult": 0.90},
    "Hayabusa": {"prefix": "HAY", "price_mult": 1.25},
    "Venum": {"prefix": "VNM", "price_mult": 1.15},
    "RDX Sports": {"prefix": "RDX", "price_mult": 0.85},
}

RETAILERS = ["Amazon", "Walmart", "Target"]

PRODUCTS = [
    # (name_template, category_path, subcatg, base_price, catg_id, model_suffix, weight, color)
    ("Pro Boxing Gloves 12oz", "Sports & Outdoors > Sports & Fitness > Martial Arts > Boxing > Boxing Gloves", "Boxing Gloves", 49.99, 1001, "BG12", "1.5 lbs", "BLACK"),
    ("Pro Boxing Gloves 16oz", "Sports & Outdoors > Sports & Fitness > Martial Arts > Boxing > Boxing Gloves", "Boxing Gloves", 54.99, 1001, "BG16", "2.0 lbs", "RED"),
    ("Training Boxing Gloves 14oz", "Sports & Outdoors > Sports & Fitness > Martial Arts > Boxing > Boxing Gloves", "Boxing Gloves", 39.99, 1001, "BGT14", "1.8 lbs", "BLUE"),
    ("MMA Sparring Gloves", "Sports & Outdoors > Sports & Fitness > Martial Arts > Mixed Martial Arts > MMA Gloves", "MMA Gloves", 44.99, 1002, "MMAG", "0.8 lbs", "BLACK"),
    ("MMA Grappling Gloves", "Sports & Outdoors > Sports & Fitness > Martial Arts > Mixed Martial Arts > MMA Gloves", "MMA Gloves", 34.99, 1002, "MMAGG", "0.6 lbs", "WHITE"),
    ("Heavy Punching Bag 70lb", "Sports & Outdoors > Sports & Fitness > Martial Arts > Boxing > Punching Bags", "Punching Bags", 129.99, 1003, "PB70", "70 lbs", "BLACK"),
    ("Free Standing Punching Bag", "Sports & Outdoors > Sports & Fitness > Martial Arts > Boxing > Punching Bags", "Punching Bags", 179.99, 1003, "PBFS", "85 lbs", "RED"),
    ("Speed Bag", "Sports & Outdoors > Sports & Fitness > Martial Arts > Boxing > Punching Bags", "Punching Bags", 29.99, 1003, "SB01", "2 lbs", "BLACK"),
    ("Headgear Pro", "Sports & Outdoors > Sports & Fitness > Martial Arts > Protective Gear > Headgear", "Protective Gear", 59.99, 1004, "HG01", "1.2 lbs", "BLACK"),
    ("Shin Guards", "Sports & Outdoors > Sports & Fitness > Martial Arts > Protective Gear > Shin Guards", "Protective Gear", 39.99, 1004, "SG01", "1.0 lbs", "BLACK"),
    ("Mouth Guard Pro", "Sports & Outdoors > Sports & Fitness > Martial Arts > Protective Gear > Mouth Guards", "Protective Gear", 14.99, 1004, "MG01", "0.1 lbs", "CLEAR"),
    ("Training Mat 4x8ft", "Sports & Outdoors > Sports & Fitness > Martial Arts > Training Equipment > Training Mats", "Training Mats", 89.99, 1005, "TM48", "15 lbs", "GREY"),
    ("Puzzle Mat 24sqft", "Sports & Outdoors > Sports & Fitness > Martial Arts > Training Equipment > Training Mats", "Training Mats", 49.99, 1005, "PM24", "8 lbs", "BLACK"),
    ("Hand Wraps 180in", "Sports & Outdoors > Sports & Fitness > Martial Arts > Boxing > Boxing Accessories", "Boxing Accessories", 12.99, 1006, "HW180", "0.3 lbs", "BLACK"),
    ("Jump Rope Speed", "Sports & Outdoors > Sports & Fitness > Exercise & Fitness > Jump Ropes", "Fitness Accessories", 19.99, 1007, "JR01", "0.5 lbs", "BLACK"),
    ("Focus Mitts Pair", "Sports & Outdoors > Sports & Fitness > Martial Arts > Boxing > Boxing Accessories", "Boxing Accessories", 34.99, 1006, "FM01", "1.0 lbs", "RED"),
    ("Rash Guard Long Sleeve", "Sports & Outdoors > Sports & Fitness > Martial Arts > Athletic Apparel", "Athletic Apparel", 39.99, 1008, "RGLS", "0.5 lbs", "BLACK"),
    ("Fight Shorts", "Sports & Outdoors > Sports & Fitness > Martial Arts > Athletic Apparel", "Athletic Apparel", 34.99, 1008, "FS01", "0.4 lbs", "BLACK"),
    ("Gym Bag Large", "Sports & Outdoors > Sports & Fitness > Exercise & Fitness > Gym Bags", "Fitness Accessories", 44.99, 1007, "GB01", "2.0 lbs", "BLACK"),
    ("Boxing Shoes Pro", "Sports & Outdoors > Sports & Fitness > Martial Arts > Boxing > Boxing Shoes", "Boxing Shoes", 79.99, 1009, "BS01", "1.5 lbs", "WHITE"),
    ("Resistance Bands Set", "Sports & Outdoors > Sports & Fitness > Exercise & Fitness > Resistance Bands", "Fitness Accessories", 24.99, 1007, "RB01", "1.0 lbs", "MULTI"),
    ("Ab Wheel Roller", "Sports & Outdoors > Sports & Fitness > Exercise & Fitness > Core Training", "Fitness Accessories", 19.99, 1007, "AW01", "2.5 lbs", "BLACK"),
    ("Kettlebell 35lb", "Sports & Outdoors > Sports & Fitness > Exercise & Fitness > Kettlebells", "Fitness Accessories", 54.99, 1007, "KB35", "35 lbs", "BLACK"),
    ("Thai Pads Pair", "Sports & Outdoors > Sports & Fitness > Martial Arts > Muay Thai > Thai Pads", "Muay Thai", 69.99, 1010, "TP01", "3.0 lbs", "RED"),
    ("Body Protector", "Sports & Outdoors > Sports & Fitness > Martial Arts > Protective Gear > Body Protectors", "Protective Gear", 79.99, 1004, "BP01", "3.5 lbs", "BLACK"),
]

def make_item_id(brand, product_idx, retailer):
    """Generate a deterministic item ID."""
    seed = f"{brand}-{product_idx}-{retailer}"
    h = int(hashlib.md5(seed.encode()).hexdigest()[:9], 16)
    return h % 9000000000 + 1000000000

def make_sku(prefix, model, retailer):
    r_code = {"Amazon": "AZ", "Walmart": "WM", "Target": "TG"}[retailer]
    return f"{prefix}-{model}-{r_code}"

def make_upc(brand_idx, product_idx):
    return f"0{880000000000 + brand_idx * 1000 + product_idx:012d}"

def escape_sql(s):
    return s.replace("'", "''").replace("\\", "\\\\")


def generate_households_data():
    """Generate ~150K+ rows of household daily data."""
    print("Generating us_households_daily data...")

    random.seed(42)  # deterministic

    start_date = date(2025, 1, 1)
    num_days = 60
    dates = [start_date + timedelta(days=i) for i in range(num_days)]

    all_rows = []
    brand_list = list(BRANDS.items())

    for brand_idx, (brand_name, brand_info) in enumerate(brand_list):
        prefix = brand_info["prefix"]
        price_mult = brand_info["price_mult"]

        # Each brand has a subset of products (some overlap, some unique)
        # TKO Combat gets all products; competitors get 15-20 each
        if brand_name == "TKO Combat":
            product_indices = list(range(len(PRODUCTS)))
        else:
            random.seed(42 + brand_idx)
            product_indices = sorted(random.sample(range(len(PRODUCTS)), random.randint(15, 20)))

        for prod_idx in product_indices:
            prod = PRODUCTS[prod_idx]
            prod_name_template, taxonomy, subcatg, base_price, catg_id, model_suffix, weight, color = prod

            product_title = f"{brand_name} {prod_name_template}"
            item_name = f"{prefix}-{model_suffix}"
            model_num = f"{prefix}{model_suffix}"
            adjusted_base = round(base_price * price_mult, 2)

            for retailer in RETAILERS:
                item_id = make_item_id(brand_name, prod_idx, retailer)
                sku = make_sku(prefix, model_suffix, retailer)
                upc = make_upc(brand_idx, prod_idx)

                # retailer-specific price adjustment
                retailer_adj = {"Amazon": 1.0, "Walmart": 0.97, "Target": 1.02}[retailer]
                retailer_base = round(adjusted_base * retailer_adj, 2)

                # Base rating for this product/brand combo
                random.seed(hash((brand_name, prod_idx, retailer)) % 2**31)
                base_rating = round(random.uniform(3.5, 4.9), 1)
                base_review_count = random.randint(50, 5000)

                for day_idx, d in enumerate(dates):
                    # Price fluctuation: ±5-15% with some trends
                    random.seed(hash((brand_name, prod_idx, retailer, str(d))) % 2**31)
                    price_noise = random.uniform(-0.08, 0.08)
                    # Add a trend component
                    trend = 0.001 * day_idx if brand_name in ["TKO Combat", "Hayabusa"] else -0.0005 * day_idx
                    current_price = round(retailer_base * (1 + price_noise + trend), 2)

                    # Availability
                    avail_roll = random.random()
                    if avail_roll < 0.85:
                        availability = "IN_STOCK"
                    elif avail_roll < 0.95:
                        availability = "LIMITED_STOCK"
                    else:
                        availability = "OUT_OF_STOCK"

                    # Rating: slight fluctuation
                    rating = round(min(5.0, max(1.0, base_rating + random.uniform(-0.2, 0.2))), 1)

                    # Review count: grows over time
                    review_count = base_review_count + day_idx * random.randint(0, 3)

                    benchmark_base_price = round(adjusted_base * 0.98, 2)
                    benchmark_site_price = round(current_price * random.uniform(0.95, 1.05), 2)
                    benchmark_avail = "true" if availability != "OUT_OF_STOCK" else "false"

                    merchant = f"{retailer}.com" if retailer == "Amazon" else retailer

                    row = (
                        f"{item_id}",
                        f"'{d.isoformat()}'",
                        f"'{escape_sql(taxonomy)}'",
                        f"'{escape_sql(product_title)}'",
                        f"'{retailer}'",
                        f"{current_price}",
                        f"'{escape_sql(brand_name)}'",
                        f"'{availability}'",
                        f"{rating}",
                        f"{review_count}.0",
                        f"'{model_num}'",
                        f"'{merchant}'",
                        f"'{sku}'",
                        f"'{weight}'",
                        f"'{escape_sql(item_name)}'",
                        "'Sports & Toys'",
                        "'Sports & Fitness'",
                        f"'{escape_sql(subcatg)}'",
                        f"{catg_id}",
                        f"'{escape_sql(subcatg)}'",
                        f"'{escape_sql(brand_name)}'",
                        f"'{upc}'",
                        f"'{model_num}'",
                        f"'{escape_sql(color)}'",
                        benchmark_avail,
                        f"'{color}'",
                        f"'material - synthetic leather, sport - martial arts'",
                        f"{benchmark_base_price}",
                        f"{benchmark_site_price}"
                    )
                    all_rows.append(row)

    print(f"Total rows to insert: {len(all_rows)}")

    # Insert in batches of 500
    batch_size = 500
    for i in range(0, len(all_rows), batch_size):
        batch = all_rows[i:i+batch_size]
        values = ", ".join([f"({', '.join(r)})" for r in batch])
        sql = f"INSERT INTO {CATALOG_SCHEMA}.us_households_daily VALUES {values}"
        success = run_sql(sql)
        pct = min(100, round((i + batch_size) / len(all_rows) * 100))
        print(f"  Inserted batch {i//batch_size + 1}/{(len(all_rows)-1)//batch_size + 1} ({pct}%)", "OK" if success else "FAILED")

    print("us_households_daily data generation complete.")


def generate_serps_data():
    """Generate SERP ranking data."""
    print("Generating us_serps_daily data...")

    random.seed(123)

    SEARCH_KEYWORDS = [
        ("boxing gloves", 2001, "Boxing Gloves"),
        ("mma gloves", 2002, "MMA Gloves"),
        ("punching bag", 2003, "Punching Bags"),
        ("martial arts equipment", 2004, "Martial Arts"),
        ("boxing headgear", 2005, "Protective Gear"),
        ("training mats martial arts", 2006, "Training Mats"),
        ("hand wraps boxing", 2007, "Boxing Accessories"),
        ("muay thai pads", 2008, "Muay Thai"),
        ("boxing shoes", 2009, "Boxing Shoes"),
        ("mma fight shorts", 2010, "Athletic Apparel"),
        ("shin guards martial arts", 2011, "Protective Gear"),
        ("speed bag boxing", 2012, "Punching Bags"),
        ("rash guard mma", 2013, "Athletic Apparel"),
        ("heavy bag stand", 2014, "Punching Bags"),
        ("kettlebell workout", 2015, "Fitness Accessories"),
    ]

    DOMAINS = {
        "TKO Combat": ["tkocombat.com", "amazon.com", "walmart.com", "target.com"],
        "Century Martial Arts": ["centurymartialarts.com", "amazon.com", "walmart.com"],
        "Everlast": ["everlast.com", "amazon.com", "walmart.com", "target.com"],
        "Hayabusa": ["hayabusafight.com", "amazon.com"],
        "Venum": ["venum.com", "amazon.com", "walmart.com"],
        "RDX Sports": ["rdxsports.com", "amazon.com", "walmart.com"],
    }

    all_rows = []
    brand_list = list(BRANDS.keys())

    for keyword, term_key, dept in SEARCH_KEYWORDS:
        for brand in brand_list:
            domains = DOMAINS[brand]
            for domain in domains:
                random.seed(hash((keyword, brand, domain)) % 2**31)

                # Generate position and ranking
                base_position = random.randint(1, 30)
                num_products = random.randint(1, 15)

                # Brand-specific ranking tendencies
                if brand == "TKO Combat" and "amazon.com" in domain:
                    base_position = random.randint(3, 12)
                elif brand == "Everlast":
                    base_position = random.randint(1, 8)
                elif brand == "Hayabusa":
                    base_position = random.randint(5, 15)

                item_id = make_item_id(brand, SEARCH_KEYWORDS.index((keyword, term_key, dept)), domain)
                price = round(random.uniform(15, 200), 2)
                ranking = round(random.uniform(5, 25), 6)

                snippet = f"Shop {brand} {keyword} - Premium quality martial arts gear. Free shipping on orders over $50."
                product_title_str = f"{brand} Premium {keyword.title()}"
                displayed_url_val = f"https://www.{domain} > {keyword.replace(' ', '-')}"
                url_val = f"https://www.{domain}/{keyword.replace(' ', '-')}"

                row = (
                    f"'{domain}'",
                    f"'{dept}'",
                    f"{ranking}",
                    f"{num_products}",
                    f"{base_position}",
                    f"{term_key}",
                    f"{item_id}",
                    f"{price}",
                    "'google_search'",
                    "'US'",
                    f"'{escape_sql(displayed_url_val)}'",
                    "'OrganicResult'",
                    f"'{escape_sql(snippet)}'",
                    f"'{escape_sql(url_val)}'",
                    f"'{escape_sql(product_title_str)}'"
                )
                all_rows.append(row)

    print(f"Total SERP rows to insert: {len(all_rows)}")

    batch_size = 500
    for i in range(0, len(all_rows), batch_size):
        batch = all_rows[i:i+batch_size]
        values = ", ".join([f"({', '.join(r)})" for r in batch])
        sql = f"INSERT INTO {CATALOG_SCHEMA}.us_serps_daily VALUES {values}"
        success = run_sql(sql)
        pct = min(100, round((i + batch_size) / len(all_rows) * 100))
        print(f"  Inserted batch {i//batch_size + 1}/{(len(all_rows)-1)//batch_size + 1} ({pct}%)", "OK" if success else "FAILED")

    print("us_serps_daily data generation complete.")


if __name__ == "__main__":
    print("=== TKO Combat Brand Analyzer - Mock Data Generation ===")
    create_tables()
    generate_households_data()
    generate_serps_data()
    print("=== Data generation complete! ===")
