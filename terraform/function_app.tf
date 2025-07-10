# App Service Plan for Function App
resource "azurerm_service_plan" "function_plan" {
  name                = "${var.project_name}-func-plan-${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = var.function_app_sku_name
  
  tags = local.common_tags
}

# Function App for Backend API
resource "azurerm_linux_function_app" "backend" {
  name                       = "${var.project_name}-func-${local.resource_suffix}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  service_plan_id           = azurerm_service_plan.function_plan.id
  storage_account_name       = azurerm_storage_account.function_storage.name
  storage_account_access_key = azurerm_storage_account.function_storage.primary_access_key
  
  builtin_logging_enabled = false
  
  site_config {
    application_insights_key               = azurerm_application_insights.main.instrumentation_key
    application_insights_connection_string = azurerm_application_insights.main.connection_string
    
    application_stack {
      python_version = "3.11"
    }
    
    cors {
      allowed_origins = [
        "https://${azurerm_linux_web_app.frontend.default_hostname}",
        "http://localhost:3000",
        "https://dispatchplannerapp.wonderfultree-66eac7c6.eastus.azurecontainerapps.io"
      ]
      support_credentials = true
    }
  }
  
  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"       = "python"
    "AzureWebJobsFeatureFlags"      = "EnableWorkerIndexing"
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    
    # Database configuration
    "DATABASE_URL" = "postgresql://${var.postgres_admin_username}:${var.postgres_admin_password}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${azurerm_postgresql_flexible_server_database.main.name}?sslmode=require"
    
    # Redis configuration
    "REDIS_URL" = "rediss://:${azurerm_redis_cache.main.primary_access_key}@${azurerm_redis_cache.main.hostname}:${azurerm_redis_cache.main.ssl_port}"
    
    # JWT configuration
    "SECRET_KEY" = var.jwt_secret_key
    "ALGORITHM" = "HS256"
    "ACCESS_TOKEN_EXPIRE_MINUTES" = "15"
    "REFRESH_TOKEN_EXPIRE_DAYS" = "7"
    
    # File upload configuration
    "MAX_FILE_SIZE" = "10485760"
    "UPLOAD_CONTAINER" = azurerm_storage_container.uploads.name
    "AZURE_STORAGE_CONNECTION_STRING" = azurerm_storage_account.uploads_storage.primary_connection_string
    "ALLOWED_FILE_TYPES" = ".csv,.xml,.log,.txt"
    
    # Email configuration
    "SMTP_SERVER" = var.smtp_server
    "SMTP_PORT" = var.smtp_port
    "SMTP_USERNAME" = var.smtp_username
    "SMTP_PASSWORD" = var.smtp_password
    
    # CORS configuration
    "ALLOWED_ORIGINS" = "https://${azurerm_linux_web_app.frontend.default_hostname},http://localhost:3000,https://dispatchplannerapp.wonderfultree-66eac7c6.eastus.azurecontainerapps.io"
    
    # Logging
    "LOG_LEVEL" = "INFO"
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = local.common_tags
}

# Storage Blob Data Contributor role assignment for Function App
resource "azurerm_role_assignment" "function_storage_contributor" {
  scope                = azurerm_storage_account.uploads_storage.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_function_app.backend.identity[0].principal_id
}
