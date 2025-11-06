#!/bin/bash

# Azure Function Webhook Deployment Script

set -e  # Exit on any error

echo "========================================"
echo "Azure Function Webhook Deployment"
echo "========================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed. Please install it first."
    exit 1
fi

if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check Azure login
if ! az account show &> /dev/null; then
    echo "❌ Not logged into Azure. Please run 'az login' first."
    exit 1
fi

echo "✅ All prerequisites met"
echo ""

# Deploy infrastructure
echo "Step 1: Deploying Azure infrastructure with Terraform..."
terraform init
terraform apply -auto-approve

echo ""
echo "✅ Infrastructure deployed successfully"
echo ""

# Get function app name
FUNCTION_APP_NAME=$(terraform output -raw function_app_name)
echo "Function App Name: $FUNCTION_APP_NAME"
echo ""

# Deploy function code
echo "Step 2: Deploying function code..."

# Check if Azure Functions Core Tools is available
if command -v func &> /dev/null; then
    echo "Using Azure Functions Core Tools..."
    func azure functionapp publish $FUNCTION_APP_NAME --python
else
    echo "Azure Functions Core Tools not found. Using Azure CLI with zip deployment..."
    
    # Create deployment package
    zip -r function.zip function_app.py requirements.txt host.json .funcignore
    
    # Deploy using Azure CLI
    az functionapp deployment source config-zip \
        --resource-group rg-webhook-function \
        --name $FUNCTION_APP_NAME \
        --src function.zip
    
    # Clean up zip file
    rm function.zip
fi

echo ""
echo "✅ Function code deployed successfully"
echo ""

# Display outputs
echo "========================================"
echo "Deployment Complete!"
echo "========================================"
echo ""
terraform output
echo ""
echo "Test your webhook with:"
echo "curl -X POST $(terraform output -raw webhook_url) \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"message\": \"Hello from webhook!\"}'"
echo ""
echo "View logs with:"
echo "az functionapp log tail --name $FUNCTION_APP_NAME --resource-group rg-webhook-function"
