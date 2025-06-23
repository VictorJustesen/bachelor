# apps.tf

# Backend Deployment
resource "kubernetes_deployment" "backend" {
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
            value = "dev"
          }
           env {
            name = "DB_HOST"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db_secret.metadata.0.name
                key  = "POSTGRES_HOST"
              }
            }
          }
          env {
            name  = "DB_PORT"
            value = "5432"
          }
          env {
            name  = "DB_NAME"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db_secret.metadata.0.name
                key  = "POSTGRES_DB"
              }
            }
          }
          env {
            name  = "DB_USER"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db_secret.metadata.0.name
                key  = "POSTGRES_USER"
              }
            }
          }
          env {
            name  = "DB_PASSWORD"
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
      target_port = 3000 # Assuming your backend runs on port 3000 inside the container
    }
    type = "ClusterIP"
  }
}

# Frontend, Scraper, Predictor would follow a similar pattern for deployments and services...
# Here are the deployments:

resource "kubernetes_deployment" "frontend" {
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

resource "kubernetes_deployment" "scraper" {
  metadata {
    name      = "scraper-deployment"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "scraper"
      }
    }
    template {
      metadata {
        labels = {
          app = "scraper"
        }
      }
      spec {
        container {
          name  = "scraper-container"
          image = "${azurerm_container_registry.acr.login_server}/scraper:latest"
          port {
            container_port = 9000
          }
        }
      }
    }
  }
}

resource "kubernetes_deployment" "predictor" {
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

# Configure the Helm provider to connect to your AKS cluster
provider "helm" {
  kubernetes {
    host                   = azurerm_kubernetes_cluster.aks.kube_config.0.host
    client_certificate     = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_certificate)
    client_key             = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_key)
    cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.cluster_ca_certificate)
  }
}

# Configure the Kubernetes provider to connect to your AKS cluster
provider "kubernetes" {
  host                   = azurerm_kubernetes_cluster.aks.kube_config.0.host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.cluster_ca_certificate)
}

# Use the Helm provider to install the ingress-nginx controller
resource "helm_release" "ingress_nginx" {
  name       = "ingress-nginx"
  repository = "https://kubernetes.github.io/ingress-nginx"
  chart      = "ingress-nginx"
  namespace  = "ingress-basic"
  create_namespace = true
}

# Use a loop to apply all YAML manifests from your kubernetes directory
resource "kubernetes_manifest" "app_manifests" {
  for_each = fileset("../kubernetes", "*.yaml")

  manifest = yamldecode(file("../kubernetes/${each.value}"))

  # This ensures the Ingress controller is ready before applying manifests that need it
  depends_on = [helm_release.ingress_nginx]
}