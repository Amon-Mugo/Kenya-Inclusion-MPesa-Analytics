import functions_framework
import os
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET = os.getenv("BQ_DATASET")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

EXPECTED_PREFIX = "raw/world_bank/"

SCHEMA = [
    bigquery.SchemaField("indicator_code", "STRING"),
    bigquery.SchemaField("indicator_name", "STRING"),
    bigquery.SchemaField("country", "STRING"),
    bigquery.SchemaField("country_code", "STRING"),
    bigquery.SchemaField("year", "INTEGER"),
    bigquery.SchemaField("value", "FLOAT"),
    bigquery.SchemaField("ingested_at", "TIMESTAMP"),
]


def load_world_bank(object_name):
    """Load a single World Bank indicators file from GCS into BigQuery."""
    print(f"Loading World Bank indicators from gs://{BUCKET_NAME}/{object_name}")

    client = bigquery.Client(project=PROJECT_ID)
    gcs_uri = f"gs://{BUCKET_NAME}/{object_name}"
    table_id = f"{PROJECT_ID}.{DATASET}.raw_world_bank_indicators"

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
def world_bank_load_entry(cloud_event):
    """Eventarc entry point, fired on every finalized object in the bucket.

    Since the GCS trigger is bucket-wide (Eventarc's storage.googleapis.com
    provider has no native prefix filter), this no-ops for any object that
    isn't a World Bank ingestion file.
    """
    object_name = cloud_event.data["name"]

    if not object_name.startswith(EXPECTED_PREFIX):
        print(f"Ignoring {object_name} (not a World Bank file)")
        return

    load_world_bank(object_name)
