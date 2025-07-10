@echo off
REM Quick Start Script for Order Management System Azure Deployment
REM This script helps you get started with the deployment process

echo.
echo ===================================
echo   Order Management System
echo   Azure Deployment Quick Start
echo ===================================
echo.

REM Check if running from correct directory
if not exist "terraform" (
    echo ❌ Error: Please run this script from the project root directory
    echo    Make sure you can see the 'terraform' folder
    pause
    exit /b 1
)

REM Check prerequisites
echo 🔍 Checking prerequisites...
echo.

REM Check Azure CLI
where az >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Azure CLI not found
    echo    Please install Azure CLI from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
    echo    Then run this script again
    pause
    exit /b 1
) else (
    echo ✅ Azure CLI found
)

REM Check Terraform
where terraform >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Terraform not found
    echo    Please install Terraform from: https://www.terraform.io/downloads.html
    echo    Then run this script again
    pause
    exit /b 1
) else (
    echo ✅ Terraform found
)

REM Check Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Node.js not found
    echo    Please install Node.js 18+ from: https://nodejs.org/
    echo    Then run this script again
    pause
    exit /b 1
) else (
    echo ✅ Node.js found
)

REM Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python not found
    echo    Please install Python 3.11+ from: https://www.python.org/downloads/
    echo    Then run this script again
    pause
    exit /b 1
) else (
    echo ✅ Python found
)

echo.
echo ✅ All prerequisites found!
echo.

REM Azure login check
echo 🔐 Checking Azure authentication...
az account show >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Not logged in to Azure
    echo    Please log in to Azure...
    az login
    if %errorlevel% neq 0 (
        echo ❌ Azure login failed
        pause
        exit /b 1
    )
) else (
    echo ✅ Already logged in to Azure
)

echo.
echo 📋 Current Azure Subscription:
az account show --output table
echo.

set /p "continue=Do you want to continue with this subscription? (y/n): "
if /i "%continue%" neq "y" (
    echo You can change subscription with: az account set --subscription [subscription-id]
    pause
    exit /b 0
)

echo.
echo 🛠️  Setting up configuration...

REM Check if terraform.tfvars exists
if not exist "terraform\terraform.tfvars" (
    echo 📄 Creating terraform.tfvars from example...
    copy "terraform\terraform.tfvars.example" "terraform\terraform.tfvars"
    echo.
    echo ⚠️  IMPORTANT: You need to edit terraform\terraform.tfvars with your values
    echo    Especially:
    echo    - postgres_admin_password
    echo    - sendgrid_api_key
    echo    - jwt_secret
    echo.
    set /p "edit_now=Do you want to edit terraform.tfvars now? (y/n): "
    if /i "%edit_now%" equ "y" (
        notepad "terraform\terraform.tfvars"
    )
    echo.
    echo Please make sure terraform.tfvars is configured correctly before proceeding
    pause
)

echo.
echo 🚀 Ready to deploy!
echo.
echo Choose deployment option:
echo 1. Run automated deployment script (recommended)
echo 2. Get manual deployment instructions
echo 3. Exit
echo.
set /p "choice=Enter your choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo 🚀 Running automated deployment...
    call deploy.bat
) else if "%choice%"=="2" (
    echo.
    echo 📖 Manual Deployment Instructions:
    echo.
    echo 1. Deploy Infrastructure:
    echo    cd terraform
    echo    terraform init
    echo    terraform plan
    echo    terraform apply
    echo.
    echo 2. Deploy Backend:
    echo    See README-AZURE.md for detailed instructions
    echo.
    echo 3. Deploy Frontend:
    echo    See README-AZURE.md for detailed instructions
    echo.
    echo 📖 For complete instructions, see:
    echo    - README-AZURE.md
    echo    - DEPLOYMENT-CHECKLIST.md
    echo.
) else if "%choice%"=="3" (
    echo.
    echo 👋 Goodbye!
    exit /b 0
) else (
    echo.
    echo ❌ Invalid choice
    pause
    exit /b 1
)

echo.
echo 🎉 Quick start completed!
echo.
echo 📚 Next steps:
echo    1. Check the deployment results
echo    2. Review DEPLOYMENT-CHECKLIST.md for post-deployment tasks
echo    3. Monitor your application in Azure Portal
echo.
pause
