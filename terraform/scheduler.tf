resource "google_cloud_scheduler_job" "dbt_run_daily" {
  name      = "dbt-run-kenya-inclusion-daily"
  region    = "us-central1"
  schedule  = "0 10 * * *"
  time_zone = "Africa/Nairobi"

  http_target {
    uri         = "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/dbt-run-kenya-inclusion:run"
    http_method = "POST"

    oauth_token {
      service_account_email = google_service_account.dbt_runner.email
    }
  }
}

resource "google_cloud_scheduler_job" "world_bank_ingest_daily" {
  name      = "world-bank-ingest-daily"
  region    = "us-central1"
  schedule  = "0 8 * * *"
  time_zone = "Africa/Nairobi"

  http_target {
    uri         = google_cloudfunctions2_function.ingestion["world-bank-ingest"].url
    http_method = "POST"

    oidc_token {
      service_account_email = google_service_account.dbt_runner.email
      audience              = google_cloudfunctions2_function.ingestion["world-bank-ingest"].url
    }
  }
}

resource "google_cloud_scheduler_job" "finaccess_ingest_daily" {
  name      = "finaccess-ingest-daily"
  region    = "us-central1"
  schedule  = "5 8 * * *"
  time_zone = "Africa/Nairobi"

  http_target {
    uri         = google_cloudfunctions2_function.ingestion["finaccess-ingest"].url
    http_method = "POST"

    oidc_token {
      service_account_email = google_service_account.dbt_runner.email
      audience              = google_cloudfunctions2_function.ingestion["finaccess-ingest"].url
    }
  }
}

resource "google_cloud_scheduler_job" "mpesa_ingest_daily" {
  name      = "mpesa-ingest-daily"
  region    = "us-central1"
  schedule  = "10 8 * * *"
  time_zone = "Africa/Nairobi"

  http_target {
    uri         = google_cloudfunctions2_function.ingestion["mpesa-ingest"].url
    http_method = "POST"

    oidc_token {
      service_account_email = google_service_account.dbt_runner.email
      audience              = google_cloudfunctions2_function.ingestion["mpesa-ingest"].url
    }
  }
}
