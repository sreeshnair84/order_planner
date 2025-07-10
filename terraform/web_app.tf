# App Service Plan for Web App
resource "azurerm_service_plan" "webapp_plan" {
  name                = "${var.project_name}-webapp-plan-${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = var.app_service_sku_name
  
  tags = local.common_tags
}

# Linux Web App for Frontend
resource "azurerm_linux_web_app" "frontend" {
  name                = "${var.project_name}-webapp-${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.webapp_plan.id
  
  site_config {
    always_on = false
    
    application_stack {
      node_version = "18-lts"
    }
  }
  
  app_settings = {
    "REACT_APP_API_URL" = "https://${azurerm_linux_function_app.backend.default_hostname}"
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    "WEBSITE_NODE_DEFAULT_VERSION" = "~18"
  }
  
  tags = local.common_tags
}

# Web App deployment slot for staging
resource "azurerm_linux_web_app_slot" "staging" {
  name           = "staging"
  app_service_id = azurerm_linux_web_app.frontend.id
  
  site_config {
    always_on = false
    
    application_stack {
      node_version = "18-lts"
    }
  }
  
  app_settings = {
    "REACT_APP_API_URL" = "https://${azurerm_linux_function_app.backend.default_hostname}/api"
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    "WEBSITE_NODE_DEFAULT_VERSION" = "~18"
  }
  
  tags = local.common_tags
}
