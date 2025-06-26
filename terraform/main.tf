terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }
}

provider "azurerm" {
  features {}
}

provider "kubernetes" {
  alias = "aks"

  host                   = azurerm_kubernetes_cluster.aks.kube_config.0.host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.cluster_ca_certificate)
}

provider "helm" {
  alias = "aks"

  kubernetes {
    host                   = azurerm_kubernetes_cluster.aks.kube_config.0.host
    client_certificate     = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_certificate)
    client_key             = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_key)
    cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.cluster_ca_certificate)
  }
}

resource "azurerm_resource_group" "rg" {
  name     = "bachelorrg"
  location = "Sweden Central"
}

resource "azurerm_container_registry" "acr" {
  name                = "bacheloracr"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Standard"
  admin_enabled       = true
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "bachelor-logs-workspace"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_kubernetes_cluster" "aks" {
  name                = "bacheloraks"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "bachelorproject"

  default_node_pool {
    name       = "default"
    node_count = 1
    vm_size    = "Standard_B2ms"
    temporary_name_for_rotation = "tempnodepool"
  }

  identity {
    type = "SystemAssigned"
  }

  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  }

  network_profile {
    network_plugin     = "kubenet"
    service_cidr       = "10.0.0.0/16"
    dns_service_ip     = "10.0.1.10"
    docker_bridge_cidr = "172.17.0.1/16"
  }
}

resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  # Use the main principal ID of the AKS cluster for more reliable pull permissions
  principal_id         = azurerm_kubernetes_cluster.aks.identity[0].principal_id
}

resource "kubernetes_namespace" "app_ns" {
  provider = kubernetes.aks
 
  metadata {
    name = "bachelor-app"
  }
}