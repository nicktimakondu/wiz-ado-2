terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Variables for Azure DevOps configuration
variable "azdo_org_url" {
  description = "Azure DevOps organization URL (e.g., https://dev.azure.com/yourorg)"
  type        = string
}

variable "azdo_project" {
  description = "Azure DevOps project name where work items will be created"
  type        = string
}

# Resource Group
resource "azurerm_resource_group" "rg" {
  name     = "rg-webhook-function"
  location = "Central US"
}

# Storage Account (required for Azure Functions)
resource "azurerm_storage_account" "storage" {
  name                     = "stwebhookfunc${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# Random string for unique naming
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# App Service Plan (Consumption plan for serverless)
resource "azurerm_service_plan" "plan" {
  name                = "asp-webhook-function"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "Y1" # Consumption plan
}

# Application Insights (optional but recommended)
resource "azurerm_application_insights" "insights" {
  name                = "appi-webhook-function"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  application_type    = "web"
  workspace_id = "/subscriptions/f100f736-376d-4b86-b681-632f72504b17/resourceGroups/ai_appi-webhook-function_abb6a9b6-dbfd-4998-8a99-456f9b844b9b_managed/providers/Microsoft.OperationalInsights/workspaces/managed-appi-webhook-function-ws"
}

# Linux Function App
resource "azurerm_linux_function_app" "function" {
  name                       = "func-webhook-${random_string.suffix.result}"
  resource_group_name        = azurerm_resource_group.rg.name
  location                   = azurerm_resource_group.rg.location
  service_plan_id            = azurerm_service_plan.plan.id
  storage_account_name       = azurerm_storage_account.storage.name
  storage_account_access_key = azurerm_storage_account.storage.primary_access_key

  # Enable system-assigned managed identity
  identity {
    type = "SystemAssigned"
  }

  site_config {
    application_stack {
      python_version = "3.11"
    }
    
    cors {
      allowed_origins = ["*"]
    }
  }

  app_settings = {
    "APPINSIGHTS_INSTRUMENTATIONKEY"        = azurerm_application_insights.insights.instrumentation_key
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = azurerm_application_insights.insights.connection_string
    "FUNCTIONS_WORKER_RUNTIME"              = "python"
    # Azure DevOps Configuration - No PAT needed with Managed Identity
    "AZDO_ORG_URL"                          = var.azdo_org_url
    "AZDO_PROJECT"                          = var.azdo_project
  }

  lifecycle {
    ignore_changes = [
      app_settings["WEBSITE_RUN_FROM_PACKAGE"],
    ]
  }
}

# Outputs
output "function_app_name" {
  value       = azurerm_linux_function_app.function.name
  description = "The name of the Function App"
}

output "function_app_url" {
  value       = "https://${azurerm_linux_function_app.function.default_hostname}"
  description = "The URL of the Function App"
}

output "webhook_url" {
  value       = "https://${azurerm_linux_function_app.function.default_hostname}/api/webhook"
  description = "The webhook endpoint URL"
}

output "managed_identity_principal_id" {
  value       = azurerm_linux_function_app.function.identity[0].principal_id
  description = "The Principal ID of the Function App's Managed Identity"
}

output "managed_identity_tenant_id" {
  value       = azurerm_linux_function_app.function.identity[0].tenant_id
  description = "The Tenant ID of the Function App's Managed Identity"
}

output "managed_identity_service_principal_name" {
  value       = "func-webhook-${random_string.suffix.result}"
  description = "The service principal name (same as function app name) to add to Azure DevOps"
}
