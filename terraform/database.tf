# database.tf

resource "kubernetes_secret" "db_secret" {
  metadata {
    name      = "db-secret"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
  }
  data = {
    POSTGRES_USER     = "dev_user"
    POSTGRES_PASSWORD = "dev_password"
    POSTGRES_DB       = "realestate_db"
  }
  type = "Opaque"
}

resource "kubernetes_persistent_volume_claim" "db_pvc" {
  metadata {
    name      = "db-pvc"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "1Gi"
      }
    }
  }
}

resource "kubernetes_deployment" "database" {
  metadata {
    name      = "database-deployment"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "database"
      }
    }
    template {
      metadata {
        labels = {
          app = "database"
        }
      }
      spec {
        container {
          name  = "database-container"
          image = "${azurerm_container_registry.acr.login_server}/database:latest"

          env_from {
            secret_ref {
              name = kubernetes_secret.db_secret.metadata.0.name
            }
          }

          port {
            container_port = 5432
          }

          volume_mount {
            mount_path = "/var/lib/postgresql/data"
            name       = "db-storage"
          }

          readiness_probe {
            exec {
              command = ["pg_isready", "-U", "dev_user", "-d", "realestate_db"]
            }
            initial_delay_seconds = 10
            period_seconds      = 10
            timeout_seconds     = 3
            failure_threshold   = 5
          }
        }
        volume {
          name = "db-storage"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.db_pvc.metadata.0.name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "database_service" {
  metadata {
    name      = "database"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
  }
  spec {
    selector = {
      app = "database"
    }
    port {
      port        = 5432
      target_port = 5432
    }
    type = "ClusterIP"
  }
}