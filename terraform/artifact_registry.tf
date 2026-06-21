resource "google_artifact_registry_repository" "kenya_inclusion_repo" {
  repository_id = "kenya-inclusion-repo"
  location      = "us-central1"
  format        = "DOCKER"
  description   = "Docker images for Kenya Inclusion & M-Pesa Analytics"
}
