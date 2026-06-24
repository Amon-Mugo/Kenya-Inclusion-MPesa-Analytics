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

  # NOTE: `terraform plan` will persistently show a diff removing
  # `scaling.manual_instance_count` and re-flagging `scaling.min_instance_count`.
  # This is a known limitation in google provider v6.50.0: GCP's Cloud Run Admin
  # API returns `manual_instance_count = 0` in every GetService response even
  # when `scaling_mode` is left at its default (AUTOMATIC), where the field is
  # inert. The provider has no schema attribute to set or ignore this field
  # directly (confirmed: `manual_instance_count` is rejected as an unsupported
  # argument in this resource, and `lifecycle.ignore_changes` on the `scaling`
  # block does not suppress it on subsequent plans).
  #
  # Effect: cosmetic only. No resource recreation, no downtime, no change to
  # actual service behavior. Safe to disregard.
  # Tracked upstream: https://github.com/hashicorp/terraform-provider-google/issues/20368
}

resource "google_cloud_run_v2_job_iam_member" "dbt_run_invoker" {
  name     = google_cloud_run_v2_job.dbt_run.name
  location = "us-central1"
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.dbt_runner.email}"
}