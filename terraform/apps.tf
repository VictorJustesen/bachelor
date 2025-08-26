# apps.tf

# Backend Deployment
resource "kubernetes_deployment" "backend" {
  provider = kubernetes.aks

  depends_on = [
    azurerm_role_assignment.aks_acr_pull
  ]

  metadata {
    name      = "backend-deployment"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "backend"
      }
    }
    template {
      metadata {
        labels = {
          app = "backend"
        }
      }
      spec {
        container {
          name  = "backend-container"
          image = "${azurerm_container_registry.acr.login_server}/backend:latest"
          env {
            name  = "SCRAPER_SERVICE_URL"
            value = "http://scraper:9000"
          }
          env {
            name  = "PREDICTOR_SERVICE_URL"
            value = "http://predictor:8001"
          }
          env {
            name  = "ENVIRONMENT"
            value = "prod"
          }
          # FIXED: Changed the 'name' to match database.js
          env {
            name = "POSTGRES_HOST"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db_secret.metadata.0.name
                key  = "POSTGRES_HOST"
              }
            }
          }
          # FIXED: Added POSTGRES_PORT for completeness
          env {
            name  = "POSTGRES_PORT"
            value = "5432"
          }
          # FIXED: Changed the 'name' to match database.js
          env {
            name  = "POSTGRES_DB"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db_secret.metadata.0.name
                key  = "POSTGRES_DB"
              }
            }
          }
          # FIXED: Changed the 'name' to match database.js
          env {
            name  = "POSTGRES_USER"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db_secret.metadata.0.name
                key  = "POSTGRES_USER"
              }
            }
          }
          # FIXED: Changed the 'name' to match database.js
          env {
            name  = "POSTGRES_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db_secret.metadata.0.name
                key  = "POSTGRES_PASSWORD"
              }
            }
          }
        }
      }
    }
  }
}


resource "kubernetes_service" "backend_service" {
  provider = kubernetes.aks

  metadata {
    name      = "backend"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
  }
  spec {
    selector = {
      app = "backend"
    }
    port {
      port        = 80
      target_port = 8000 # Assuming your backend runs on port 8000 inside the container
    }
    type = "ClusterIP"
  }
}

# Frontend, Scraper, Predictor would follow a similar pattern for deployments and services...
# Here are the deployments:

resource "kubernetes_deployment" "frontend" {
  provider = kubernetes.aks

  depends_on = [
    azurerm_role_assignment.aks_acr_pull
  ]

  metadata {
    name      = "frontend-deployment"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "frontend"
      }
    }
    template {
      metadata {
        labels = {
          app = "frontend"
        }
      }
      spec {
        container {
          name  = "frontend-container"
          image = "${azurerm_container_registry.acr.login_server}/frontend:latest"
          port {
            container_port = 3000
          }
        }
      }
    }
  }
}
resource "kubernetes_secret" "storage_secret" {
  provider = kubernetes.aks
  metadata {
    name      = "storage-secret"
    namespace = kubernetes_namespace.app_ns.metadata[0].name
  }
  data = {
    AZURE_STORAGE_CONNECTION_STRING = azurerm_storage_account.scraperdata.primary_connection_string
  }
}

