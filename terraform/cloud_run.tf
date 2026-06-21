resource "google_cloud_run_v2_job" "dbt_run" {
  name     = "dbt-run-kenya-inclusion"
  location = "us-central1"

  template {
    template {
      service_account = google_service_account.dbt_runner.email

      containers {
        image = "us-central1-docker.pkg.dev/${var.project_id}/kenya-inclusion-repo/dbt-runner:latest"
      }
    }
  }
}

resource "google_cloud_run_v2_service" "kenya_inclusion_api" {
  name     = "kenya-inclusion-api"
  location = "us-central1"

  template {
    service_account = google_service_account.dbt_runner.email

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    containers {
      image = "us-central1-docker.pkg.dev/${var.project_id}/kenya-inclusion-repo/kenya-inclusion-api:latest"

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "BIGQUERY_DATASET"
        value = "kenya_inclusion_raw"
      }
    }
  }
}

resource "google_cloud_run_v2_job_iam_member" "dbt_run_invoker" {
  name     = google_cloud_run_v2_job.dbt_run.name
  location = "us-central1"
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.dbt_runner.email}"
}
