resource "google_service_account" "dbt_runner" {
  account_id   = "dbt-runner"
  display_name = "dbt Runner"
}

resource "google_project_iam_member" "dbt_runner_bigquery_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.dbt_runner.email}"
}

resource "google_project_iam_member" "dbt_runner_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.dbt_runner.email}"
}

resource "google_project_iam_member" "dbt_runner_storage_object_creator" {
  project = var.project_id
  role    = "roles/storage.objectCreator"
  member  = "serviceAccount:${google_service_account.dbt_runner.email}"
}

resource "google_cloud_run_v2_service_iam_member" "ingestion_invoker" {
  for_each = local.ingestion_functions
  project  = var.project_id
  location = "us-central1"
  name     = each.key
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.dbt_runner.email}"

  depends_on = [google_cloudfunctions2_function.ingestion]
}