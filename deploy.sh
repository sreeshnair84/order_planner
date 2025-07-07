#!/bin/bash
# Deployment script for Order Management System Azure Infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
TERRAFORM_DIR="terraform"
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
AZURE_FUNCTIONS_DIR="backend_azure_functions"

echo -e "${GREEN}🚀 Starting Azure Infrastructure Deployment${NC}"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform is not installed. Please install it first.${NC}"
    exit 1
fi

# Login to Azure if not already logged in
echo -e "${YELLOW}🔐 Checking Azure authentication...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}Please login to Azure...${NC}"
    az login
fi

# Display current subscription
echo -e "${GREEN}📋 Current Azure Subscription:${NC}"
az account show --output table

# Ask for confirmation
read -p "Do you want to proceed with this subscription? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled.${NC}"
    exit 0
fi

# Change to terraform directory
cd "$TERRAFORM_DIR"

# Check if terraform.tfvars exists
if [[ ! -f "terraform.tfvars" ]]; then
    echo -e "${YELLOW}⚠️  terraform.tfvars not found. Creating from example...${NC}"
    cp terraform.tfvars.example terraform.tfvars
    echo -e "${RED}❌ Please edit terraform.tfvars with your specific values before running this script again.${NC}"
    exit 1
fi

# Initialize Terraform
echo -e "${YELLOW}🏗️  Initializing Terraform...${NC}"
terraform init

# Format Terraform files
echo -e "${YELLOW}🎨 Formatting Terraform files...${NC}"
terraform fmt

# Validate Terraform configuration
echo -e "${YELLOW}✅ Validating Terraform configuration...${NC}"
terraform validate

# Plan deployment
echo -e "${YELLOW}📋 Planning deployment...${NC}"
terraform plan -out=tfplan

# Ask for confirmation before applying
read -p "Do you want to apply this plan? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled.${NC}"
    exit 0
fi

# Apply deployment
echo -e "${YELLOW}🚀 Applying infrastructure deployment...${NC}"
terraform apply tfplan

# Display outputs
echo -e "${GREEN}📊 Deployment completed! Here are the important URLs:${NC}"
terraform output

# Prepare Azure Function deployment
echo -e "${YELLOW}📦 Preparing Azure Function deployment...${NC}"
cd "../$AZURE_FUNCTIONS_DIR"

# Copy backend code to Azure Functions directory
echo -e "${YELLOW}📁 Copying backend code...${NC}"
cp -r "../$BACKEND_DIR/app" ./
cp "../$BACKEND_DIR/requirements.txt" ./

# Create deployment package
echo -e "${YELLOW}📦 Creating deployment package...${NC}"
zip -r function-app.zip . -x "*.git*" "*.env*" "__pycache__/*" "*.pyc"

# Get function app name from terraform output
cd "../$TERRAFORM_DIR"
FUNCTION_APP_NAME=$(terraform output -raw function_app_name)
RESOURCE_GROUP_NAME=$(terraform output -raw resource_group_name)

# Deploy to Azure Functions
echo -e "${YELLOW}🚀 Deploying to Azure Functions...${NC}"
cd "../$AZURE_FUNCTIONS_DIR"
az functionapp deployment source config-zip \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$FUNCTION_APP_NAME" \
    --src function-app.zip

# Frontend deployment instructions
echo -e "${GREEN}✅ Infrastructure deployment complete!${NC}"
echo -e "${YELLOW}📋 Next steps for frontend deployment:${NC}"
echo "1. Build the React app:"
echo "   cd $FRONTEND_DIR"
echo "   npm install"
echo "   npm run build"
echo ""
echo "2. Deploy to Azure Web App:"
echo "   az webapp deployment source config-zip \\"
echo "     --resource-group $RESOURCE_GROUP_NAME \\"
echo "     --name \$(terraform output -raw web_app_name) \\"
echo "     --src build.zip"
echo ""
echo -e "${GREEN}🎉 Deployment script completed!${NC}"
