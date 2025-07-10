#!/bin/bash

# Order Management System Setup Script

echo "🚀 Setting up Order Management System..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker and Docker Compose first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create environment file if it doesn't exist
if [ ! -f "backend/.env" ]; then
    echo "📝 Creating environment file..."
    cp backend/.env.example backend/.env
    echo "✅ Environment file created. Please edit backend/.env with your configuration."
fi

# Create uploads directory
echo "📁 Creating uploads directory..."
mkdir -p backend/uploads

# Build and start the application
echo "🔨 Building and starting the application..."
docker-compose up --build -d

echo "⏳ Waiting for services to start..."
sleep 30

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Application started successfully!"
    echo ""
    echo "🌐 Access the application:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo "   API Documentation: http://localhost:8000/docs"
    echo ""
    echo "📖 Check the README.md for more information."
else
    echo "❌ Failed to start the application. Check the logs:"
    echo "   docker-compose logs"
fi
