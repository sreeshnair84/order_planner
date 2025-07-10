# PowerShell script to fix HTTPS redirect issue in Azure Container App

Write-Host "Fixing HTTPS redirect issue for Azure Container App..." -ForegroundColor Green

# Option 1: Update Container App to disable HTTP traffic (Recommended)
Write-Host "Updating Container App to disable insecure HTTP traffic..." -ForegroundColor Yellow
try {
    az containerapp ingress update `
        --resource-group "ODL-Infosys-Hack-1775541-02" `
        --name dispatchplannerapp `
        --allow-insecure false
    
    Write-Host "✅ Successfully disabled HTTP traffic. Only HTTPS will be allowed." -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to update Container App ingress. Please update manually via Azure Portal." -ForegroundColor Red
    Write-Host "Manual steps:" -ForegroundColor Yellow
    Write-Host "1. Go to Azure Portal -> Container Apps" -ForegroundColor Yellow
    Write-Host "2. Find 'dispatchplannerapp'" -ForegroundColor Yellow
    Write-Host "3. Go to Ingress settings" -ForegroundColor Yellow
    Write-Host "4. Uncheck 'Allow insecure traffic'" -ForegroundColor Yellow
}

# Option 2: Set environment variable for production
Write-Host "Setting ENVIRONMENT variable to production..." -ForegroundColor Yellow
try {
    az containerapp update `
        --name dispatchplannerapp `
        --resource-group "ODL-Infosys-Hack-1775541-02" `
        --set-env-vars ENVIRONMENT=production
    
    Write-Host "✅ Successfully set ENVIRONMENT=production" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to set environment variable" -ForegroundColor Red
}

Write-Host "Fix complete! Your Container App should now:" -ForegroundColor Green
Write-Host "• Only accept HTTPS traffic" -ForegroundColor Green
Write-Host "• Redirect any HTTP requests to HTTPS" -ForegroundColor Green
Write-Host "• Handle pagination redirects correctly" -ForegroundColor Green

Write-Host "`nPlease restart your Container App for changes to take effect:" -ForegroundColor Yellow
Write-Host "az containerapp restart --name dispatchplannerapp --resource-group 'ODL-Infosys-Hack-1775541-02'" -ForegroundColor Cyan
