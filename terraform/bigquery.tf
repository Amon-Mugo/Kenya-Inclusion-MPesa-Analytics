resource "google_bigquery_dataset" "kenya_inclusion_raw" {
  dataset_id  = "kenya_inclusion_raw"
  location    = "us-central1"
  description = "Kenya Financial Inclusion raw data"
}
