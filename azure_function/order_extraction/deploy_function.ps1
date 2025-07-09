# Deploy Azure Function with retailer extraction features
# This script deploys the updated Azure Function with retailer extraction capabilities

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$true)]
    [string]$FunctionAppName,
    
    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId
)

Write-Host "=== Azure Function Deployment Script ===" -ForegroundColor Green
Write-Host "Function App: $FunctionAppName" -ForegroundColor Yellow
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor Yellow

# Set subscription if provided
if ($SubscriptionId) {
    Write-Host "Setting subscription: $SubscriptionId" -ForegroundColor Yellow
    az account set --subscription $SubscriptionId
}

# Get current directory
$currentDir = Get-Location
$functionDir = Join-Path $currentDir "azure_function\order_extraction"

Write-Host "Function directory: $functionDir" -ForegroundColor Yellow

# Check if function directory exists
if (-not (Test-Path $functionDir)) {
    Write-Error "Function directory not found: $functionDir"
    exit 1
}

# Change to function directory
Set-Location $functionDir

Write-Host "Installing dependencies..." -ForegroundColor Cyan
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
} else {
    Write-Warning "requirements.txt not found"
}

Write-Host "Deploying Azure Function..." -ForegroundColor Cyan

# Deploy the function app
$deployResult = func azure functionapp publish $FunctionAppName --python

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Function deployment successful!" -ForegroundColor Green
    
    # Get function app URL
    $functionUrl = az functionapp show --name $FunctionAppName --resource-group $ResourceGroupName --query "defaultHostName" --output tsv
    
    if ($functionUrl) {
        Write-Host ""
        Write-Host "=== Deployment Complete ===" -ForegroundColor Green
        Write-Host "Function App URL: https://$functionUrl" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Available endpoints:" -ForegroundColor Cyan
        Write-Host "  • Health Check: https://$functionUrl/api/health" -ForegroundColor White
        Write-Host "  • File Reader: https://$functionUrl/api/order_file_reader" -ForegroundColor White
        Write-Host "  • Retailer Extraction: https://$functionUrl/api/extract_retailer_info" -ForegroundColor White
        Write-Host "  • Update Retailer Mapping: https://$functionUrl/api/update_retailer_mapping" -ForegroundColor White
        Write-Host "  • Validate Completeness: https://$functionUrl/api/validate_order_completeness" -ForegroundColor White
        Write-Host ""
        Write-Host "Testing deployment..." -ForegroundColor Cyan
        
        # Test health endpoint
        try {
            $healthResponse = Invoke-RestMethod -Uri "https://$functionUrl/api/health" -Method Get -TimeoutSec 30
            if ($healthResponse.status -eq "healthy") {
                Write-Host "✅ Health check passed" -ForegroundColor Green
                Write-Host "Azure OpenAI Configured: $($healthResponse.azure_openai_configured)" -ForegroundColor Yellow
            } else {
                Write-Warning "Health check returned unexpected status: $($healthResponse.status)"
            }
        } catch {
            Write-Warning "Health check failed: $($_.Exception.Message)"
        }
        
        Write-Host ""
        Write-Host "=== Next Steps ===" -ForegroundColor Green
        Write-Host "1. Configure Azure OpenAI environment variables if not already set:" -ForegroundColor White
        Write-Host "   • AZURE_OPENAI_ENDPOINT" -ForegroundColor Gray
        Write-Host "   • AZURE_OPENAI_KEY" -ForegroundColor Gray
        Write-Host "   • AZURE_OPENAI_DEPLOYMENT" -ForegroundColor Gray
        Write-Host ""
        Write-Host "2. Test retailer extraction with an existing order:" -ForegroundColor White
        Write-Host "   python integration_test.py https://$functionUrl <order_id>" -ForegroundColor Gray
        Write-Host ""
        Write-Host "3. Verify database has pg_trgm extension enabled for fuzzy matching:" -ForegroundColor White
        Write-Host "   CREATE EXTENSION IF NOT EXISTS pg_trgm;" -ForegroundColor Gray
        
    } else {
        Write-Warning "Could not retrieve function app URL"
    }
} else {
    Write-Error "❌ Function deployment failed!"
    exit 1
}

# Return to original directory
Set-Location $currentDir

Write-Host ""
Write-Host "Deployment script completed." -ForegroundColor Green
