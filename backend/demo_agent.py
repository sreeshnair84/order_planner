#!/usr/bin/env python3
"""
Working Example: Order Processing Agent Demo

This script demonstrates how to use the Order Processing Agent
in both mock mode and with real database.
"""

import asyncio
import json
import uuid
from datetime import datetime

async def demo_agent_service():
    """Demonstrate the agent service in mock mode"""
    print("🤖 Order Processing Agent Service Demo")
    print("=" * 50)
    
    try:
        from app.services.ai_foundry_agent_service import OrderProcessingAgentService
        
        # Create service without database (mock mode)
        print("1. Creating Agent Service (Mock Mode)...")
        service = OrderProcessingAgentService(None)
        
        # Get agent status
        print("2. Getting Agent Status...")
        status = await service.get_agent_status()
        print(f"   Status: {json.dumps(status, indent=2)}")
        
        # Try to process an order (will fail gracefully in mock mode)
        print("3. Testing Order Processing (Mock Mode)...")
        test_order_id = str(uuid.uuid4())
        result = await service.process_order_completely(test_order_id, "TEST-001")
        print(f"   Result: {json.dumps(result, indent=2)}")
        
        # Test step processing
        print("4. Testing Step Processing (Mock Mode)...")
        step_result = await service.process_order_step(test_order_id, "validate")
        print(f"   Step Result: {json.dumps(step_result, indent=2)}")
        
        print("✅ Agent Service Demo Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        return False

async def demo_unified_processor():
    """Demonstrate the unified order processor"""
    print("\n🔧 Unified Order Processor Demo")
    print("=" * 50)
    
    try:
        from app.services.unified_order_processor import UnifiedOrderProcessor
        
        # Create processor without database
        print("1. Creating Unified Processor...")
        processor = UnifiedOrderProcessor(None)
        
        # Test various methods
        print("2. Testing Processor Methods...")
        
        # Test validation
        test_data = {
            "order_items": [
                {
                    "sku_code": "TEST001",
                    "quantity": 10,
                    "price": 15.99
                }
            ],
            "delivery_date": "2025-01-15",
            "retailer_info": {
                "name": "Test Retailer",
                "email": "test@retailer.com"
            }
        }
        
        test_order_id = str(uuid.uuid4())
        validation_result = await processor.validate_order_completeness(test_order_id, test_data)
        print(f"   Validation Result: {json.dumps(validation_result, indent=2)}")
        
        print("✅ Unified Processor Demo Completed!")
        return True
        
    except Exception as e:
        print(f"❌ Unified Processor Demo failed: {str(e)}")
        return False

async def demo_api_endpoints():
    """Demonstrate how to use the API endpoints"""
    print("\n🌐 API Endpoints Demo")
    print("=" * 50)
    
    print("To test the API endpoints, start the server first:")
    print("   python -m uvicorn app.main:app --reload")
    print()
    print("Then use these curl commands:")
    print()
    
    endpoints = [
        ("Agent Status", "GET", "/api/ai-agent/status", ""),
        ("Process Order", "POST", "/api/ai-agent/orders/{order_id}/process", ""),
        ("Process Step", "POST", "/api/ai-agent/orders/{order_id}/steps/validate", ""),
        ("Get Threads", "GET", "/api/ai-agent/orders/{order_id}/threads", ""),
    ]
    
    for name, method, endpoint, body in endpoints:
        print(f"{name}:")
        if body:
            print(f"   curl -X {method} http://localhost:8000{endpoint} \\")
            print(f"        -H 'Content-Type: application/json' \\")
            print(f"        -d '{body}'")
        else:
            print(f"   curl -X {method} http://localhost:8000{endpoint}")
        print()

async def demo_real_database_usage():
    """Show how to use with real database"""
    print("\n💾 Real Database Usage Example")
    print("=" * 50)
    
    print("To use with a real database:")
    print()
    print("1. Setup database:")
    print("   python scripts/setup_database.py")
    print()
    print("2. Create database session and use the agent:")
    print("""
   from app.database.connection import AsyncSessionLocal
   from app.services.ai_foundry_agent_service import OrderProcessingAgentService
   
   async def process_order():
       async with AsyncSessionLocal() as session:
           service = OrderProcessingAgentService(session)
           result = await service.process_order_completely(order_id, order_number)
           return result
""")
    print()
    print("3. Or use the API endpoints (preferred for frontend integration)")

async def main():
    """Run all demos"""
    print("🚀 Order Processing Agent Complete Demo")
    print("=" * 60)
    
    demos = [
        ("Agent Service", demo_agent_service),
        ("Unified Processor", demo_unified_processor),
        ("API Endpoints", demo_api_endpoints),
        ("Database Usage", demo_real_database_usage),
    ]
    
    results = []
    for name, demo_func in demos:
        try:
            result = await demo_func()
            results.append((name, result if result is not None else True))
        except Exception as e:
            print(f"❌ {name} demo failed: {str(e)}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DEMO SUMMARY")
    print("=" * 60)
    
    for name, success in results:
        if success is True:
            print(f"✅ {name}")
        elif success is False:
            print(f"❌ {name}")
        else:
            print(f"ℹ️ {name} (Info only)")
    
    working_demos = sum(1 for _, success in results if success is True)
    total_demos = len([r for r in results if r[1] is not None])
    
    if total_demos > 0:
        print(f"\nResult: {working_demos}/{total_demos} demos working")
    
    print("\n🎯 Quick Start Recommendations:")
    print("1. Use mock mode for development (no Azure AI needed)")
    print("2. Start server: python -m uvicorn app.main:app --reload")
    print("3. Test via API endpoints")
    print("4. For production: set up Azure AI configuration")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
