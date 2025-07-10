#!/usr/bin/env python3
"""
Validation script to check the Order Management System implementation
"""
import os
import sys
import json
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and return status"""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description}: {filepath} - NOT FOUND")
        return False

def check_backend_structure():
    """Check backend structure"""
    print("\n=== Backend Structure Check ===")
    
    backend_files = [
        ("backend/app/main.py", "Main FastAPI application"),
        ("backend/app/models/order.py", "Enhanced Order model"),
        ("backend/app/models/sku_item.py", "SKU Item model"),
        ("backend/app/models/schemas.py", "Pydantic schemas"),
        ("backend/app/services/sku_service.py", "SKU service"),
        ("backend/app/services/order_processing_service.py", "Order processing service"),
        ("backend/app/services/email_service.py", "Enhanced email service"),
        ("backend/app/api/requestedorders.py", "Enhanced orders API"),
        ("backend/app/api/tracking.py", "Enhanced tracking API"),
        ("backend/app/database/connection.py", "Database connection"),
        ("backend/scripts/migrate_database.py", "Database migration script"),
        ("backend/requirements.txt", "Python dependencies"),
        ("backend/Dockerfile", "Docker configuration"),
    ]
    
    backend_score = 0
    for filepath, description in backend_files:
        if check_file_exists(filepath, description):
            backend_score += 1
    
    print(f"\nBackend Score: {backend_score}/{len(backend_files)}")
    return backend_score == len(backend_files)

def check_frontend_structure():
    """Check frontend structure"""
    print("\n=== Frontend Structure Check ===")
    
    frontend_files = [
        ("frontend/package.json", "Frontend dependencies"),
        ("frontend/src/App.js", "Main React app"),
        ("frontend/src/pages/TrackingPage.js", "Enhanced tracking page"),
        ("frontend/src/services/apiClient.js", "API client"),
        ("frontend/Dockerfile", "Frontend Docker configuration"),
        ("frontend/nginx.conf", "Nginx configuration"),
    ]
    
    frontend_score = 0
    for filepath, description in frontend_files:
        if check_file_exists(filepath, description):
            frontend_score += 1
    
    print(f"\nFrontend Score: {frontend_score}/{len(frontend_files)}")
    return frontend_score == len(frontend_files)

def check_email_templates():
    """Check email templates"""
    print("\n=== Email Templates Check ===")
    
    template_files = [
        ("backend/app/templates/emails/sku_validation.html", "SKU validation template"),
        ("backend/app/templates/emails/trip_notification.html", "Trip notification template"),
        ("backend/app/templates/emails/delivery_notification.html", "Delivery notification template"),
    ]
    
    template_score = 0
    for filepath, description in template_files:
        if check_file_exists(filepath, description):
            template_score += 1
    
    print(f"\nEmail Templates Score: {template_score}/{len(template_files)}")
    return template_score == len(template_files)

def check_infrastructure():
    """Check infrastructure files"""
    print("\n=== Infrastructure Check ===")
    
    infra_files = [
        ("docker-compose.yml", "Docker Compose configuration"),
        ("README.md", "Project documentation"),
        ("IMPLEMENTATION_SUMMARY.md", "Implementation summary"),
    ]
    
    infra_score = 0
    for filepath, description in infra_files:
        if check_file_exists(filepath, description):
            infra_score += 1
    
    print(f"\nInfrastructure Score: {infra_score}/{len(infra_files)}")
    return infra_score == len(infra_files)

def validate_requirements():
    """Validate requirements.txt has all needed dependencies"""
    print("\n=== Requirements Validation ===")
    
    try:
        with open("backend/requirements.txt", "r") as f:
            requirements = f.read().lower()
        
        required_packages = [
            "fastapi", "uvicorn", "sqlalchemy", "asyncpg", "psycopg2-binary",
            "pydantic", "jinja2", "aiofiles", "aiosmtplib", "pandas",
            "python-jose", "passlib", "python-multipart", "pytest"
        ]
        
        missing_packages = []
        for package in required_packages:
            if package not in requirements:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"✗ Missing packages: {', '.join(missing_packages)}")
            return False
        else:
            print("✓ All required packages present")
            return True
    except Exception as e:
        print(f"✗ Error reading requirements.txt: {e}")
        return False

def check_code_quality():
    """Check for basic code quality indicators"""
    print("\n=== Code Quality Check ===")
    
    # Check for docstrings in key files
    key_files = [
        "backend/app/services/sku_service.py",
        "backend/app/services/order_processing_service.py",
        "backend/app/models/schemas.py"
    ]
    
    quality_score = 0
    for filepath in key_files:
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                content = f.read()
                if '"""' in content or "'''" in content:
                    print(f"✓ {filepath} has docstrings")
                    quality_score += 1
                else:
                    print(f"✗ {filepath} lacks docstrings")
    
    print(f"\nCode Quality Score: {quality_score}/{len(key_files)}")
    return quality_score >= len(key_files) * 0.8

def main():
    """Main validation function"""
    print("Order Management System - Implementation Validation")
    print("=" * 50)
    
    # Change to project directory
    os.chdir("c:/project/order_planner")
    
    # Run all checks
    checks = [
        check_backend_structure(),
        check_frontend_structure(),
        check_email_templates(),
        check_infrastructure(),
        validate_requirements(),
        check_code_quality()
    ]
    
    # Summary
    passed = sum(checks)
    total = len(checks)
    
    print(f"\n{'=' * 50}")
    print(f"VALIDATION SUMMARY")
    print(f"{'=' * 50}")
    print(f"Passed: {passed}/{total} checks")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("✓ ALL CHECKS PASSED - System is ready for testing!")
    elif passed >= total * 0.8:
        print("⚠ MOSTLY COMPLETE - Minor issues to address")
    else:
        print("✗ MAJOR ISSUES - Significant work needed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
