import functions_framework
import os
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET = os.getenv("BQ_DATASET")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

EXPECTED_PREFIX = "raw/finaccess/"

SCHEMA = [
    bigquery.SchemaField("county", "STRING"),
    bigquery.SchemaField("county_code", "INTEGER"),
    bigquery.SchemaField("formal_inclusion_pct", "FLOAT"),
    bigquery.SchemaField("mobile_money_pct", "FLOAT"),
    bigquery.SchemaField("bank_account_pct", "FLOAT"),
    bigquery.SchemaField("excluded_pct", "FLOAT"),
    bigquery.SchemaField("survey_year", "INTEGER"),
    bigquery.SchemaField("source", "STRING"),
    bigquery.SchemaField("ingested_at", "TIMESTAMP"),
]


def load_finaccess_county(object_name):
    """Load a single FinAccess county file from GCS into BigQuery."""
    print(f"Loading FinAccess county data from gs://{BUCKET_NAME}/{object_name}")

    client = bigquery.Client(project=PROJECT_ID)
    gcs_uri = f"gs://{BUCKET_NAME}/{object_name}"
    table_id = f"{PROJECT_ID}.{DATASET}.raw_finaccess_county"

    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    load_job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    load_job.result()  # Raises on failure — lets Eventarc's retry policy take over.

    table = client.get_table(table_id)
    print(f"  Loaded {table.num_rows} rows -> {table_id}")


@functions_framework.cloud_event
def finaccess_load_entry(cloud_event):
    """Eventarc entry point, fired on every finalized object in the bucket.

    Since the GCS trigger is bucket-wide (Eventarc's storage.googleapis.com
    provider has no native prefix filter), this no-ops for any object that
    isn't a FinAccess county file.
    """
    object_name = cloud_event.data["name"]

    if not object_name.startswith(EXPECTED_PREFIX):
        print(f"Ignoring {object_name} (not a FinAccess file)")
        return

    load_finaccess_county(object_name)
