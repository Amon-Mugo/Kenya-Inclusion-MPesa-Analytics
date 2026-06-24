locals {
  ingestion_functions = {
    world-bank-ingest = {
      entry_point = "world_bank_entry"
      source_dir  = "../cloud_functions/world_bank_ingest"
    }
    finaccess-ingest = {
      entry_point = "finaccess_entry"
      source_dir  = "../cloud_functions/finaccess_ingest"
    }
    mpesa-ingest = {
      entry_point = "mpesa_entry"
      source_dir  = "../cloud_functions/mpesa_ingest"
    }
  }
}

data "archive_file" "function_source" {
  for_each = local.ingestion_functions

  type        = "zip"
  source_dir  = each.value.source_dir
  output_path = "/tmp/${each.key}.zip"
}

resource "google_storage_bucket_object" "function_source" {
  for_each = local.ingestion_functions

  name   = "cloud-functions-source/${each.key}-${data.archive_file.function_source[each.key].output_md5}.zip"
  bucket = "kenya-inclusion-raw"
  source = data.archive_file.function_source[each.key].output_path
}

resource "google_cloudfunctions2_function" "ingestion" {
  for_each = local.ingestion_functions

  name     = each.key
  location = "us-central1"

  build_config {
    runtime     = "python311"
    entry_point = each.value.entry_point

    source {
      storage_source {
        bucket = "kenya-inclusion-raw"
        object = google_storage_bucket_object.function_source[each.key].name
      }
    }
  }

  service_config {
    timeout_seconds       = 300
    service_account_email = google_service_account.dbt_runner.email
    environment_variables = {
      GCS_BUCKET_NAME = "kenya-inclusion-raw"
      GCP_PROJECT_ID  = var.project_id
    }
  }
}

# --- GCS -> BigQuery load functions -----------------------------------
#
# Event-driven replacement for the orphaned gcs/load_to_bigquery.py script.
# Each function is triggered by GCS object-finalize events on the whole
# kenya-inclusion-raw bucket (Eventarc's storage.googleapis.com provider
# has no native prefix filter — see hashicorp/terraform-provider-google
# issue #12021), so each entry point checks the object name and no-ops
# if it doesn't match its expected prefix.

locals {
  load_functions = {
    world-bank-load = {
      entry_point = "world_bank_load_entry"
      source_dir  = "../cloud_functions/world_bank_load"
    }
    mpesa-statistics-load = {
      entry_point = "mpesa_statistics_load_entry"
      source_dir  = "../cloud_functions/mpesa_statistics_load"
    }
    finaccess-load = {
      entry_point = "finaccess_load_entry"
      source_dir  = "../cloud_functions/finaccess_load"
    }
  }
}

data "archive_file" "load_function_source" {
  for_each = local.load_functions

  type        = "zip"
  source_dir  = each.value.source_dir
  output_path = "/tmp/${each.key}.zip"
}

resource "google_storage_bucket_object" "load_function_source" {
  for_each = local.load_functions

  name   = "cloud-functions-source/${each.key}-${data.archive_file.load_function_source[each.key].output_md5}.zip"
  bucket = "kenya-inclusion-raw"
  source = data.archive_file.load_function_source[each.key].output_path
}

# Required once per project before Eventarc can route GCS events: the GCS
# service agent needs permission to publish to the Pub/Sub topic Eventarc
# creates under the hood for storage triggers. Safe to declare even if
# already granted — idempotent.
data "google_storage_project_service_account" "gcs_account" {
}

resource "google_project_iam_member" "gcs_pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = data.google_storage_project_service_account.gcs_account.member
}

# The event_trigger's service_account_email (dbt-runner) needs this role to
# receive events from the Eventarc trigger — separate from run.invoker,
# which only covers invoking the underlying Cloud Run service once the
# event is already received.
resource "google_project_iam_member" "dbt_runner_eventarc_receiver" {
  project = var.project_id
  role    = "roles/eventarc.eventReceiver"
  member  = "serviceAccount:${google_service_account.dbt_runner.email}"
}

# dbt-runner has storage.objectCreator (write-only) from Week 3/4, but the
# BigQuery load jobs in the *_load functions need to read the GCS object
# contents — objectCreator does not include storage.objects.get. Scoped to
# this bucket specifically, not project-wide, since read access is the
# more sensitive grant to keep tight.
resource "google_storage_bucket_iam_member" "dbt_runner_bucket_object_viewer" {
  bucket = "kenya-inclusion-raw"
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.dbt_runner.email}"
}

resource "google_cloudfunctions2_function" "load" {
  for_each = local.load_functions

  name     = each.key
  location = "us-central1"

  build_config {
    runtime     = "python311"
    entry_point = each.value.entry_point
    source {
      storage_source {
        bucket = "kenya-inclusion-raw"
        object = google_storage_bucket_object.load_function_source[each.key].name
      }
    }
  }

  service_config {
    timeout_seconds       = 300
    service_account_email = google_service_account.dbt_runner.email
    environment_variables = {
      GCS_BUCKET_NAME = "kenya-inclusion-raw"
      GCP_PROJECT_ID  = var.project_id
      BQ_DATASET      = "kenya_inclusion_raw"
    }
  }

  event_trigger {
    trigger_region        = "africa-south1"
    event_type            = "google.cloud.storage.object.v1.finalized"
    retry_policy          = "RETRY_POLICY_RETRY"
    service_account_email = google_service_account.dbt_runner.email

    event_filters {
      attribute = "bucket"
      value     = "kenya-inclusion-raw"
    }
  }

  depends_on = [google_project_iam_member.gcs_pubsub_publisher, google_project_iam_member.dbt_runner_eventarc_receiver]
}

# dbt-runner needs run.invoker on the load functions' underlying Cloud Run
# services for Eventarc to be able to invoke them — same fix pattern as
# the ingestion functions in Week 4.
resource "google_cloud_run_v2_service_iam_member" "load_invoker" {
  for_each = local.load_functions

  project  = var.project_id
  location = "us-central1"
  name     = google_cloudfunctions2_function.load[each.key].name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.dbt_runner.email}"
}
