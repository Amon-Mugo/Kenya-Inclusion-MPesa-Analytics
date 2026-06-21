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
    timeout_seconds        = 300
    service_account_email  = google_service_account.dbt_runner.email
    environment_variables = {
      GCS_BUCKET_NAME = "kenya-inclusion-raw"
      GCP_PROJECT_ID  = var.project_id
    }
  }
}
