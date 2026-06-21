resource "google_storage_bucket" "kenya_inclusion_raw" {
  name          = "kenya-inclusion-raw"
  location      = "AFRICA-SOUTH1"
  force_destroy = false

  uniform_bucket_level_access = true

  soft_delete_policy {
    retention_duration_seconds = 604800
  }
}
