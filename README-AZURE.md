# Order Management System - Azure Deployment Guide

A comprehensive full-stack Order Management System built with React frontend and FastAPI backend, designed for FMCG/OEM providers. This guide focuses on deploying the application to Azure with the UI as an Azure Web App and the backend as Azure Functions.

## 🏗️ Azure Architecture

- **Frontend**: React 18 with Tailwind CSS → **Azure Web App (Linux)**
- **Backend**: FastAPI with Python 3.11 → **Azure Functions (Linux)**
- **Database**: **Azure Database for PostgreSQL**
- **Cache**: **Azure Cache for Redis**
- **Storage**: **Azure Blob Storage**
- **Email**: **SendGrid**
- **Monitoring**: **Application Insights**
- **Security**: **Azure Key Vault**
- **Infrastructure**: **Terraform**

## 🚀 Quick Azure Deployment

### Prerequisites

1. **Azure CLI**: Install from [here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
2. **Terraform**: Install from [here](https://www.terraform.io/downloads.html)
3. **Node.js**: Version 18 or higher
4. **Python**: Version 3.11 or higher

### One-Click Deployment

```bash
# 1. Clone and navigate to project
git clone <repository-url>
cd order_planner

# 2. Login to Azure
az login

# 3. Configure deployment
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# 4. Deploy everything
chmod +x ../deploy.sh
../deploy.sh
```

## 🔧 Manual Deployment Steps

### Step 1: Infrastructure Deployment

```bash
cd terraform

# Initialize Terraform
terraform init

# Review the deployment plan
terraform plan

# Deploy infrastructure
terraform apply
```

### Step 2: Backend Deployment (Azure Functions)

```bash
# Copy backend code to Azure Functions directory
cp -r backend/app backend_azure_functions/
cp backend/requirements.txt backend_azure_functions/

# Create deployment package
cd backend_azure_functions
zip -r function-app.zip . -x "*.git*" "*.env*" "__pycache__/*" "*.pyc"

# Deploy to Azure Functions
RESOURCE_GROUP=$(terraform output -raw resource_group_name)
FUNCTION_APP_NAME=$(terraform output -raw function_app_name)

az functionapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP_NAME \
  --src function-app.zip
```

### Step 3: Frontend Deployment (Azure Web App)

```bash
cd frontend

# Install dependencies and build
npm install
npm run build

# Create deployment package
zip -r build.zip build/

# Deploy to Azure Web App
WEB_APP_NAME=$(terraform output -raw web_app_name)

az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --src build.zip
```

## ⚙️ Configuration

### Terraform Variables

Edit `terraform/terraform.tfvars`:

```hcl
# Project Configuration
project_name = "order-management"
environment  = "prod"
location     = "East US"

# Database Configuration
postgres_admin_username = "orderadmin"
postgres_admin_password = "YourSecurePassword123!"
postgres_sku_name      = "B_Standard_B1ms"

# Redis Configuration
redis_sku_name = "Basic"
redis_family   = "C"
redis_capacity = 0

# App Service Configuration
app_service_sku_name  = "B1"    # Web App SKU
function_app_sku_name = "Y1"    # Function App SKU (Consumption)

# Storage Configuration
storage_account_tier             = "Standard"
storage_account_replication_type = "LRS"

# Email Configuration
sendgrid_api_key = "your-sendgrid-api-key"

# JWT Configuration
jwt_secret = "your-jwt-secret-key"

# Tags
tags = {
  Project     = "Order Management System"
  Environment = "Production"
  Owner       = "Your Name"
}
```

### Azure Resources Created

The Terraform scripts create the following Azure resources:

1. **Resource Group**: Container for all resources
2. **Azure Database for PostgreSQL**: Main database
3. **Azure Cache for Redis**: Caching and session storage
4. **Azure Storage Account**: File uploads and function storage
5. **Azure Function App**: Backend API (FastAPI)
6. **Azure Web App**: Frontend UI (React)
7. **Application Insights**: Monitoring and telemetry
8. **Log Analytics Workspace**: Centralized logging
9. **Azure Key Vault**: Secure configuration storage

## 🔐 Security Configuration

### Azure Key Vault Secrets

The deployment automatically creates the following secrets in Key Vault:

- `database-url`: PostgreSQL connection string
- `redis-url`: Redis connection string
- `jwt-secret`: JWT signing secret
- `sendgrid-api-key`: SendGrid API key

### Managed Identity

The system uses Azure Managed Identity for secure authentication:

- Function App uses system-assigned managed identity
- Web App uses system-assigned managed identity
- Access to Key Vault is granted through access policies

## 🚦 API Endpoints

### Health Check
- `GET /health` - Service health status

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh

### Orders
- `GET /api/orders` - List orders
- `POST /api/orders` - Create order
- `GET /api/orders/{id}` - Get order details
- `PUT /api/orders/{id}` - Update order
- `DELETE /api/orders/{id}` - Delete order

### File Upload
- `POST /api/files/upload` - Upload order file
- `GET /api/files/{id}` - Download file

### Tracking
- `GET /api/tracking/{order_id}` - Get order tracking
- `POST /api/tracking/{order_id}` - Update tracking status

## 🔄 CI/CD Pipeline

### GitHub Actions

The repository includes a complete CI/CD pipeline (`.github/workflows/deploy.yml`):

1. **Infrastructure**: Deploys Terraform resources
2. **Backend**: Builds and deploys Azure Functions
3. **Frontend**: Builds and deploys React app to Azure Web App
4. **Testing**: Runs tests on pull requests

**Required GitHub Secrets:**
```yaml
AZURE_CREDENTIALS: |
  {
    "clientId": "your-client-id",
    "clientSecret": "your-client-secret",
    "subscriptionId": "your-subscription-id",
    "tenantId": "your-tenant-id"
  }
POSTGRES_ADMIN_PASSWORD: "your-db-password"
SENDGRID_API_KEY: "your-sendgrid-key"
JWT_SECRET: "your-jwt-secret"
```

### Azure DevOps

Alternative pipeline configuration (`azure-pipelines.yml`) for Azure DevOps:

**Required Variables:**
- `azureServiceConnection`: Azure service connection
- `postgresAdminPassword`: Database password
- `sendgridApiKey`: SendGrid API key
- `jwtSecret`: JWT secret

## 📊 Monitoring and Logging

### Application Insights

Monitor your application with:
- **Performance**: Response times, throughput
- **Availability**: Uptime monitoring
- **Usage**: User analytics
- **Failures**: Error tracking

### Log Analytics

Centralized logging for:
- Function App logs
- Web App logs
- Database logs
- Security events

### Health Checks

Built-in health checks available at:
- Function App: `https://your-function-app.azurewebsites.net/health`
- Web App: `https://your-web-app.azurewebsites.net/health`

## 🔧 Troubleshooting

### Common Issues

1. **Function App not starting**
   - Check Application Insights logs
   - Verify Python version compatibility
   - Ensure all dependencies are in requirements.txt

2. **Database connection issues**
   - Verify PostgreSQL firewall rules
   - Check connection string in Key Vault
   - Ensure managed identity has database permissions

3. **CORS errors**
   - Verify CORS configuration in Function App
   - Check frontend API URL configuration

### Debug Commands

```bash
# View Function App logs
az functionapp log tail --name <function-app-name> --resource-group <resource-group>

# View Web App logs
az webapp log tail --name <web-app-name> --resource-group <resource-group>

# Check resource status
az resource list --resource-group <resource-group> --output table
```

## 💰 Cost Optimization

### Recommended Production SKUs

```hcl
# Basic tier for development/staging
app_service_sku_name  = "B1"      # ~$13/month
function_app_sku_name = "Y1"      # Consumption pricing
postgres_sku_name     = "B_Standard_B1ms"  # ~$24/month
redis_sku_name        = "Basic"   # ~$16/month

# Standard tier for production
app_service_sku_name  = "S1"      # ~$73/month
function_app_sku_name = "EP1"     # ~$146/month
postgres_sku_name     = "GP_Standard_D2s_v3"  # ~$117/month
redis_sku_name        = "Standard" # ~$95/month
```

### Cost Monitoring

Set up cost alerts in Azure:
```bash
az consumption budget create \
  --budget-name "order-management-budget" \
  --amount 200 \
  --time-grain Monthly \
  --time-period start-date=2024-01-01 \
  --resource-group <resource-group>
```

## 🛡️ Security Best Practices

1. **Use Azure Key Vault** for all secrets
2. **Enable Azure AD authentication** for additional security
3. **Configure network security groups** to restrict access
4. **Enable Azure Security Center** for threat detection
5. **Use managed identities** instead of connection strings
6. **Enable Azure DDoS protection** for production workloads

## 📱 Local Development

For local development, use the Docker Compose setup:

```bash
# Start local development environment
docker-compose up

# Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# Database: localhost:5432
# Redis: localhost:6379
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For Azure deployment support:
- Check Azure documentation
- Review Application Insights logs
- Create GitHub issues for bugs
- Use Azure support for infrastructure issues

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🎯 Next Steps After Deployment

1. **Configure custom domain** for your Web App
2. **Set up SSL certificates** for HTTPS
3. **Configure backup policies** for your database
4. **Set up monitoring alerts** in Azure Monitor
5. **Configure auto-scaling** for high availability
6. **Set up deployment slots** for blue-green deployments
