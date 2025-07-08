#!/usr/bin/env python3
"""
Order Processing Agent Setup Script

This script creates, configures, and manages the Order Processing Agent
for the FMCG Order Planning system.

Usage:
  python setup_agent.py create    # Create and configure the agent
  python setup_agent.py test      # Test the agent with sample data
  python setup_agent.py status    # Check agent status
  python setup_agent.py clean     # Clean up agent resources
"""

import asyncio
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.database.config import get_async_db
from app.services.unified_order_processor import UnifiedOrderProcessor
from agents.order_processing_agent import OrderProcessingAgent, create_order_processing_agent
from app.models.order import Order
from app.utils.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentSetup:
    """Order Processing Agent setup and management"""
    
    def __init__(self):
        self.db_session = None
        self.agent = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.db_session = await get_async_db().__anext__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.agent:
            await self.agent.cleanup()
        if self.db_session:
            await self.db_session.close()
    
    async def create_agent(self) -> Dict[str, Any]:
        """Create and configure the Order Processing Agent"""
        try:
            logger.info("Creating Order Processing Agent...")
            
            # Check Azure AI configuration
            if not settings.AZURE_AI_PROJECT_CONNECTION_STRING:
                return {
                    "success": False,
                    "error": "Azure AI Project connection string not configured"
                }
            
            # Create the agent
            self.agent = await create_order_processing_agent(self.db_session)
            
            # Check agent status
            status = await self.agent.get_agent_status()
            
            if status["initialized"]:
                logger.info(f"Agent created successfully with ID: {status.get('agent_id', 'unknown')}")
                
                # Configure agent tools
                tool_descriptions = await self._get_tool_descriptions()
                
                return {
                    "success": True,
                    "agent_id": status.get("agent_id"),
                    "agent_name": status.get("agent_name"),
                    "status": status,
                    "tools": tool_descriptions,
                    "message": "Order Processing Agent created and configured successfully"
                }
            else:
                return {
                    "success": False,
                    "error": status.get("error", "Agent initialization failed"),
                    "status": status
                }
        
        except Exception as e:
            logger.error(f"Failed to create agent: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_agent(self, order_id: Optional[str] = None) -> Dict[str, Any]:
        """Test the agent with sample data or existing order"""
        try:
            logger.info("Testing Order Processing Agent...")
            
            if not self.agent:
                self.agent = await create_order_processing_agent(self.db_session)
            
            if not self.agent.is_initialized:
                return {
                    "success": False,
                    "error": "Agent not initialized"
                }
            
            # Use provided order ID or find a test order
            test_order_id = order_id or await self._find_test_order()
            
            if not test_order_id:
                return {
                    "success": False,
                    "error": "No test order available. Please upload an order first."
                }
            
            logger.info(f"Testing with order: {test_order_id}")
            
            # Test the complete processing workflow
            result = await self.agent.process_order_complete(test_order_id)
            
            return {
                "success": True,
                "test_order_id": test_order_id,
                "test_result": result,
                "message": "Agent test completed successfully"
            }
        
        except Exception as e:
            logger.error(f"Agent test failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_status(self) -> Dict[str, Any]:
        """Check agent and system status"""
        try:
            logger.info("Checking agent status...")
            
            # Check Azure AI configuration
            azure_config = {
                "connection_string_configured": bool(settings.AZURE_AI_PROJECT_CONNECTION_STRING),
                "endpoint_configured": bool(getattr(settings, 'AZURE_AI_ENDPOINT', None)),
                "key_configured": bool(getattr(settings, 'AZURE_AI_KEY', None))
            }
            
            # Check database connection
            try:
                from sqlalchemy import text
                result = await self.db_session.execute(text("SELECT 1"))
                db_status = {"connected": True, "test_query": "passed"}
            except Exception as e:
                db_status = {"connected": False, "error": str(e)}
            
            # Check agent if available
            agent_status = None
            if self.agent:
                agent_status = await self.agent.get_agent_status()
            else:
                try:
                    self.agent = await create_order_processing_agent(self.db_session)
                    agent_status = await self.agent.get_agent_status()
                except Exception as e:
                    agent_status = {"error": str(e)}
            
            # Check sample orders availability
            orders_count = await self._count_orders()
            
            return {
                "success": True,
                "azure_config": azure_config,
                "database": db_status,
                "agent": agent_status,
                "orders_available": orders_count,
                "system_ready": (
                    azure_config["connection_string_configured"] and
                    db_status["connected"] and
                    (agent_status and agent_status.get("initialized", False))
                )
            }
        
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def clean_resources(self) -> Dict[str, Any]:
        """Clean up agent resources"""
        try:
            logger.info("Cleaning up agent resources...")
            
            if self.agent:
                await self.agent.cleanup()
                self.agent = None
            
            return {
                "success": True,
                "message": "Agent resources cleaned up successfully"
            }
        
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of available agent tools"""
        return {
            "process_order_complete": "Complete order processing workflow from file parsing to logistics calculation",
            "parse_order_file": "Parse uploaded order files and extract structured data",
            "validate_order_data": "Validate order data for completeness and business rules",
            "process_email_workflow": "Generate and send emails for missing information (unified step)",
            "process_sku_items": "Process and validate SKU items with totals calculation",
            "calculate_logistics": "Calculate shipping costs and delivery requirements",
            "get_order_summary": "Get comprehensive order summary and status",
            "retry_processing_step": "Retry failed processing steps with backoff",
            "apply_corrections": "Apply user corrections to order data"
        }
    
    async def _find_test_order(self) -> Optional[str]:
        """Find a suitable test order"""
        try:
            from sqlalchemy import select
            
            # Find an order that's uploaded but not fully processed
            result = await self.db_session.execute(
                select(Order.id).where(Order.status.in_(["UPLOADED", "PARSED", "MISSING_INFO"]))
                .limit(1)
            )
            order = result.scalar_one_or_none()
            
            if order:
                return str(order)
            
            # If no suitable order, find any order
            result = await self.db_session.execute(
                select(Order.id).limit(1)
            )
            order = result.scalar_one_or_none()
            
            return str(order) if order else None
        
        except Exception as e:
            logger.error(f"Error finding test order: {str(e)}")
            return None
    
    async def _count_orders(self) -> int:
        """Count available orders"""
        try:
            from sqlalchemy import select, func
            
            result = await self.db_session.execute(
                select(func.count(Order.id))
            )
            return result.scalar() or 0
        
        except Exception as e:
            logger.error(f"Error counting orders: {str(e)}")
            return 0


async def main():
    """Main entry point for the setup script"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    async with AgentSetup() as setup:
        if command == "create":
            result = await setup.create_agent()
        elif command == "test":
            order_id = sys.argv[2] if len(sys.argv) > 2 else None
            result = await setup.test_agent(order_id)
        elif command == "status":
            result = await setup.check_status()
        elif command == "clean":
            result = await setup.clean_resources()
        else:
            result = {
                "success": False,
                "error": f"Unknown command: {command}",
                "available_commands": ["create", "test", "status", "clean"]
            }
        
        # Pretty print the result
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
