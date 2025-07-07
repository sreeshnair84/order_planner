@echo off
REM Deployment script for Order Management System Azure Infrastructure (Windows)

echo 🚀 Starting Azure Infrastructure Deployment

REM Configuration
set TERRAFORM_DIR=terraform
set BACKEND_DIR=backend
set FRONTEND_DIR=frontend
set AZURE_FUNCTIONS_DIR=backend_azure_functions

REM Check if Azure CLI is installed
where az >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Azure CLI is not installed. Please install it first.
    exit /b 1
)

REM Check if Terraform is installed
where terraform >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Terraform is not installed. Please install it first.
    exit /b 1
)

REM Login to Azure if not already logged in
echo 🔐 Checking Azure authentication...
az account show >nul 2>nul
if %errorlevel% neq 0 (
    echo Please login to Azure...
    az login
)

REM Display current subscription
echo 📋 Current Azure Subscription:
az account show --output table

REM Ask for confirmation
set /p "continue=Do you want to proceed with this subscription? (y/n): "
if /i "%continue%" neq "y" (
    echo Deployment cancelled.
    exit /b 0
)

REM Change to terraform directory
cd %TERRAFORM_DIR%

REM Check if terraform.tfvars exists
if not exist "terraform.tfvars" (
    echo ⚠️  terraform.tfvars not found. Creating from example...
    copy terraform.tfvars.example terraform.tfvars
    echo ❌ Please edit terraform.tfvars with your specific values before running this script again.
    exit /b 1
)

REM Initialize Terraform
echo 🏗️  Initializing Terraform...
terraform init

REM Format Terraform files
echo 🎨 Formatting Terraform files...
terraform fmt

REM Validate Terraform configuration
echo ✅ Validating Terraform configuration...
terraform validate

REM Plan deployment
echo 📋 Planning deployment...
terraform plan -out=tfplan

REM Ask for confirmation before applying
set /p "apply=Do you want to apply this plan? (y/n): "
if /i "%apply%" neq "y" (
    echo Deployment cancelled.
    exit /b 0
)

REM Apply deployment
echo 🚀 Applying infrastructure deployment...
terraform apply tfplan

REM Display outputs
echo 📊 Deployment completed! Here are the important URLs:
terraform output

REM Prepare Azure Function deployment
echo 📦 Preparing Azure Function deployment...
cd ..\%AZURE_FUNCTIONS_DIR%

REM Copy backend code to Azure Functions directory
echo 📁 Copying backend code...
xcopy /E /Y "..\%BACKEND_DIR%\app" "app\"
copy "..\%BACKEND_DIR%\requirements.txt" "requirements.txt"

REM Create deployment package (using PowerShell)
echo 📦 Creating deployment package...
powershell -Command "Compress-Archive -Path * -DestinationPath function-app.zip -Force"

REM Get function app name from terraform output
cd ..\%TERRAFORM_DIR%
for /f "tokens=*" %%i in ('terraform output -raw function_app_name') do set FUNCTION_APP_NAME=%%i
for /f "tokens=*" %%i in ('terraform output -raw resource_group_name') do set RESOURCE_GROUP_NAME=%%i

REM Deploy to Azure Functions
echo 🚀 Deploying to Azure Functions...
cd ..\%AZURE_FUNCTIONS_DIR%
az functionapp deployment source config-zip --resource-group %RESOURCE_GROUP_NAME% --name %FUNCTION_APP_NAME% --src function-app.zip

REM Frontend deployment instructions
echo ✅ Infrastructure deployment complete!
echo 📋 Next steps for frontend deployment:
echo 1. Build the React app:
echo    cd %FRONTEND_DIR%
echo    npm install
echo    npm run build
echo.
echo 2. Deploy to Azure Web App:
echo    az webapp deployment source config-zip ^
echo      --resource-group %RESOURCE_GROUP_NAME% ^
echo      --name [web_app_name] ^
echo      --src build.zip
echo.
echo 🎉 Deployment script completed!

pause
