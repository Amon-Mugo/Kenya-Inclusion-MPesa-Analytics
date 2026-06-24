import functions_framework
import os
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET = os.getenv("BQ_DATASET")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

# Note: raw/cbk/ also contains mobile_money_indicators_*.json files (a World
# Bank fallback artifact, unrelated to this loader). The prefix below is
# deliberately specific to mpesa_statistics so those files are ignored.
EXPECTED_PREFIX = "raw/cbk/mpesa_statistics"

SCHEMA = [
    bigquery.SchemaField("year", "INTEGER"),
    bigquery.SchemaField("month", "INTEGER"),
    bigquery.SchemaField("agents", "INTEGER"),
    bigquery.SchemaField("customers_millions", "FLOAT"),
    bigquery.SchemaField("transactions_millions", "FLOAT"),
    bigquery.SchemaField("value_ksh_billions", "FLOAT"),
    bigquery.SchemaField("source", "STRING"),
    bigquery.SchemaField("country", "STRING"),
    bigquery.SchemaField("country_code", "STRING"),
    bigquery.SchemaField("ingested_at", "TIMESTAMP"),
]


def load_mpesa_statistics(object_name):
    """Load a single M-Pesa statistics file from GCS into BigQuery."""
    print(f"Loading M-Pesa statistics from gs://{BUCKET_NAME}/{object_name}")

    client = bigquery.Client(project=PROJECT_ID)
    gcs_uri = f"gs://{BUCKET_NAME}/{object_name}"
    table_id = f"{PROJECT_ID}.{DATASET}.raw_mpesa_statistics"

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
def mpesa_statistics_load_entry(cloud_event):
    """Eventarc entry point, fired on every finalized object in the bucket.

    Since the GCS trigger is bucket-wide (Eventarc's storage.googleapis.com
    provider has no native prefix filter), this no-ops for any object that
    isn't an M-Pesa statistics file — including the sibling
    mobile_money_indicators files that share the raw/cbk/ folder.
    """
    object_name = cloud_event.data["name"]

    if not object_name.startswith(EXPECTED_PREFIX):
        print(f"Ignoring {object_name} (not an M-Pesa statistics file)")
        return

    load_mpesa_statistics(object_name)
