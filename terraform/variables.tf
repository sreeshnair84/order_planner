# Project variables
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "order-management"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "East US"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = ""
}

# Database variables
variable "postgres_admin_username" {
  description = "PostgreSQL administrator username"
  type        = string
  default     = "orderadmin"
}

variable "postgres_admin_password" {
  description = "PostgreSQL administrator password"
  type        = string
  sensitive   = true
}

variable "postgres_sku_name" {
  description = "PostgreSQL SKU name"
  type        = string
  default     = "B_Standard_B1ms"
}

variable "postgres_storage_mb" {
  description = "PostgreSQL storage in MB"
  type        = number
  default     = 32768
}

# Redis variables
variable "redis_sku_name" {
  description = "Redis SKU name"
  type        = string
  default     = "Basic"
}

variable "redis_family" {
  description = "Redis family"
  type        = string
  default     = "C"
}

variable "redis_capacity" {
  description = "Redis capacity"
  type        = number
  default     = 0
}

# App Service variables
variable "app_service_sku_name" {
  description = "App Service SKU name"
  type        = string
  default     = "B1"
}

# Function App variables
variable "function_app_sku_name" {
  description = "Function App SKU name"
  type        = string
  default     = "Y1"
}

# Storage variables
variable "storage_account_tier" {
  description = "Storage account tier"
  type        = string
  default     = "Standard"
}

variable "storage_account_replication_type" {
  description = "Storage account replication type"
  type        = string
  default     = "LRS"
}

# Email configuration
variable "smtp_server" {
  description = "SMTP server for email notifications"
  type        = string
  default     = "smtp.gmail.com"
}

variable "smtp_port" {
  description = "SMTP port for email notifications"
  type        = number
  default     = 587
}

variable "smtp_username" {
  description = "SMTP username for email notifications"
  type        = string
  default     = ""
}

variable "smtp_password" {
  description = "SMTP password for email notifications"
  type        = string
  sensitive   = true
  default     = ""
}

# JWT configuration
variable "jwt_secret_key" {
  description = "JWT secret key for authentication"
  type        = string
  sensitive   = true
}

# Tags
variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "OrderManagement"
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}
