# Kenya Financial Inclusion & M-Pesa Analytics

An end-to-end GCP data pipeline analyzing financial inclusion across Kenya's 47 counties and the growth of M-Pesa mobile money over a decade. Built as a portfolio project to demonstrate production-style data engineering: event-driven ingestion, dbt transformations, infrastructure as code, and a REST API — all running on Google Cloud.

## What this project does

Three independent data sources are ingested, loaded, transformed, and served:

| Source | Description |
|---|---|
| **World Bank Indicators** | Annual development statistics for Kenya (account ownership, bank branches, ATMs per capita), 2010–2024 |
| **M-Pesa Statistics** | Yearly mobile money usage and growth metrics (agents, customers, transaction volume/value), 2015–2024 |
| **FinAccess County Survey** | County-level financial inclusion metrics for all 47 Kenyan counties, 2024 FinAccess Household Survey |

The pipeline ingests raw data to Cloud Storage, loads it into BigQuery, transforms it with dbt into analysis-ready marts, and serves it through a REST API and a Looker Studio dashboard.

## Architecture

```
                    ┌─────────────────┐
                    │  Data Sources   │
                    │ World Bank API  │
                    │ M-Pesa (static) │
                    │ FinAccess (static) │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Cloud Functions │  ◄── Ingestion (3 functions)
                    │   (ingest)      │
                    └────────┬────────┘
                             │ writes NDJSON
                    ┌────────▼────────┐
                    │  GCS Bucket     │  kenya-inclusion-raw
                    │ (AFRICA-SOUTH1) │  (Eventarc finalize trigger)
                    └────────┬────────┘
                             │ triggers
                    ┌────────▼────────┐
                    │ Cloud Functions │  ◄── Loading (3 functions, gen2)
                    │    (load)       │      Eventarc-triggered, prefix-routed
                    └────────┬────────┘
                             │ WRITE_TRUNCATE
                    ┌────────▼────────┐
                    │   BigQuery      │  kenya_inclusion_raw (raw tables)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │      dbt        │  staging → intermediate → marts
                    │  (Cloud Run Job)│
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
     ┌────────▼────────┐          ┌─────────▼─────────┐
     │    FastAPI       │          │  Looker Studio     │
     │  (Cloud Run)      │          │   Dashboard         │
     └───────────────────┘          └─────────────────────┘
```

All infrastructure is provisioned via Terraform.

## Why event-driven ingestion

The pipeline was originally designed around a daily cron schedule (Cloud Scheduler → Cloud Functions). It was rebuilt to be event-driven: each ingestion function writes a file to GCS, which fires an Eventarc trigger that immediately runs the matching load function. This removes the lag between data landing and data being queryable, and removed a standalone, manually-run loading script that had let raw tables go stale for over a week without anyone noticing.

