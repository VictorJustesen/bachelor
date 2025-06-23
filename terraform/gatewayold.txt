# gateway.tf

resource "kubernetes_deployment" "api_gateway" {
  metadata {
    name      = "api-gateway-deployment"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "api-gateway"
      }
    }
    template {
      metadata {
        labels = {
          app = "api-gateway"
        }
      }
      spec {
        container {
          name  = "gateway-container"
          image = "${azurerm_container_registry.acr.login_server}/gateway:latest"
          port {
            container_port = 80
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "api_gateway_service" {
  metadata {
    name      = "api-gateway"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
  }
  spec {
    selector = {
      app = "api-gateway"
    }
    port {
      port        = 80
      target_port = 80
    }
    type = "LoadBalancer"
  }
}