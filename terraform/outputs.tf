# Resource Group
output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_location" {
  description = "Location of the resource group"
  value       = azurerm_resource_group.main.location
}

# Frontend Web App
output "frontend_url" {
  description = "URL of the frontend web app"
  value       = "https://${azurerm_linux_web_app.frontend.default_hostname}"
}

output "frontend_staging_url" {
  description = "URL of the frontend staging slot"
  value       = "https://${azurerm_linux_web_app_slot.staging.default_hostname}"
}

output "web_app_name" {
  description = "Name of the frontend web app"
  value       = azurerm_linux_web_app.frontend.name
}

# Backend Function App
output "backend_url" {
  description = "URL of the backend function app"
  value       = "https://${azurerm_linux_function_app.backend.default_hostname}"
}

output "backend_api_url" {
  description = "API URL of the backend function app"
  value       = "https://${azurerm_linux_function_app.backend.default_hostname}/api"
}

output "function_app_name" {
  description = "Name of the backend function app"
  value       = azurerm_linux_function_app.backend.name
}

# Database
output "postgres_server_fqdn" {
  description = "FQDN of the PostgreSQL server"
  value       = azurerm_postgresql_flexible_server.main.fqdn
}

output "postgres_database_name" {
  description = "Name of the PostgreSQL database"
  value       = azurerm_postgresql_flexible_server_database.main.name
}

# Redis
output "redis_hostname" {
  description = "Hostname of the Redis cache"
  value       = azurerm_redis_cache.main.hostname
}

# Storage
output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.uploads_storage.name
}

output "storage_container_name" {
  description = "Name of the storage container"
  value       = azurerm_storage_container.uploads.name
}

# Key Vault
output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.main.name
}

output "key_vault_url" {
  description = "URL of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

# Application Insights
output "application_insights_connection_string" {
  description = "Connection string for Application Insights"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "application_insights_instrumentation_key" {
  description = "Instrumentation key for Application Insights"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

# Deployment Information
output "deployment_commands" {
  description = "Commands to deploy the applications"
  value = {
    backend_deployment = "az functionapp deployment source config-zip --resource-group ${azurerm_resource_group.main.name} --name ${azurerm_linux_function_app.backend.name} --src function-app.zip"
    frontend_deployment = "az webapp deployment source config-zip --resource-group ${azurerm_resource_group.main.name} --name ${azurerm_linux_web_app.frontend.name} --src build.zip"
  }
}

# Summary
output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    resource_group = azurerm_resource_group.main.name
    location = azurerm_resource_group.main.location
    frontend_url = "https://${azurerm_linux_web_app.frontend.default_hostname}"
    backend_url = "https://${azurerm_linux_function_app.backend.default_hostname}"
    database_server = azurerm_postgresql_flexible_server.main.fqdn
    redis_hostname = azurerm_redis_cache.main.hostname
    storage_account = azurerm_storage_account.uploads_storage.name
    key_vault = azurerm_key_vault.main.name
  }
}

output "redis_ssl_port" {
  description = "SSL port of the Redis cache"
  value       = azurerm_redis_cache.main.ssl_port
}

# Storage
output "uploads_storage_account_name" {
  description = "Name of the uploads storage account"
  value       = azurerm_storage_account.uploads_storage.name
}

output "uploads_container_name" {
  description = "Name of the uploads container"
  value       = azurerm_storage_container.uploads.name
}

# Key Vault
output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

# Application Insights
output "application_insights_instrumentation_key" {
  description = "Instrumentation key for Application Insights"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "application_insights_connection_string" {
  description = "Connection string for Application Insights"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

# Deployment information
output "deployment_commands" {
  description = "Commands to deploy the application"
  value = {
    frontend = "az webapp deployment source config-zip --resource-group ${azurerm_resource_group.main.name} --name ${azurerm_linux_web_app.frontend.name} --src frontend.zip"
    backend  = "func azure functionapp publish ${azurerm_linux_function_app.backend.name} --python"
  }
}
