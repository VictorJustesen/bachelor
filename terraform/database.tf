# 1. Create the Azure Database for PostgreSQL server
resource "azurerm_postgresql_flexible_server" "db_server" {
  name                   = "bachelor-postgres-server"
  resource_group_name    = azurerm_resource_group.rg.name
  location               = azurerm_resource_group.rg.location
  zone                   = "1"
  version                = "13"
  sku_name               = "B_Standard_B1ms"

  administrator_login    = "dev_user"
  administrator_password = "YourSecurePassword123!"
  storage_mb             = 32768
  
  public_network_access_enabled = true
}

# Configure SSL settings
resource "azurerm_postgresql_flexible_server_configuration" "ssl_enforcement" {
  name      = "ssl"
  server_id = azurerm_postgresql_flexible_server.db_server.id
  value     = "on"
}

resource "azurerm_postgresql_flexible_server_configuration" "ssl_min_protocol_version" {
  name      = "ssl_min_protocol_version"
  server_id = azurerm_postgresql_flexible_server.db_server.id
  value     = "TLSv1.2"
}

# Allow the uuid extension
resource "azurerm_postgresql_flexible_server_configuration" "allow_extensions" {
  name      = "azure.extensions"
  server_id = azurerm_postgresql_flexible_server.db_server.id
  value     = "uuid-ossp"
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

resource "kubernetes_config_map" "db_init_script" {
  provider = kubernetes.aks

  metadata {
    name      = "db-init-script"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
  }

  data = {
    "init.sql" = file("${path.module}/../database/init.sql")
  }
}

# 6. Create a Kubernetes Job to run the init.sql script
resource "kubernetes_job" "db_init_job" {
  provider = kubernetes.aks

  metadata {
    name      = "db-schema-initializer"
    namespace = kubernetes_namespace.app_ns.metadata.0.name
  }

  spec {
    template {
      metadata {}
      spec {
        container {
          name    = "db-init-container"
          image   = "postgres:13"
          
          command = [
            "/bin/sh",
            "-c",
            "sleep 5 && PGPASSWORD=$POSTGRES_PASSWORD psql --file=/scripts/init.sql --host=$POSTGRES_HOST --username=$POSTGRES_USER --dbname=$POSTGRES_DB --port=5432"
            #might need longer weight
          ]

          env_from {
            secret_ref {
              name = kubernetes_secret.db_secret.metadata.0.name
            }
          }

          volume_mount {
            name       = "sql-scripts"
            mount_path = "/scripts"
          }
        }

        volume {
          name = "sql-scripts"
          config_map {
            name = kubernetes_config_map.db_init_script.metadata.0.name
          }
        }
        
        restart_policy = "Never"
      }
    }
    backoff_limit = 4
  }

  # Make sure the job only runs after the database is ready
  depends_on = [
    azurerm_postgresql_flexible_server.db_server,
    kubernetes_secret.db_secret
  ]
}