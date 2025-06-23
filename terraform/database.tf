# 1. Create the Azure Database for PostgreSQL server
resource "azurerm_postgresql_flexible_server" "db_server" {
  name                   = "bachelor-postgres-server" # Choose a unique name
  resource_group_name    = azurerm_resource_group.rg.name
  location               = azurerm_resource_group.rg.location
  zone                   = "1" # Add this line to pin the zone
  version                = "13"
  sku_name               = "B_Standard_B1ms" # This SKU is eligible for the Azure Free Tier

  administrator_login    = "dev_user"
  administrator_password = "YourSecurePassword123!" # Hardcoded as requested
  storage_mb             = 32768
  
  public_network_access_enabled = true
}

# 2. Create the specific database within the server
resource "azurerm_postgresql_flexible_server_database" "db" {
  name      = "realestate_db"
  server_id = azurerm_postgresql_flexible_server.db_server.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# 3. Create a firewall rule to allow Azure services to connect
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_all_dev" {
  name             = "allow-all-ips-for-dev"
  server_id        = azurerm_postgresql_flexible_server.db_server.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "255.255.255.255"
}

# 4. Update the Kubernetes secret with the new Azure DB connection info
resource "kubernetes_secret" "db_secret" {
  provider = kubernetes.aks
  
  metadata {
    name      = "db-secret"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
  }
  data = {
    POSTGRES_HOST     = azurerm_postgresql_flexible_server.db_server.fqdn
    POSTGRES_USER     = azurerm_postgresql_flexible_server.db_server.administrator_login
    POSTGRES_PASSWORD = azurerm_postgresql_flexible_server.db_server.administrator_password
    POSTGRES_DB       = azurerm_postgresql_flexible_server_database.db.name
  }
  type = "Opaque"
}