resource "kubernetes_deployment" "scraper" {
  provider  = kubernetes.aks
  # depends_on is no longer needed

  metadata {
    name      = "scraper-deployment"
    namespace = "bachelor-app"
  }
  spec {
    replicas = 1
    selector { match_labels = { app = "scraper" } }
    template {
      metadata { labels = { app = "scraper" } }
      spec {
        # --- NEW: Init Container ---
        # This container runs to completion before the main container starts.
        init_container {
          name    = "blob-downloader"
          image   = "mcr.microsoft.com/azure-cli"
          command = ["/bin/sh", "-c"]
          args = [
            "az storage blob download --container-name scraper-data-container --name cleaned_data.csv --file /data/cleaned_data.csv --connection-string $(AZURE_STORAGE_CONNECTION_STRING)"
          ]

          # Mount the shared volume
          volume_mount {
            name       = "scraper-data-volume"
            mount_path = "/data"
          }

          # Get the connection string from our new secret
          env {
            name = "AZURE_STORAGE_CONNECTION_STRING"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.storage_secret.metadata[0].name
                key  = "AZURE_STORAGE_CONNECTION_STRING"
              }
            }
          }
        }

        # --- Main Application Container ---
        container {
          name  = "scraper-container"
          image = "${azurerm_container_registry.acr.login_server}/scraper:latest"
          port { container_port = 9000 }

          env {
            name  = "DATA_FILE_PATH"
            value = "/data/cleaned_data.csv" # It will find the file here
          }

          # Mount the shared volume where the file was downloaded
          volume_mount {
            name       = "scraper-data-volume"
            mount_path = "/data"
          }
        }

        # --- The Shared Volume ---
        # This is a temporary directory that both containers can see.
        volume {
          name = "scraper-data-volume"
          empty_dir {}
        }
      }
    }
  }
}



resource "kubernetes_deployment" "predictor" {
  provider = kubernetes.aks

  depends_on = [
    azurerm_role_assignment.aks_acr_pull
  ]

  metadata {
    name      = "predictor-deployment"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "predictor"
      }
    }
    template {
      metadata {
        labels = {
          app = "predictor"
        }
      }
      spec {
        container {
          name  = "predictor-container"
          image = "${azurerm_container_registry.acr.login_server}/predictor:latest"
          port {
            container_port = 8001
          }
           env {
            name  = "PYTHONPATH"
            value = "/app/automltrainer_lib"
          }
        }
      }
    }
  }
}

# ClusterIP Services for internal communication
resource "kubernetes_service" "frontend_service" {
  provider = kubernetes.aks

  metadata {
    name      = "frontend"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
  }
  spec {
    selector = {
      app = "frontend"
    }
    port {
      port        = 80
      target_port = 3000
    }
    type = "ClusterIP"
  }
}

resource "kubernetes_service" "scraper_service" {
  provider = kubernetes.aks

  metadata {
    name      = "scraper"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
  }
  spec {
    selector = {
      app = "scraper"
    }
    port {
      port        = 9000
      target_port = 9000
    }
    type = "ClusterIP"
  }
}

resource "kubernetes_service" "predictor_service" {
  provider = kubernetes.aks

  metadata {
    name      = "predictor"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
  }
  spec {
    selector = {
      app = "predictor"
    }
    port {
      port        = 8001
      target_port = 8001
    }
    type = "ClusterIP"
  }
}



# Use the Helm provider to install the ingress-nginx controller
resource "helm_release" "ingress_nginx" {
  provider = helm.aks

  name       = "ingress-nginx"
  repository = "https://kubernetes.github.io/ingress-nginx"
  chart      = "ingress-nginx"
  namespace  = "ingress-basic"
  create_namespace = true

  depends_on = [
    azurerm_kubernetes_cluster.aks
  ]
}

resource "kubernetes_ingress_v1" "main_ingress" {
  provider = kubernetes.aks

  metadata {
    name      = "main-ingress"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
    annotations = {
      # This annotation is fine for the frontend, but we don't want it for the API
      "kubernetes.io/ingress.class" = "nginx"
    }
  }

  spec {
    rule {
      http {
        # FIX: Path for the API with NO rewrite
        path {
          path      = "/api"
          path_type = "Prefix"
          backend {
            service {
              name = kubernetes_service.backend_service.metadata.0.name
              port {
                number = 80
              }
            }
          }
        }

        # Path for the frontend, which can have a rewrite if needed
        path {
          path      = "/"
          path_type = "Prefix"
          backend {
            service {
              name = kubernetes_service.frontend_service.metadata.0.name
              port {
                number = 80
              }
            }
          }
        }
      }
    }
  }



  depends_on = [
    kubernetes_service.backend_service,
    kubernetes_service.frontend_service
  ]
}