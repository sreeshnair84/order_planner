@echo off
REM Order Management System Setup Script for Windows

echo 🚀 Setting up Order Management System...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Create environment file if it doesn't exist
if not exist "backend\.env" (
    echo 📝 Creating environment file...
    copy "backend\.env.example" "backend\.env"
    echo ✅ Environment file created. Please edit backend\.env with your configuration.
)

REM Create uploads directory
echo 📁 Creating uploads directory...
if not exist "backend\uploads" mkdir "backend\uploads"

REM Build and start the application
echo 🔨 Building and starting the application...
docker-compose up --build -d

echo ⏳ Waiting for services to start...
timeout /t 30 /nobreak >nul

REM Check if services are running
docker-compose ps | findstr "Up" >nul
if %errorlevel% equ 0 (
    echo ✅ Application started successfully!
    echo.
    echo 🌐 Access the application:
    echo    Frontend: http://localhost:3000
    echo    Backend API: http://localhost:8000
    echo    API Documentation: http://localhost:8000/docs
    echo.
    echo 📖 Check the README.md for more information.
) else (
    echo ❌ Failed to start the application. Check the logs:
    echo    docker-compose logs
)

pause
