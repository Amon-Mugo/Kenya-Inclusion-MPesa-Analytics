import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from google.cloud import bigquery, storage

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET = os.getenv("BQ_DATASET")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

client = bigquery.Client(project=PROJECT_ID)


def get_latest_gcs_file(folder):
    """Get the most recently uploaded file from a GCS folder."""
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = list(bucket.list_blobs(prefix=f"raw/{folder}/"))

    if not blobs:
        print(f"  No files found in raw/{folder}/")
        return None

    # Sort by time uploaded, get latest
    latest = sorted(blobs, key=lambda b: b.time_created, reverse=True)[0] # Get the most recently uploaded file
    print(f" Latest file: {latest.name}")
    return f"gs://{BUCKET_NAME}/{latest.name}"


def load_world_bank():
    """Load World Bank indicators into BigQuery."""
    print("\n[1] Loading World Bank indicators...")

    gcs_uri = get_latest_gcs_file("world_bank")#
    if not gcs_uri:
        return

    schema = [
        bigquery.SchemaField("indicator_code",  "STRING"),
        bigquery.SchemaField("indicator_name",  "STRING"),
        bigquery.SchemaField("country",         "STRING"),
        bigquery.SchemaField("country_code",    "STRING"),
        bigquery.SchemaField("year",            "INTEGER"),
        bigquery.SchemaField("value",           "FLOAT"),
        bigquery.SchemaField("ingested_at",     "TIMESTAMP"),
    ]

    table_id = f"{PROJECT_ID}.{DATASET}.raw_world_bank_indicators"

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    load_job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    load_job.result()

    table = client.get_table(table_id)
    print(f"  ✓ Loaded {table.num_rows} rows → {table_id}")


def load_mpesa_statistics():
    """Load M-Pesa historical statistics into BigQuery."""
    print("\n[2] Loading M-Pesa statistics...")

    # Get mpesa_statistics file specifically
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = list(bucket.list_blobs(prefix="raw/cbk/mpesa_statistics"))# List all files in the mpesa_statistics folder, then find the latest one

    if not blobs:
        print("No M-Pesa statistics file found")
        return

    latest = sorted(blobs, key=lambda b: b.time_created, reverse=True)[0]
    gcs_uri = f"gs://{BUCKET_NAME}/{latest.name}"
    print(f" Latest file: {latest.name}")

    schema = [
        bigquery.SchemaField("year",                    "INTEGER"),
        bigquery.SchemaField("month",                   "INTEGER"),
        bigquery.SchemaField("agents",                  "INTEGER"),
        bigquery.SchemaField("customers_millions",      "FLOAT"),
        bigquery.SchemaField("transactions_millions",   "FLOAT"),
        bigquery.SchemaField("value_ksh_billions",      "FLOAT"),
        bigquery.SchemaField("source",                  "STRING"),
        bigquery.SchemaField("country",                 "STRING"),
        bigquery.SchemaField("country_code",            "STRING"),
        bigquery.SchemaField("ingested_at",             "TIMESTAMP"),
    ]

    table_id = f"{PROJECT_ID}.{DATASET}.raw_mpesa_statistics"

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    load_job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    load_job.result()

    table = client.get_table(table_id)
    print(f"  ✓ Loaded {table.num_rows} rows → {table_id}")


def load_finaccess_county():
    """Load FinAccess county data into BigQuery."""
    print("\n[3] Loading FinAccess county data...")

    gcs_uri = get_latest_gcs_file("finaccess")
    if not gcs_uri:
        return

    schema = [
        bigquery.SchemaField("county",                 "STRING"),
        bigquery.SchemaField("county_code",            "INTEGER"),
        bigquery.SchemaField("formal_inclusion_pct",   "FLOAT"),
        bigquery.SchemaField("mobile_money_pct",       "FLOAT"),
        bigquery.SchemaField("bank_account_pct",       "FLOAT"),
        bigquery.SchemaField("excluded_pct",           "FLOAT"),
        bigquery.SchemaField("survey_year",            "INTEGER"),
        bigquery.SchemaField("source",                 "STRING"),
        bigquery.SchemaField("ingested_at",            "TIMESTAMP"),
    ]

    table_id = f"{PROJECT_ID}.{DATASET}.raw_finaccess_county"

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    load_job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    load_job.result()

    table = client.get_table(table_id)
    print(f"  ✓ Loaded {table.num_rows} rows → {table_id}")


def run():
    print("=" * 50)
    print("GCS → BigQuery Load Job")
    print(f"Dataset: {DATASET}")
    print("=" * 50)

    load_world_bank()
    load_mpesa_statistics()
    load_finaccess_county()

    print("\n All tables loaded into BigQuery!")
    print(f"\nVerify in BigQuery console:")
    print(f"https://console.cloud.google.com/bigquery?project={PROJECT_ID}")


if __name__ == "__main__":
    run()
