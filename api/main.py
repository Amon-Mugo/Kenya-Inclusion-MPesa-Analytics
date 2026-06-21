
import os
import time
from typing import Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google.cloud import bigquery

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET = os.getenv("BIGQUERY_DATASET", "kenya_inclusion_raw")
CACHE_TTL_SECONDS = 60 * 60  # one hour

app = FastAPI(
    title="Kenya Financial Inclusion & M-Pesa Analytics API",
    description="Serves county financial inclusion and M-Pesa growth data from BigQuery.",
    version="1.0.0",
)

client = bigquery.Client(project=PROJECT_ID)

_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}


def run_query(query_key: str, query: str) -> list[dict[str, Any]]:
    """Run a BigQuery query, serving from cache when still fresh."""
    cached = _cache.get(query_key)
    if cached is not None:
        cached_at, rows = cached
        if time.time() - cached_at < CACHE_TTL_SECONDS:
            return rows

    rows = [dict(row.items()) for row in client.query(query).result()]
    _cache[query_key] = (time.time(), rows)
    return rows


@app.get("/")
def health_check() -> dict[str, str]:
    """Basic liveness check."""
    return {"status": "ok", "service": "kenya-inclusion-mpesa-api"}


@app.get("/county")
def get_all_counties() -> list[dict[str, Any]]:
    """Return financial inclusion metrics for all 47 counties."""
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET}.mart_county_financial_access`
        ORDER BY mobile_money_pct DESC
    """
    return run_query("all_counties", query)


@app.get("/county/{county_code}")
def get_county(county_code: int) -> dict[str, Any]:
    """Return financial inclusion metrics for a single county by code."""
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET}.mart_county_financial_access`
        WHERE county_code = @county_code
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("county_code", "INT64", county_code)]
    )
    rows = [dict(row.items()) for row in client.query(query, job_config=job_config).result()]

    if not rows:
        raise HTTPException(status_code=404, detail=f"County code {county_code} not found")

    return rows[0]


@app.get("/mpesa")
def get_mpesa_overview() -> list[dict[str, Any]]:
    """Return M-Pesa growth metrics for all available years."""
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET}.mart_mpesa_financial_overview`
        ORDER BY year
    """
    return run_query("mpesa_overview", query)


@app.get("/mpesa/{year}")
def get_mpesa_year(year: int) -> dict[str, Any]:
    """Return M-Pesa growth metrics for a single year."""
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET}.mart_mpesa_financial_overview`
        WHERE year = @year
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("year", "INT64", year)]
    )
    rows = [dict(row.items()) for row in client.query(query, job_config=job_config).result()]

    if not rows:
        raise HTTPException(status_code=404, detail=f"Year {year} not found")

    return rows[0]
