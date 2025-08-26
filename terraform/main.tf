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
  # Use the Kubelet's Managed Identity for pulling images
  principal_id         = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id
}

resource "kubernetes_namespace" "app_ns" {
  provider = kubernetes.aks
 
  metadata {
    name = "bachelor-app"
  }
}

# --- NEW: Create a Storage Account for the scraper data ---
resource "azurerm_storage_account" "scraperdata" {
  name                     = "bachelorscraperdata" # A unique name is required
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# --- NEW: Create a Blob Container inside the Storage Account ---
resource "azurerm_storage_container" "scraperdata" {
  name                  = "scraper-data-container"
  storage_account_name  = azurerm_storage_account.scraperdata.name
  container_access_type = "private"
}

# --- NEW: Upload the CSV file to the Blob Container ---
# This resource will upload your local file during the 'terraform apply'
resource "azurerm_storage_blob" "csv_blob" {
  name                   = "cleaned_data.csv"
  storage_account_name   = azurerm_storage_account.scraperdata.name
  storage_container_name = azurerm_storage_container.scraperdata.name
  type                   = "Block"
  source                 = "../scraping2/dataexplor/cleaned_data_harshertesttest4.csv" # Path to your local CSV
}

# Helper to generate a unique name for the storage account
resource "random_id" "unique" {
  byte_length = 8
}