Each load function is triggered by a single bucket-wide GCS finalize event (Eventarc's `storage.googleapis.com` provider has no native prefix filter), and performs its own prefix check to ignore files belonging to the other two sources.

## Tech stack

- **Ingestion / Loading:** Python, Cloud Functions (gen2), Eventarc
- **Storage:** Google Cloud Storage, BigQuery
- **Transformation:** dbt (BigQuery adapter)
- **Orchestration:** Cloud Run Job (dbt), Cloud Scheduler
- **API:** FastAPI, deployed as a Cloud Run service
- **Dashboard:** Looker Studio
- **Infrastructure:** Terraform
- **CI/Build:** Cloud Build, Artifact Registry

## Repository structure

```
.
├── cloud_functions/
│   ├── world_bank_ingest/      # Pulls World Bank API data, writes to GCS
│   ├── mpesa_ingest/           # Writes static M-Pesa statistics to GCS
│   ├── finaccess_ingest/       # Writes static FinAccess county data to GCS
│   ├── world_bank_load/        # Eventarc-triggered: loads World Bank data to BigQuery
│   ├── mpesa_statistics_load/  # Eventarc-triggered: loads M-Pesa data to BigQuery
│   └── finaccess_load/         # Eventarc-triggered: loads FinAccess data to BigQuery
├── dbt/kenya_inclusion/
│   └── models/
│       ├── staging/            # 1:1 cleaned views over raw BigQuery tables
│       ├── intermediate/       # Joined/pivoted World Bank + M-Pesa data
│       └── marts/              # Analysis-ready tables + dbt tests (schema.yml)
├── api/
│   └── main.py                 # FastAPI service: /county, /county/{code}, /mpesa, /mpesa/{year}
└── terraform/
    ├── main.tf, variables.tf
    ├── storage.tf               # GCS bucket
    ├── bigquery.tf              # Dataset
    ├── cloud_functions.tf       # All 6 Cloud Functions + Eventarc triggers + IAM
    ├── cloud_run.tf             # API service + dbt job
    ├── artifact_registry.tf
    ├── iam.tf
    └── scheduler.tf
```

## API endpoints

Deployed at Cloud Run (`us-central1`):

| Endpoint | Description |
|---|---|
| `GET /county` | All 47 counties, ranked by mobile money adoption |
| `GET /county/{county_code}` | Single county by code |
| `GET /mpesa` | M-Pesa metrics for all years (2015–2024) |
| `GET /mpesa/{year}` | M-Pesa metrics for a single year |

Responses are cached in-memory for one hour per query to reduce BigQuery costs on repeated requests.

## Data quality

dbt tests guard the two mart models against the failure modes that actually occurred during development:

- `unique` + `not_null` on `county_code` (`mart_county_financial_access`)
- `not_null` on `county` and `formal_inclusion_pct`
- `unique` + `not_null` on `year` (`mart_mpesa_financial_overview`)
- `not_null` on `customers_millions`

Run with:

```bash
cd dbt/kenya_inclusion
dbt test
```

There is no automated test suite for the Cloud Functions or the FastAPI service — verification during development was manual, via Cloud Logging and direct BigQuery/API queries. A natural next step would be `pytest` coverage for the API endpoints.

## Notable engineering decisions and bugs fixed

This project surfaced a few real infrastructure and data bugs worth documenting, since debugging them was as much a part of the learning as building the pipeline:

- **Silent struct-nesting from CTE name collisions.** Naming a CTE the same as a column in the underlying table (e.g. a CTE called `source` alongside a `source` column) causes BigQuery to silently nest the entire CTE as a STRUCT rather than raising an error. Fix: always name CTEs distinctly (`base`, `staged`), never reuse a column name.
- **Region mismatch in Eventarc triggers.** A Cloud Function's `trigger_region` must match the *bucket's* region, not the function's own execution region — these are independent settings, and mismatching them causes triggers to silently never fire.
- **Incomplete IAM for Eventarc.** The trigger's service account needs `roles/eventarc.eventReceiver` at the project level, separate from `roles/run.invoker` on the underlying Cloud Run service. Missing either one causes silent failures with no obvious error pointing at IAM.
- **Read vs. write permission gap.** A service account with `roles/storage.objectCreator` can write to GCS but cannot read back — BigQuery load jobs need `roles/storage.objectViewer` as well, granted at the bucket level to keep read access scoped tightly.
- **A column silently dropped from a mart.** A `CASE` expression referenced `formal_inclusion_pct` to compute a derived column, but the underlying raw column was never included in the model's final `select` list. BigQuery doesn't complain about this — it only surfaced when a `not_null` dbt test failed with "Unrecognized name," which is the reason this project now has dbt tests on both marts.

## Status

Pipeline is live and verified end-to-end: ingestion → event-driven loading → dbt transforms → API, with all infrastructure managed in Terraform. Built as a learning project targeting Kenya's fintech/banking data engineering market, with BigQuery chosen as the entry point into a broader cloud/big data roadmap (GCP → Spark → Snowflake → Kafka).
