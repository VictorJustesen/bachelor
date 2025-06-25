terraform {
  backend "azurerm" {
    resource_group_name  = "bachelorrg"
    storage_account_name = "bachelortfstate"
    container_name       = "tfstate"
    key                  = "prod.terraform.tfstate"
  }
}
