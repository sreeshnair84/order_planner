"""
Base Service for Order Processing System
Provides common functionality to eliminate code duplication.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update as sql_update
from app.models.order import Order
from app.models.tracking import OrderTracking
from app.models.sku_item import OrderSKUItem

logger = logging.getLogger(__name__)


class BaseOrderService:
    """Base service with common functionality for all order-related services"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============== COMMON DATABASE OPERATIONS ==============
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID with error handling"""
        try:
            result = await self.db.execute(
                select(Order).where(Order.id == uuid.UUID(order_id))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching order {order_id}: {str(e)}")
            return None
    
    async def get_order_tracking(self, order_id: str) -> List[OrderTracking]:
        """Get order tracking entries"""
        try:
            result = await self.db.execute(
                select(OrderTracking)
                .where(OrderTracking.order_id == uuid.UUID(order_id))
                .order_by(OrderTracking.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching tracking for order {order_id}: {str(e)}")
            return []
    
    # ============== LOGGING AND TRACKING ==============
    
    async def log_tracking(self, order_id: str, status: str, message: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """Unified tracking logging method"""
        try:
            tracking_entry = OrderTracking(
                id=uuid.uuid4(),
                order_id=uuid.UUID(order_id),
                status=status,
                message=message,
                details=details,
                created_at=datetime.utcnow()
            )
            
            self.db.add(tracking_entry)
            await self.db.commit()
            
            # Also log to application logger
            logger.info(f"Order {order_id} - {status}: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging tracking for order {order_id}: {str(e)}")
            return False
    
    async def update_order_status(self, order: Order, status: str, message: str, notes: Optional[str] = None) -> bool:
        """Unified order status update method"""
        try:
            order.status = status
            order.processing_notes = notes or message
            order.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Log the status change
            await self.log_tracking(
                str(order.id), 
                f"STATUS_UPDATE_{status}", 
                message,
                {"previous_status": order.status, "new_status": status}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}")
            return False
    
    # ============== ERROR HANDLING ==============
    
    def create_error_result(self, error_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create standardized error response"""
        result = {
            "success": False,
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        if context:
            result["context"] = context
        return result
    
    def create_success_result(self, data: Dict[str, Any], message: str = "Operation completed successfully") -> Dict[str, Any]:
        """Create standardized success response"""
        return {
            "success": True,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            **data
        }
    
    # ============== VALIDATION HELPERS ==============
    
    def validate_order_id(self, order_id: str) -> bool:
        """Validate order ID format"""
        try:
            uuid.UUID(order_id)
            return True
        except (ValueError, TypeError):
            return False
    
    def is_valid_quantity(self, quantity: Any) -> bool:
        """Check if quantity is valid"""
        try:
            qty = float(quantity)
            return qty > 0
        except (ValueError, TypeError):
            return False
    
    def is_valid_price(self, price: Any) -> bool:
        """Check if price is valid"""
        try:
            p = float(price)
            return p >= 0
        except (ValueError, TypeError):
            return False
    
    def is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) if email else False
    
    # ============== DATA PROCESSING HELPERS ==============
    
    def extract_missing_fields(self, data: Dict[str, Any], required_fields: Dict[str, List[str]]) -> List[str]:
        """Extract missing fields from data"""
        missing = []
        
        # Check order level fields
        for field in required_fields.get("order_level", []):
            if not data.get(field):
                missing.append(field)
        
        # Check retailer info fields
        retailer_info = data.get("retailer_info", {})
        for field in required_fields.get("retailer_level", []):
            if not retailer_info.get(field):
                missing.append(f"retailer_info.{field}")
        
        # Check item level fields
        items = data.get("order_items", [])
        for i, item in enumerate(items):
            for field in required_fields.get("item_level", []):
                if not item.get(field):
                    missing.append(f"item_{i}.{field}")
        
        return missing
    
    def calculate_data_quality_score(self, data: Dict[str, Any]) -> float:
        """Calculate data quality score (0.0 to 1.0)"""
        if not data:
            return 0.0
        
        total_checks = 0
        passed_checks = 0
        
        # Order level checks
        order_fields = ["order_number", "delivery_date", "retailer_info"]
        for field in order_fields:
            total_checks += 1
            if data.get(field):
                passed_checks += 1
        
        # Item level checks
        items = data.get("order_items", [])
        if items:
            for item in items:
                item_fields = ["sku_code", "quantity", "price"]
                for field in item_fields:
                    total_checks += 1
                    if item.get(field):
                        passed_checks += 1
        
        return passed_checks / total_checks if total_checks > 0 else 0.0
    
    # ============== BUSINESS LOGIC HELPERS ==============
    
    def categorize_tracking_status(self, status: str) -> str:
        """Categorize tracking status for UI display"""
        status_categories = {
            "FILE_": "file_processing",
            "VALIDATION_": "validation",  
            "EMAIL_": "communication",
            "SKU_": "sku_processing",
            "PROCESSING_": "processing",
            "ERROR": "error",
            "FAILED": "error"
        }
        
        for key, category in status_categories.items():
            if key in status:
                return category
        
        return "general"
    
    def get_processing_priority(self, order: Order) -> str:
        """Determine processing priority for an order"""
        if not order:
            return "LOW"
        
        # Check if order has errors
        if "ERROR" in (order.status or ""):
            return "HIGH"
        
        # Check delivery date urgency
        try:
            if order.delivery_date:
                days_until_delivery = (order.delivery_date - datetime.utcnow().date()).days
                if days_until_delivery <= 1:
                    return "URGENT"
                elif days_until_delivery <= 3:
                    return "HIGH"
        except:
            pass
        
        # Check order value
        if order.total and order.total > 10000:
            return "HIGH"
        elif order.total and order.total > 5000:
            return "MEDIUM"
        
        return "LOW"
    
    # ============== RETRY MECHANISMS ==============
    
    async def retry_with_backoff(self, func, max_retries: int = 3, backoff_factor: float = 2.0) -> Any:
        """Generic retry mechanism with exponential backoff"""
        import asyncio
        
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                
                wait_time = backoff_factor ** attempt
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}")
                await asyncio.sleep(wait_time)
        
        raise Exception(f"All {max_retries} attempts failed")
    
    # ============== FIELD METADATA ==============
    
    def get_field_metadata(self, field_name: str) -> Dict[str, Any]:
        """Get metadata for a field (type, description, validation rules)"""
        field_metadata = {
            "delivery_address": {
                "type": "text",
                "description": "Complete delivery address including street, city, state, zip",
                "validation": ["required", "min_length:10"],
                "category": "address"
            },
            "delivery_date": {
                "type": "date", 
                "description": "Requested delivery date (YYYY-MM-DD format)",
                "validation": ["required", "date", "future_date"],
                "category": "scheduling"
            },
            "retailer_contact": {
                "type": "email",
                "description": "Primary contact email for this order",
                "validation": ["required", "email"],
                "category": "contact"
            },
            "retailer_phone": {
                "type": "tel",
                "description": "Contact phone number",
                "validation": ["phone"],
                "category": "contact"
            },
            "priority": {
                "type": "select",
                "description": "Order priority level",
                "validation": ["required", "in:LOW,MEDIUM,HIGH,URGENT"],
                "options": ["LOW", "MEDIUM", "HIGH", "URGENT"],
                "category": "business"
            },
            "special_instructions": {
                "type": "textarea",
                "description": "Any special delivery or handling instructions",
                "validation": [],
                "category": "instructions"
            }
        }
        
        return field_metadata.get(field_name, {
            "type": "text",
            "description": f"Please provide {field_name.replace('_', ' ')}",
            "validation": ["required"],
            "category": "general"
        })
