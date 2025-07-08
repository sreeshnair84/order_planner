# Azure Deployment Checklist

## 📋 Pre-Deployment Checklist

### Prerequisites
- [ ] Azure CLI installed and logged in (`az login`)
- [ ] Terraform installed (version 1.6.0 or later)
- [ ] Node.js 18+ installed
- [ ] Python 3.11+ installed
- [ ] Access to Azure subscription with Contributor rights

### Configuration
- [ ] Created `terraform/terraform.tfvars` from `terraform.tfvars.example`
- [ ] Updated PostgreSQL admin password (secure password)
- [ ] Configured SendGrid API key
- [ ] Set JWT secret key (32+ characters)
- [ ] Reviewed and set appropriate SKUs for your environment

### SendGrid Setup
- [ ] Created SendGrid account
- [ ] Generated API key with Mail Send permissions
- [ ] Verified sender email address
- [ ] Added SendGrid API key to terraform.tfvars

### Azure Subscription
- [ ] Verified Azure subscription has sufficient quotas
- [ ] Confirmed region availability for all services
- [ ] Checked cost estimates for selected SKUs

## 🚀 Deployment Steps

### Step 1: Infrastructure Deployment
- [ ] Navigate to terraform directory (`cd terraform`)
- [ ] Run `terraform init`
- [ ] Run `terraform plan` and review changes
- [ ] Run `terraform apply` and confirm deployment
- [ ] Save terraform outputs for later use

### Step 2: Backend Deployment
- [ ] Copy backend code to Azure Functions directory
- [ ] Create deployment package (`zip -r function-app.zip .`)
- [ ] Deploy to Azure Functions using Azure CLI
- [ ] Verify function app is running (check `/health` endpoint)

### Step 3: Frontend Deployment
- [ ] Install frontend dependencies (`npm install`)
- [ ] Build React app (`npm run build`)
- [ ] Create deployment package (`zip -r build.zip build/`)
- [ ] Deploy to Azure Web App using Azure CLI
- [ ] Verify web app is running

## ✅ Post-Deployment Verification

### Infrastructure Verification
- [ ] All Azure resources created successfully
- [ ] PostgreSQL database accessible
- [ ] Redis cache operational
- [ ] Storage account created with container
- [ ] Application Insights collecting data
- [ ] Key Vault contains all secrets

### Application Verification
- [ ] Frontend loads without errors
- [ ] Backend API responds to health check
- [ ] Database connections working
- [ ] Redis cache functioning
- [ ] File upload functionality working
- [ ] Email notifications working (test with SendGrid)

### Security Verification
- [ ] HTTPS enabled for all endpoints
- [ ] CORS configured correctly
- [ ] Managed identities assigned properly
- [ ] Key Vault access policies configured
- [ ] Secrets stored securely (not in code)

### Performance Verification
- [ ] Application Insights showing telemetry
- [ ] Performance metrics within acceptable ranges
- [ ] No critical errors in logs
- [ ] Auto-scaling configured if needed

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Function App Issues
**Problem**: Function app not starting
**Solutions**:
- Check Application Insights logs
- Verify Python version compatibility
- Ensure all dependencies in requirements.txt
- Check function app settings

#### Database Connection Issues
**Problem**: Cannot connect to PostgreSQL
**Solutions**:
- Verify connection string in Key Vault
- Check PostgreSQL firewall rules
- Ensure managed identity has database permissions
- Test connection from Azure Cloud Shell

#### CORS Issues
**Problem**: Frontend cannot call backend API
**Solutions**:
- Verify CORS settings in Function App
- Check frontend API URL configuration
- Ensure HTTPS is used for all calls
- Review browser console for detailed errors

#### Storage Issues
**Problem**: File upload not working
**Solutions**:
- Check storage account permissions
- Verify container exists and is accessible
- Review storage connection string
- Test with Azure Storage Explorer

### Debug Commands

```bash
# Check resource status
az resource list --resource-group <resource-group> --output table

# View Function App logs
az functionapp log tail --name <function-app-name> --resource-group <resource-group>

# View Web App logs
az webapp log tail --name <web-app-name> --resource-group <resource-group>

# Test database connection
az postgres flexible-server connect --name <server-name> --admin-user <username>

# Check Key Vault secrets
az keyvault secret list --vault-name <key-vault-name>

# Monitor Application Insights
az monitor app-insights query --app <app-insights-name> --analytics-query "requests | limit 10"
```

## 🏗️ CI/CD Setup (Optional)

### GitHub Actions
- [ ] Create GitHub repository
- [ ] Add required secrets to GitHub repository
- [ ] Push code to repository
- [ ] Verify workflow runs successfully
- [ ] Set up branch protection rules

### Azure DevOps
- [ ] Create Azure DevOps project
- [ ] Set up service connection to Azure
- [ ] Create pipeline using azure-pipelines.yml
- [ ] Configure pipeline variables
- [ ] Run pipeline and verify deployment

## 📊 Monitoring Setup

### Application Insights
- [ ] Configure alerts for critical metrics
- [ ] Set up availability tests
- [ ] Create custom dashboards
- [ ] Configure log analytics queries

### Azure Monitor
- [ ] Set up cost alerts
- [ ] Configure performance alerts
- [ ] Create action groups for notifications
- [ ] Set up log retention policies

## 🔄 Maintenance

### Regular Tasks
- [ ] Review and rotate secrets quarterly
- [ ] Update dependencies regularly
- [ ] Monitor costs and optimize resources
- [ ] Review security recommendations
- [ ] Update documentation

### Backup Strategy
- [ ] Configure PostgreSQL automated backups
- [ ] Set up storage account replication
- [ ] Document recovery procedures
- [ ] Test disaster recovery plan

## 📞 Support Contacts

### Internal Team
- DevOps Engineer: [email]
- Database Administrator: [email]
- Security Team: [email]
- Application Owner: [email]

### External Support
- Azure Support: [support plan details]
- SendGrid Support: [account details]
- Domain/SSL Provider: [contact details]

---

## 🎯 Success Criteria

Deployment is considered successful when:
- [ ] All infrastructure deployed without errors
- [ ] Frontend application loads and functions correctly
- [ ] Backend API responds to all endpoints
- [ ] Database operations work correctly
- [ ] File upload and processing functions
- [ ] Email notifications are sent successfully
- [ ] Monitoring and logging are operational
- [ ] Security configurations are verified
- [ ] Performance meets requirements
- [ ] Documentation is updated

**Deployment Date**: ___________
**Deployed By**: ___________
**Environment**: ___________
**Version**: ___________
