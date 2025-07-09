# PowerShell script to add processing_remarks column to order_sku_items table
# Usage: .\migrate_add_processing_remarks.ps1

param(
    [string]$DbHost = $env:DB_HOST ?? "localhost",
    [string]$DbPort = $env:DB_PORT ?? "5432", 
    [string]$DbName = $env:DB_NAME ?? "order_planner",
    [string]$DbUser = $env:DB_USER ?? "postgres",
    [string]$DbPassword = $env:DB_PASSWORD ?? ""
)

Write-Host "=== Order Planner Database Migration ===" -ForegroundColor Cyan
Write-Host "Adding processing_remarks column to order_sku_items table" -ForegroundColor Yellow
Write-Host ""

# Display configuration
Write-Host "Database Configuration:" -ForegroundColor Green
Write-Host "  Host: $DbHost"
Write-Host "  Port: $DbPort"
Write-Host "  Database: $DbName"
Write-Host "  User: $DbUser"
Write-Host "  Password: $(if($DbPassword) { '*' * $DbPassword.Length } else { 'Not set' })"
Write-Host ""

# Check if psql is available
try {
    $null = Get-Command psql -ErrorAction Stop
    Write-Host "✓ PostgreSQL psql command found" -ForegroundColor Green
} catch {
    Write-Host "✗ PostgreSQL psql command not found. Please install PostgreSQL client tools." -ForegroundColor Red
    Write-Host "Download from: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    exit 1
}

# Prepare connection string
$env:PGPASSWORD = $DbPassword
$connectionArgs = @(
    "-h", $DbHost,
    "-p", $DbPort,
    "-U", $DbUser,
    "-d", $DbName
)

Write-Host "Testing database connection..." -ForegroundColor Yellow

# Test connection
try {
    $testResult = & psql @connectionArgs -c "SELECT version();" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Connection failed: $testResult"
    }
    Write-Host "✓ Database connection successful" -ForegroundColor Green
} catch {
    Write-Host "✗ Database connection failed: $_" -ForegroundColor Red
    Write-Host "Please check your database configuration and ensure PostgreSQL is running." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Checking if processing_remarks column already exists..." -ForegroundColor Yellow

# Check if column exists
$checkColumnSQL = @"
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'order_sku_items' 
AND column_name = 'processing_remarks';
"@

try {
    $columnExists = & psql @connectionArgs -t -c $checkColumnSQL 2>&1
    if ($columnExists -and $columnExists.Trim() -eq "processing_remarks") {
        Write-Host "✓ Column 'processing_remarks' already exists in order_sku_items table" -ForegroundColor Green
        Write-Host "Migration not needed." -ForegroundColor Yellow
        exit 0
    }
} catch {
    Write-Host "✗ Error checking column existence: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Column does not exist. Adding processing_remarks column..." -ForegroundColor Yellow

# Add the column
$addColumnSQL = @"
ALTER TABLE order_sku_items 
ADD COLUMN processing_remarks TEXT;
"@

try {
    $result = & psql @connectionArgs -c $addColumnSQL 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to add column: $result"
    }
    Write-Host "✓ Successfully added processing_remarks column" -ForegroundColor Green
} catch {
    Write-Host "✗ Error adding column: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Verifying column was added..." -ForegroundColor Yellow

# Verify column was added
$verifySQL = @"
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'order_sku_items' 
AND column_name = 'processing_remarks';
"@

try {
    $verification = & psql @connectionArgs -c $verifySQL 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Verification failed: $verification"
    }
    Write-Host "✓ Column verification successful:" -ForegroundColor Green
    Write-Host $verification
} catch {
    Write-Host "✗ Error verifying column: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Migration Completed Successfully! ===" -ForegroundColor Green
Write-Host "The processing_remarks column has been added to the order_sku_items table." -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Restart your backend services"
Write-Host "2. Test the new SKU Items tab in the frontend"
Write-Host "3. Process a new order to see processing remarks in action"
Write-Host ""

# Clean up password from environment
$env:PGPASSWORD = $null
